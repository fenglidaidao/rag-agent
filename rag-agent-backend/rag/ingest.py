# rag/ingest.py
from pathlib import Path
import hashlib
import sqlite3
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from core.config import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL
from rag.loader_router import load_document
from rag.file_handlers import process_text_file, process_image_file, process_csv_file
from core.logger import get_logger
logger = get_logger("ingest")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DIR = BASE_DIR / "vectorstore"
HASH_DB = BASE_DIR / "file_hashes.db"

# 支持的文件格式
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx", ".csv", ".png", ".jpg", ".jpeg", ".webp"}


# ========== 数据库初始化 ==========
def initialize_hash_db():
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS file_hashes (hash TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()


def file_hash_exists(file_hash: str) -> bool:
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM file_hashes WHERE hash=?", (file_hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def save_file_hash(file_hash: str):
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO file_hashes (hash) VALUES (?)", (file_hash,))
    conn.commit()
    conn.close()


def delete_file_hash(file_hash: str):
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM file_hashes WHERE hash=?", (file_hash,))
    conn.commit()
    conn.close()


def get_file_hash(file_path: str) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# ========== 文件校验 ==========
def validate_file(filename: str, file_content: bytes) -> tuple[bool, str]:
    """
    校验文件是否可处理
    返回 (is_valid, error_message)
    """
    # 检查是否为空
    if not file_content or len(file_content) == 0:
        return False, "文件内容为空，拒绝入库"

    # 检查文件格式
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        return False, f"不支持的文件格式 '{suffix}'，支持：{', '.join(SUPPORTED_SUFFIXES)}"

    return True, ""


# ========== 核心 ingest ==========
def ingest_file(file_path: str) -> tuple[bool, str]:
    """
    对单个文件进行 chunk + embedding + 存入向量库
    返回 (success, message)
    """
    initialize_hash_db()

    path = Path(file_path)

    # 格式校验
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        return False, f"不支持的文件格式：{suffix}"

    # 空文件校验
    if path.stat().st_size == 0:
        return False, f"文件为空：{path.name}"

    # 去重校验
    file_hash = get_file_hash(file_path)
    if file_hash_exists(file_hash):
        return False, f"文件 '{path.name}' 内容未变化，跳过入库"

    # 加载文档
    docs = load_document(file_path)
    if not docs:
        return False, f"文件 '{path.name}' 无法提取内容"

    # 分块
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    if not chunks:
        return False, f"文件 '{path.name}' 分块结果为空"

    logger.info(f"Loaded {len(chunks)} chunks from {path.name}")

    # 向量化存储
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )

    if VECTOR_DIR.exists():
        vectordb = FAISS.load_local(str(VECTOR_DIR), embeddings, allow_dangerous_deserialization=True)
        vectordb.add_documents(chunks)
        logger.warning(f"Vectorstore updated with '{path.name}'")
    else:
        vectordb = FAISS.from_documents(chunks, embeddings)
        logger.info(f"Vectorstore created with '{path.name}'")

    vectordb.save_local(str(VECTOR_DIR))
    save_file_hash(file_hash)

    return True, f"文件 '{path.name}' 成功入库，共 {len(chunks)} 个 chunks"


def ingest_all():
    """启动时批量处理 data/ 目录下所有文件"""
    results = []
    for file in DATA_DIR.iterdir():
        if file.is_file():
            success, msg = ingest_file(str(file))
            results.append({"file": file.name, "success": success, "message": msg})
            logger.info(msg)
    return results


# ========== user_id 隔离非全局变量：临时对话上下文 ==========
_file_contexts: dict[int, str] = {}

def store_file_content_for_prompt(content: str, user_id: int):
    _file_contexts[user_id] = content

def get_file_content_for_prompt(user_id: int = 0) -> str:
    return _file_contexts.get(user_id, "")

def clear_file_content_for_prompt(user_id: int):
    _file_contexts.pop(user_id, None)