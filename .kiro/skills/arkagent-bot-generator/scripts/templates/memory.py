"""Memory System 模板 — SHORT_TERM_PY, LONG_TERM_PY, MEMORY_INIT_PY"""

# ── memory/short_term.py ──
SHORT_TERM_PY = '''"""短期記憶 — 對話 context（in-memory, max_turns 限制）"""
import logging
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """
    對話上下文記憶，使用 deque 實作固定長度佇列。
    每條記錄包含 role（user/assistant）、content、timestamp。
    """

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self._history: deque[dict] = deque(maxlen=max_turns)
        logger.info(f"ShortTermMemory 初始化（max_turns={max_turns}）")

    def add(self, role: str, content: str):
        """新增一條對話記錄"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self._history.append(entry)

    def get_history(self, last_n: int = None) -> list[dict]:
        """取得對話歷史，可指定最近 N 條"""
        history = list(self._history)
        if last_n and last_n < len(history):
            return history[-last_n:]
        return history

    def get_context_string(self, last_n: int = None) -> str:
        """將對話歷史格式化為字串，供 LLM prompt 使用"""
        history = self.get_history(last_n)
        lines = []
        for entry in history:
            role = "使用者" if entry["role"] == "user" else "助理"
            lines.append(f"{role}：{entry['content']}")
        return "\\n".join(lines)

    def clear(self):
        """清空對話歷史"""
        self._history.clear()
        logger.info("ShortTermMemory 已清空")

    @property
    def count(self) -> int:
        return len(self._history)
'''

# ── memory/long_term.py ──
LONG_TERM_PY = '''"""長期記憶 — SQLite 持久化儲存"""
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    長期記憶，使用 SQLite 持久化。
    支援 CRUD 操作 + 關鍵字搜尋。
    預留介面供未來擴展 vector DB。
    """

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"LongTermMemory 初始化（db={db_path}）")

    def _init_db(self):
        """建立記憶表"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL DEFAULT 'default',
                category TEXT NOT NULL DEFAULT 'general',
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_agent
            ON memories(agent_name)
        """)
        conn.commit()
        conn.close()

    def store(self, content: str, agent_name: str = "default",
              category: str = "general", metadata: dict = None) -> int:
        """儲存一條記憶，回傳 id"""
        import json
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO memories (agent_name, category, content, metadata) VALUES (?, ?, ?, ?)",
            (agent_name, category, content, meta_str),
        )
        conn.commit()
        mem_id = cursor.lastrowid
        conn.close()
        return mem_id

    def search(self, keyword: str, agent_name: str = "default",
               limit: int = 10) -> list[dict]:
        """關鍵字搜尋記憶"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM memories WHERE agent_name = ? AND content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (agent_name, f"%{keyword}%", limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_recent(self, agent_name: str = "default", limit: int = 20) -> list[dict]:
        """取得最近的記憶"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM memories WHERE agent_name = ? ORDER BY created_at DESC LIMIT ?",
            (agent_name, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete(self, memory_id: int) -> bool:
        """刪除指定記憶"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def count(self, agent_name: str = "default") -> int:
        """計算記憶數量"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE agent_name = ?",
            (agent_name,),
        ).fetchone()
        conn.close()
        return row[0] if row else 0
'''

# ── memory/__init__.py ──
MEMORY_INIT_PY = '''"""ArkAgent Memory System — 短期 + 長期記憶"""
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
'''
