from langchain_openai import ChatOpenAI
from core.config import OPENAI_API_KEY, OPENAI_BASE_URL, VISION_MODEL, MODEL_NAME


def get_llm():
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0,
        streaming=False  # ✅ 改为 False
    )

def get_vision_llm():

    return ChatOpenAI(
        model=VISION_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0
    )

def get_streaming_llm():
    """流式输出专用"""
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0,
        streaming=True
    )