# 修复前
import sqlite3
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()  # ❌ 重启即丢失

# 修复后
from langgraph.checkpoint.sqlite import SqliteSaver
MEMORY_DB = Path(__file__).resolve().parent.parent / "memory.db"
_conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
memory = SqliteSaver(_conn)