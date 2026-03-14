# auth/models.py
import sqlite3
from pathlib import Path

AUTH_DB = Path(__file__).resolve().parent.parent / "auth.db"


def init_auth_db():
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 会话表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            thread_id   TEXT PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            title       TEXT DEFAULT '新对话',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # 消息历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id   TEXT NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES conversations(thread_id)
        )
    """)
    conn.commit()
    conn.close()


# ========== 用户操作 ==========
def create_user(username: str, hashed_password: str) -> bool:
    try:
        conn = sqlite3.connect(AUTH_DB)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(username: str) -> dict | None:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "password": row[2]}
    return None


# ========== 会话操作 ==========
def create_conversation(thread_id: str, user_id: int, title: str = "新对话"):
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO conversations (thread_id, user_id, title) VALUES (?, ?, ?)",
        (thread_id, user_id, title)
    )
    conn.commit()
    conn.close()


def get_user_conversations(user_id: int) -> list:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT thread_id, title, created_at, updated_at FROM conversations WHERE user_id=? ORDER BY updated_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"thread_id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]}
        for r in rows
    ]


def verify_conversation_owner(thread_id: str, user_id: int) -> bool:
    """验证会话是否属于该用户"""
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM conversations WHERE thread_id=? AND user_id=?",
        (thread_id, user_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def delete_conversation(thread_id: str, user_id: int) -> bool:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM conversations WHERE thread_id=? AND user_id=?",
        (thread_id, user_id)
    )
    affected = cursor.rowcount
    # 同时删除消息记录
    cursor.execute("DELETE FROM messages WHERE thread_id=?", (thread_id,))
    conn.commit()
    conn.close()
    return affected > 0


def update_conversation_time(thread_id: str):
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE thread_id=?",
        (thread_id,)
    )
    conn.commit()
    conn.close()


# ========== 消息历史操作 ==========
def save_message(thread_id: str, role: str, content: str):
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, role, content)
    )
    conn.commit()
    conn.close()


def get_conversation_messages(thread_id: str) -> list:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, created_at FROM messages WHERE thread_id=? ORDER BY created_at ASC",
        (thread_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]


def update_conversation_title(thread_id: str, user_id: int, title: str) -> bool:
    conn = sqlite3.connect(AUTH_DB)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET title=? WHERE thread_id=? AND user_id=?",
        (title, thread_id, user_id)
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

init_auth_db()