# tools/tool_registry.py
import sqlite3
import inspect
import json
from pathlib import Path
from pydantic import create_model
from langchain.tools import tool
from langchain_core.tools import StructuredTool
from tools.weather_tool import get_weather
from tools.rag_tool import search_docs
from core.logger import get_logger
from tools.sandbox import execute_in_sandbox
logger = get_logger("tool_registry")

DB_PATH = Path(__file__).resolve().parent.parent / "tools_registry.db"

BUILTIN_TOOLS = {
    "get_weather": get_weather,
    "search_docs": search_docs,
}


# ========== 数据库初始化 ==========
def init_tool_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            name        TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            code        TEXT NOT NULL,
            enabled     INTEGER DEFAULT 1,
            builtin     INTEGER DEFAULT 0
        )
    """)
    for name, fn in BUILTIN_TOOLS.items():
        cursor.execute("""
            INSERT OR IGNORE INTO tools (name, description, code, enabled, builtin)
            VALUES (?, ?, ?, 1, 1)
        """, (name, fn.description, "# builtin tool"))
    conn.commit()
    conn.close()
    logger.info("工具数据库初始化完成")


# ========== CRUD ==========
def list_tools():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, enabled, builtin FROM tools")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"name": r[0], "description": r[1], "enabled": bool(r[2]), "builtin": bool(r[3])}
        for r in rows
    ]


def add_tool(name: str, description: str, code: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO tools (name, description, code, enabled, builtin)
        VALUES (?, ?, ?, 1, 0)
    """, (name, description, code))
    conn.commit()
    conn.close()
    logger.info(f"工具已添加：{name}")


def update_tool(name: str, description: str = None, code: str = None, enabled: bool = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT builtin FROM tools WHERE name=?", (name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Tool '{name}' not found")
    if description:
        cursor.execute("UPDATE tools SET description=? WHERE name=?", (description, name))
    if code and not row[0]:
        cursor.execute("UPDATE tools SET code=? WHERE name=?", (code, name))
    if enabled is not None:
        cursor.execute("UPDATE tools SET enabled=? WHERE name=?", (int(enabled), name))
    conn.commit()
    conn.close()
    logger.info(f"工具已更新：{name}")


def delete_tool(name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT builtin FROM tools WHERE name=?", (name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Tool '{name}' not found")
    if row[0]:
        conn.close()
        raise ValueError(f"Cannot delete builtin tool '{name}'")
    cursor.execute("DELETE FROM tools WHERE name=?", (name,))
    conn.commit()
    conn.close()
    logger.info(f"工具已删除：{name}")


# ========== 工具包装：统一日志 + 异常处理 ==========
def _wrap_builtin_tool(fn):
    """为内置工具添加统一日志和异常处理"""
    from tools.tool_response import code_error
    tool_name = fn.name

    original_func = fn.func  # 取出原始函数

    def wrapped_func(**kwargs):
        logger.info(f"[{tool_name}] 调用开始 | kwargs={kwargs}")
        try:
            result = original_func(**kwargs)
            logger.info(f"[{tool_name}] 调用成功 | result={str(result)[:100]}")
            return result
        except Exception as e:
            logger.error(f"[{tool_name}] 调用异常 | error={e}")
            return code_error(str(e))

    # 保持原有 schema 不变，只替换执行函数
    return StructuredTool(
        name=fn.name,
        description=fn.description,
        func=wrapped_func,
        args_schema=fn.args_schema,
    )


def _make_dynamic_tool(fn, name: str, description: str, params: list):
    """包装动态工具，添加统一日志、异常处理和标准返回结构"""
    from tools.tool_response import success, code_error

    def tool_fn(**kwargs):
        logger.info(f"[{name}] 调用开始 | kwargs={kwargs}")
        try:
            raw = fn(**kwargs)
            # 已经是标准结构直接返回
            try:
                parsed = json.loads(raw)
                if "state" in parsed:
                    state = parsed["state"]
                    if state == 200:
                        logger.info(f"[{name}] 调用成功 | result={str(parsed.get('result', ''))[:100]}")
                    else:
                        logger.warning(f"[{name}] 逻辑错误 | error={parsed.get('error_message', '')}")
                    return raw
            except (json.JSONDecodeError, TypeError):
                pass
            logger.info(f"[{name}] 调用成功（非标准结构，已自动包装）| result={str(raw)[:100]}")
            return success(str(raw))
        except Exception as e:
            logger.error(f"[{name}] 调用异常 | error={e}")
            return code_error(str(e))

    tool_fn.__name__ = name
    tool_fn.__doc__ = description
    return tool_fn


# ========== 加载所有启用工具 ==========
def load_active_tools():
    from pydantic import create_model

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, code, builtin FROM tools WHERE enabled=1")
    rows = cursor.fetchall()
    conn.close()

    active_tools = []

    for name, description, code, builtin in rows:
        if builtin:
            if name in BUILTIN_TOOLS:
                try:
                    wrapped = _wrap_builtin_tool(BUILTIN_TOOLS[name])
                    active_tools.append(wrapped)
                    logger.debug(f"内置工具已加载：{name}")
                except Exception as e:
                    logger.error(f"内置工具加载失败：{name} | error={e}")
        else:
            try:
                # ✅ 用沙箱执行，替换原来的裸 exec
                fn, err = execute_in_sandbox(code, name)
                if fn is None:
                    logger.warning(f"动态工具加载失败：{name} | {err}")
                    continue

                params = list(inspect.signature(fn).parameters.keys())
                logger.info(f"动态工具函数解析成功：{name} | 参数={params}")

                fields = {p: (str, ...) for p in params}
                args_schema = create_model(f"{name}_schema", **fields)

                wrapped_fn = _make_dynamic_tool(fn, name, description, params)

                dynamic_tool = StructuredTool(
                    name=name,
                    description=description,
                    func=wrapped_fn,
                    args_schema=args_schema,
                )
                active_tools.append(dynamic_tool)
                logger.info(f"动态工具注册成功：{name}")

            except Exception as e:
                logger.error(f"动态工具加载异常：{name} | error={e}")

    logger.info(f"已加载工具列表：{[t.name for t in active_tools]}")
    return active_tools


init_tool_db()