"""事件日誌 — 寫入 events.db，支援查詢與自動清理。

EventLogger 封裝 events 表的 CRUD 操作，
所有 SQL 使用參數化查詢（? 佔位符），遵循安全規範。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from kiro_agent.db import init_db

# 允許的事件類型（與 DB CHECK 約束一致）
VALID_EVENT_TYPES = frozenset(
    {
        "instance_started",
        "instance_stopped",
        "instance_crashed",
        "message_sent",
        "message_received",
        "cost_warning",
        "cost_limit_reached",
        "hang_detected",
        "context_rotated",
        "schedule_triggered",
        "access_denied",
        "tool_decision",
        "hang_action",
    }
)


class EventLogger:
    """事件日誌管理器。

    Args:
        db_path: SQLite 資料庫路徑，或 ``":memory:"`` 用於測試。
        conn: 可選的已建立連線（優先使用），方便測試注入。
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        *,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        self._conn = conn if conn is not None else init_db(db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log(
        self,
        event_type: str,
        instance_name: str | None = None,
        data: dict | None = None,
    ) -> None:
        """記錄一筆事件。

        Args:
            event_type: 事件類型，必須在 VALID_EVENT_TYPES 中。
            instance_name: 關聯的 Instance 名稱（可為 None）。
            data: 附加資料字典，會以 JSON 儲存。

        Raises:
            ValueError: 若 event_type 不在允許清單中。
        """
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'. "
                f"Must be one of: {sorted(VALID_EVENT_TYPES)}"
            )
        data_json = json.dumps(data or {}, ensure_ascii=False)
        self._conn.execute(
            "INSERT INTO events (event_type, instance_name, data) VALUES (?, ?, ?)",
            (event_type, instance_name, data_json),
        )
        self._conn.commit()

    def query(
        self,
        event_type: str | None = None,
        instance_name: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """查詢事件日誌。

        Args:
            event_type: 篩選事件類型（None 表示不篩選）。
            instance_name: 篩選 Instance 名稱（None 表示不篩選）。
            limit: 回傳筆數上限，預設 50。

        Returns:
            事件字典清單，依時間倒序排列。
        """
        clauses: list[str] = []
        params: list[object] = []

        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(event_type)
        if instance_name is not None:
            clauses.append("instance_name = ?")
            params.append(instance_name)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM events{where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def cleanup(self, days: int = 30) -> int:
        """清理超過指定天數的事件記錄。

        Args:
            days: 保留天數，預設 30。

        Returns:
            被刪除的記錄筆數。
        """
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).strftime("%Y-%m-%dT%H:%M:%S")
        cursor = self._conn.execute(
            "DELETE FROM events WHERE timestamp < ?",
            (cutoff,),
        )
        self._conn.commit()
        return cursor.rowcount

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """將 sqlite3.Row 轉為普通 dict，data 欄位解析為 dict。"""
        d = dict(row)
        try:
            d["data"] = json.loads(d["data"])
        except (json.JSONDecodeError, TypeError):
            pass
        return d
