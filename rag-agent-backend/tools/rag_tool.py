# tools/rag_tool.py
from langchain.tools import tool
from tools.tool_response import success, logic_error, code_error
from core.logger import get_logger

logger = get_logger("rag_tool")


@tool
def search_docs(query: str) -> str:
    """搜索内部知识库"""
    logger.info(f"search_docs 被调用 | query={query}")
    try:
        if not query or not query.strip():
            logger.warning("query 参数为空")
            return logic_error("查询内容不能为空")

        from rag.rag_chain import run_rag
        result = run_rag(query)

        if not result or not result.strip():
            logger.warning(f"知识库未找到相关内容 | query={query}")
            return logic_error("知识库中未找到相关内容")

        logger.info(f"search_docs 成功 | query={query} result={str(result)[:100]}")
        return success(result)

    except Exception as e:
        logger.error(f"search_docs 异常 | error={e}")
        return code_error(str(e))
