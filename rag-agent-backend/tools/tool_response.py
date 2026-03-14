# tools/tool_response.py
import json
from dataclasses import dataclass


@dataclass
class ToolResponse:
    state: int          # 200=成功 400=代码错误 500=逻辑错误
    result: str         # 成功时为结果内容，失败时为空字符串
    error_message: str  # 成功时为空字符串，失败时为错误原因

    def to_json(self) -> str:
        return json.dumps({
            "state": self.state,
            "result": self.result,
            "error_message": self.error_message
        }, ensure_ascii=False)


def success(result: str) -> str:
    """工具执行成功"""
    return ToolResponse(state=200, result=result, error_message="").to_json()


def logic_error(error_message: str) -> str:
    """业务逻辑错误，代码本身运行正常，但结果不符合预期，比如查不到数据"""
    return ToolResponse(state=500, result="", error_message=error_message).to_json()


def code_error(error_message: str) -> str:
    """代码执行异常，比如语法错误、网络错误、类型错误等"""
    return ToolResponse(state=400, result="", error_message=error_message).to_json()