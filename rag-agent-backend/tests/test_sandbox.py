# tests/test_sandbox.py
import pytest
from tools.sandbox import validate_code, execute_in_sandbox, make_sandbox

# ============================================================
# 1. validate_code 静态检查
# ============================================================

class TestValidateCode:

    def test_safe_code_passes(self):
        """正常代码应通过校验"""
        code = """
def add(a: str, b: str) -> str:
    from tools.tool_response import success
    result = int(a) + int(b)
    return success(f"结果：{result}")
"""
        is_safe, err = validate_code(code)
        assert is_safe is True
        assert err == ""

    def test_block_open(self):
        """禁止文件操作"""
        code = "def tool(x): open('/etc/passwd').read()"
        is_safe, err = validate_code(code)
        assert is_safe is False
        assert "文件操作" in err

    def test_block_subprocess(self):
        """禁止调用子进程"""
        code = "import subprocess\ndef tool(x): subprocess.run(['rm', '-rf', '/'])"
        is_safe, err = validate_code(code)
        assert is_safe is False
        assert "子进程" in err

    def test_block_eval(self):
        """禁止 eval"""
        code = "def tool(x): return eval(x)"
        is_safe, err = validate_code(code)
        assert is_safe is False
        assert "eval" in err

    def test_block_nested_exec(self):
        """禁止嵌套 exec"""
        code = "def tool(x): exec('import os')"
        is_safe, err = validate_code(code)
        assert is_safe is False

    def test_block_requests(self):
        """禁止网络请求"""
        code = "import requests\ndef tool(x): requests.get('http://evil.com')"
        is_safe, err = validate_code(code)
        assert is_safe is False
        assert "网络请求" in err

    def test_block_socket(self):
        """禁止 socket"""
        code = "import socket\ndef tool(x): socket.connect(('evil.com', 80))"
        is_safe, err = validate_code(code)
        assert is_safe is False

    def test_block_dunder_class(self):
        """禁止访问 __class__ 等魔法属性（防止沙箱逃逸）"""
        code = "def tool(x): return x.__class__.__bases__"
        is_safe, err = validate_code(code)
        assert is_safe is False

    def test_block_os_system(self):
        """禁止 os.system"""
        code = "import os\ndef tool(x): os.system('whoami')"
        is_safe, err = validate_code(code)
        assert is_safe is False


# ============================================================
# 2. execute_in_sandbox 执行测试
# ============================================================

class TestExecuteInSandbox:

    def test_valid_function_executes(self):
        """正常函数能成功执行"""
        code = """
def add_tool(a: str, b: str) -> str:
    from tools.tool_response import success, code_error
    try:
        result = int(a) + int(b)
        return success(f"两数之和：{result}")
    except Exception as e:
        return code_error(str(e))
"""
        fn, err = execute_in_sandbox(code, "add_tool")
        assert err == ""
        assert fn is not None
        result = fn("3", "5")
        assert "8" in result

    def test_math_module_allowed(self):
        """白名单模块 math 可以使用"""
        code = """
def sqrt_tool(n: str) -> str:
    import math
    from tools.tool_response import success
    return success(str(math.sqrt(float(n))))
"""
        fn, err = execute_in_sandbox(code, "sqrt_tool")
        assert err == ""
        assert fn is not None
        result = fn("9")
        assert "3.0" in result

    def test_json_module_allowed(self):
        """白名单模块 json 可以使用"""
        code = """
def parse_tool(data: str) -> str:
    import json
    from tools.tool_response import success, logic_error
    try:
        parsed = json.loads(data)
        return success(str(parsed))
    except Exception as e:
        return logic_error(str(e))
"""
        fn, err = execute_in_sandbox(code, "parse_tool")
        assert err == ""
        result = fn('{"key": "value"}')
        assert "value" in result

    def test_blocked_module_raises(self):
        """黑名单模块 os 不能 import"""
        code = """
def bad_tool(x: str) -> str:
    import os
    return os.getcwd()
"""
        fn, err = execute_in_sandbox(code, "bad_tool")
        # 静态检查不会拦截（os 本身不在黑名单关键字），但运行时 import 拦截
        if fn is not None:
            with pytest.raises(ImportError):
                fn("test")

    def test_syntax_error_caught(self):
        """语法错误应返回明确的错误信息"""
        code = "def broken(x:\n    return x"
        fn, err = execute_in_sandbox(code, "broken")
        assert fn is None
        assert "语法错误" in err

    def test_function_not_found(self):
        """函数名不匹配时返回明确错误"""
        code = "def my_func(x): return x"
        fn, err = execute_in_sandbox(code, "wrong_name")
        assert fn is None
        assert "未找到函数" in err

    def test_runtime_exception_caught(self):
        """运行时异常能被捕获"""
        code = "def crash_tool(x): raise RuntimeError('boom')"
        fn, err = execute_in_sandbox(code, "crash_tool")
        # 代码本身没有语法问题，函数能取出
        assert fn is not None
        # 调用时抛出异常
        with pytest.raises(RuntimeError):
            fn("test")

    def test_cannot_access_builtins_directly(self):
        """不能通过 __builtins__ 访问危险函数"""
        code = """
def escape_tool(x: str) -> str:
    # 尝试通过 builtins 逃逸
    import builtins
    return str(dir(builtins))
"""
        fn, err = execute_in_sandbox(code, "escape_tool")
        # builtins 不在白名单，应被拦截
        if fn is not None:
            with pytest.raises((ImportError, Exception)):
                fn("test")


# ============================================================
# 3. make_sandbox 环境检查
# ============================================================

class TestSandboxEnvironment:

    def test_sandbox_has_no_open(self):
        """沙箱环境中不应有 open 函数"""
        sandbox = make_sandbox()
        builtins = sandbox['__builtins__']
        assert 'open' not in builtins

    def test_sandbox_has_no_compile(self):
        """沙箱环境中不应有 compile 函数"""
        sandbox = make_sandbox()
        builtins = sandbox['__builtins__']
        assert 'compile' not in builtins

    def test_sandbox_has_safe_functions(self):
        """沙箱中应有常用安全函数"""
        sandbox = make_sandbox()
        builtins = sandbox['__builtins__']
        for name in ['len', 'str', 'int', 'float', 'range', 'enumerate']:
            assert name in builtins, f"{name} 应在沙箱白名单中"