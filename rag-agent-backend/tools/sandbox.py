# tools/sandbox.py
"""
自定义工具代码沙箱
限制可用的内置函数和模块，防止恶意代码执行
"""
import builtins

# ✅ 白名单内置函数，危险函数全部排除
SAFE_BUILTINS = {
    # 类型转换
    'int': int, 'float': float, 'str': str, 'bool': bool,
    'bytes': bytes, 'list': list, 'dict': dict, 'tuple': tuple,
    'set': set, 'frozenset': frozenset,

    # 常用函数
    'len': len, 'range': range, 'enumerate': enumerate,
    'zip': zip, 'map': map, 'filter': filter,
    'sorted': sorted, 'reversed': reversed,
    'min': min, 'max': max, 'sum': sum, 'abs': abs,
    'round': round, 'print': print,

    # 判断
    'isinstance': isinstance, 'issubclass': issubclass,
    'hasattr': hasattr, 'getattr': getattr,

    # 异常
    'Exception': Exception, 'ValueError': ValueError,
    'TypeError': TypeError, 'KeyError': KeyError,
    'IndexError': IndexError, 'AttributeError': AttributeError,
    'RuntimeError': RuntimeError,  # ✅ 新增
    'NotImplementedError': NotImplementedError,  # ✅ 新增
    'StopIteration': StopIteration,  # ✅ 新增
    'OverflowError': OverflowError,  # ✅ 新增
    'ZeroDivisionError': ZeroDivisionError,  # ✅ 新增
    'AssertionError': AssertionError,  # ✅ 新增

    # 其他安全的
    'repr': repr, 'hash': hash,
    'True': True, 'False': False, 'None': None,
}

# ✅ 白名单模块，只允许 import 这些
ALLOWED_MODULES = {
    'json', 'math', 'datetime', 're', 'random',
    'string', 'collections', 'itertools', 'functools',
    'decimal', 'fractions', 'statistics',
    'tools.tool_response',   # 允许导入标准返回结构
}


def _safe_import(name, *args, **kwargs):
    """拦截 import，只允许白名单模块"""
    # 取顶层模块名
    top_module = name.split('.')[0]
    if name not in ALLOWED_MODULES and top_module not in ALLOWED_MODULES:
        raise ImportError(f"禁止导入模块 '{name}'，不在安全白名单中")
    return builtins.__import__(name, *args, **kwargs)


def make_sandbox() -> dict:
    """构建沙箱执行环境"""
    safe_builtins = dict(SAFE_BUILTINS)
    safe_builtins['__import__'] = _safe_import

    return {
        '__builtins__': safe_builtins,
        '__name__': '__sandbox__',
        '__doc__': None,
    }


def validate_code(code: str) -> tuple[bool, str]:
    """
    静态检查代码是否包含危险操作
    返回 (is_safe, error_message)
    """
    # 危险关键字黑名单
    dangerous_patterns = [
        ('__import__',  '禁止直接调用 __import__'),
        ('open(',       '禁止文件操作'),
        ('exec(',       '禁止嵌套 exec'),
        ('eval(',       '禁止使用 eval'),
        ('compile(',    '禁止使用 compile'),
        ('globals(',    '禁止访问 globals'),
        ('locals(',     '禁止访问 locals'),
        ('vars(',       '禁止访问 vars'),
        ('dir(',        '禁止使用 dir'),
        ('getattr(',    '禁止使用 getattr'),
        ('setattr(',    '禁止使用 setattr'),
        ('delattr(',    '禁止使用 delattr'),
        ('subprocess',  '禁止调用子进程'),
        ('os.system',   '禁止系统调用'),
        ('os.popen',    '禁止系统调用'),
        ('shutil',      '禁止文件系统操作'),
        ('socket',      '禁止网络操作'),
        ('requests',    '禁止网络请求'),
        ('urllib',      '禁止网络请求'),
        ('httpx',       '禁止网络请求'),
        ('__class__',   '禁止访问类属性'),
        ('__bases__',   '禁止访问类属性'),
        ('__subclasses__', '禁止访问子类'),
        ('__mro__',     '禁止访问方法解析顺序'),
    ]

    for pattern, reason in dangerous_patterns:
        if pattern in code:
            return False, f"代码校验失败：{reason}"

    return True, ""


def execute_in_sandbox(code: str, function_name: str):
    """
    在沙箱中执行代码并返回函数对象
    返回 (function, error_message)
    """
    # 1. 静态检查
    is_safe, err = validate_code(code)
    if not is_safe:
        return None, err

    # 2. 编译检查语法
    try:
        compiled = compile(code, "<sandbox>", "exec")
    except SyntaxError as e:
        return None, f"代码语法错误：{e}"

    # 3. 沙箱执行
    try:
        namespace = make_sandbox()
        exec(compiled, namespace)
    except Exception as e:
        return None, f"代码执行失败：{e}"

    # 4. 取出函数
    fn = namespace.get(function_name)
    if fn is None:
        return None, f"未找到函数 '{function_name}'，请确保函数名与工具名一致"

    if not callable(fn):
        return None, f"'{function_name}' 不是可调用函数"

    return fn, ""