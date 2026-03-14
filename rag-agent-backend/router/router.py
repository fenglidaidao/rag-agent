# router/router.py
from router.intent_router import route
from agents.rag_agent import rag_agent
from agents.tool_agent import tool_agent
from agents.general_agent import general_agent
from rag.ingest import get_file_content_for_prompt
from core.logger import get_logger

logger = get_logger("router")


def run_agent(question: str, thread_id: str = "default", user_id: int = 0):
    intent = route(question)

    if "rag" in intent:
        # ✅ 按 user_id 取对应的临时文件上下文
        file_context = get_file_content_for_prompt(user_id)
        if file_context:
            from core.llm import get_llm
            prompt = f"以下是已上传文件的内容：\n\n{file_context}\n\n用户问题：{question}"
            return get_llm().invoke(prompt).content
        return rag_agent(question, thread_id=thread_id)

    elif "tool" in intent:
        return tool_agent(question, thread_id=thread_id)
    else:
        return general_agent(question, thread_id=thread_id)


def run_agent_stream(question: str, thread_id: str = "default", user_id: int = 0):
    intent = route(question)

    if "tool" in intent:
        result = tool_agent(question, thread_id=thread_id)
        for char in result:
            yield char
        return

    if "rag" in intent:
        # ✅ 按 user_id 取
        file_context = get_file_content_for_prompt(user_id)
        if file_context:
            from core.llm import get_streaming_llm
            prompt = f"以下是已上传文件的内容：\n\n{file_context}\n\n用户问题：{question}"
            for chunk in get_streaming_llm().stream(prompt):
                if chunk.content:
                    yield chunk.content
            return
        result = rag_agent(question, thread_id=thread_id)
        for char in result:
            yield char
        return

    result = general_agent(question, thread_id=thread_id)
    for char in result:
        yield char