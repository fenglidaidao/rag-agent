from tools.weather_tool import get_weather
import json
import asyncio
from langgraph.prebuilt import create_react_agent
from core.llm import get_llm
from memory.memory import memory
from tools.tool_registry import load_active_tools
from core.logger import get_logger
logger = get_logger("tool_agent")

llm = get_llm()

tools = [get_weather]

agent = create_react_agent(
    llm,
    tools,
    checkpointer=memory
)

def parse_tool_response(content: str) -> str:
    try:
        parsed = json.loads(content)
        if "state" not in parsed:
            return content
        state = parsed["state"]
        result = parsed.get("result", "")
        error_message = parsed.get("error_message", "")
        if state == 200:
            return result
        elif state == 500:
            return f"查询未能返回结果：{error_message}"
        elif state == 400:
            return f"工具执行出现错误：{error_message}"
        else:
            return content
    except (json.JSONDecodeError, KeyError):
        return content


def tool_agent(question: str, thread_id: str = "default"):
    logger.info(">>> [tool_agent] 开始执行")
    logger.info(">>> [tool_agent] 加载工具列表...")
    active_tools = load_active_tools()
    logger.info(f">>> [tool_agent] 已加载工具：{[t.name for t in active_tools]}")

    logger.info(">>> [tool_agent] 初始化 LLM...")
    llm = get_llm()

    logger.info(">>> [tool_agent] 创建 ReAct agent...")
    agent = create_react_agent(llm, active_tools, checkpointer=memory)

    logger.info(">>> [tool_agent] 调用 agent.invoke...")
    result = agent.invoke(
        {"messages": [("user", question)]},
        config={"configurable": {"thread_id": thread_id}}
    )
    logger.info(">>> [tool_agent] agent.invoke 完成")

    last_message = result["messages"][-1].content
    logger.info(f">>> [tool_agent] 原始返回：{last_message}")

    return parse_tool_response(last_message)