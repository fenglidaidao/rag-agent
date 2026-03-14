# rag/knowledge_manager.py
import sqlite3
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from core.config import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL
from rag.ingest import ingest_file, get_file_hash, initialize_hash_db
from core.logger import get_logger
logger = get_logger("knowledge_manager")


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DIR = BASE_DIR / "vectorstore"
HASH_DB = BASE_DIR / "file_hashes.db"

# 文件元数据表（记录哪些文件在知识库里）
def init_knowledge_db():
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_files (
            filename    TEXT PRIMARY KEY,
            file_hash   TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_knowledge_file_record(filename: str, file_hash: str):
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO knowledge_files (filename, file_hash)
        VALUES (?, ?)
    """, (filename, file_hash))
    conn.commit()
    conn.close()


def list_knowledge_files():
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, uploaded_at FROM knowledge_files ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"filename": r[0], "uploaded_at": r[1]} for r in rows]


def delete_knowledge_file_record(filename: str):
    conn = sqlite3.connect(HASH_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM knowledge_files WHERE filename=?", (filename,))
    conn.commit()
    conn.close()


def upload_to_knowledge_base(filename: str, file_content: bytes) -> dict:
    """保存文件到 data/ 并 ingest 进向量库"""
    from rag.ingest import validate_file, ingest_file, initialize_hash_db

    # ✅ 先校验
    is_valid, error_msg = validate_file(filename, file_content)
    if not is_valid:
        return {"success": False, "message": error_msg}

    DATA_DIR.mkdir(exist_ok=True)
    initialize_hash_db()
    init_knowledge_db()

    # 写入文件
    file_path = DATA_DIR / filename
    with open(file_path, "wb") as f:
        f.write(file_content)

    # ingest
    success, msg = ingest_file(str(file_path))

    if success:
        file_hash = get_file_hash(str(file_path))
        save_knowledge_file_record(filename, file_hash)

    return {"success": success, "message": msg}


def delete_from_knowledge_base(filename: str):
    """从 data/ 删除文件，并重建向量库"""
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"File '{filename}' not found in data directory")

    # 删除物理文件
    file_path.unlink()

    # 删除元数据记录
    delete_knowledge_file_record(filename)

    # 重建向量库（从剩余文件重新 ingest）
    _rebuild_vectorstore()

    return f"File '{filename}' removed from knowledge base"


def _rebuild_vectorstore():
    """删除文件后重建整个向量库"""
    import shutil
    from rag.ingest import ingest_file, initialize_hash_db
    from rag.ingest import HASH_DB as HASH_DB_PATH

    # 清空旧向量库
    if VECTOR_DIR.exists():
        shutil.rmtree(str(VECTOR_DIR))

    # 清空 hash 记录（重新 ingest）
    conn = sqlite3.connect(HASH_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM file_hashes")
    conn.commit()
    conn.close()

    # 重新 ingest data/ 下所有剩余文件
    for file in DATA_DIR.iterdir():
        if file.is_file():
            ingest_file(str(file))

    logger.info("Vectorstore rebuilt successfully")