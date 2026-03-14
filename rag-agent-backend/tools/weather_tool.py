# tools/weather_tool.py
from langchain.tools import tool
from tools.tool_response import success, logic_error, code_error
from core.logger import get_logger

logger = get_logger("weather_tool")


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    logger.info(f"get_weather 被调用 | city={city}")
    try:
        if not city or not city.strip():
            logger.warning("city 参数为空")
            return logic_error("城市名称不能为空")

        weather_data = {
            "上海": "25°C 晴",
            "北京": "18°C 多云",
        }

        result = weather_data.get(city.strip())
        if not result:
            logger.warning(f"未找到城市天气数据 | city={city}")
            return logic_error(f"未找到城市 '{city}' 的天气数据")

        logger.info(f"get_weather 成功 | city={city} result={result}")
        return success(f"{city} 当前天气：{result}")

    except Exception as e:
        logger.error(f"get_weather 异常 | error={e}")
        return code_error(str(e))