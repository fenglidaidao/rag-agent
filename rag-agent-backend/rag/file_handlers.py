import base64
from pathlib import Path
from PIL import Image
from langchain_core.messages import HumanMessage
from core.llm import get_vision_llm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from core.config import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL

# rag/file_handlers.py

def process_text_file(file_name, file_content):
    """处理文本文件：存向量库 + 返回原始文本内容"""
    text_content = file_content.decode("utf-8")
    doc = Document(page_content=text_content, metadata={"file_name": file_name})

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents([doc])

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    vectordb = FAISS.from_documents(chunks, embeddings)
    VECTOR_DIR = Path(__file__).resolve().parent.parent / "vectorstore"
    vectordb.save_local(str(VECTOR_DIR))  # ✅ 绝对路径，与 ingest.py 一致

    # ✅ 返回实际文本内容，而不是处理描述
    chunks_text = "\n\n".join([chunk.page_content for chunk in chunks])
    return chunks_text


def process_csv_file(file_name, file_content):
    """处理CSV文件"""
    lines = file_content.decode('utf-8').splitlines()
    chunks = [line for line in lines if line.strip()]
    # ✅ 返回实际内容
    return "\n".join(chunks)


def process_image_file(file_name, file_content):
    """处理图片文件，调用视觉模型描述图片内容"""

    # ✅ 将图片转为 base64
    image_data = base64.b64encode(file_content).decode("utf-8")

    # ✅ 判断图片格式
    suffix = file_name.split(".")[-1].lower()
    media_type_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    media_type = media_type_map.get(suffix, "image/png")

    # ✅ 使用 LangChain 多模态消息格式
    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{image_data}"
            }
        },
        {
            "type": "text",
            "text": "请详细描述这张图片的内容。"
        }
    ])

    vision_llm = get_vision_llm()
    response = vision_llm.invoke([message])  # ✅ 传消息列表

    return response.content