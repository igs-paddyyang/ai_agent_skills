"""SQLite 工具函式 — 初始化 events.db schema。

提供 init_db() 建立 events 表、cost_records 表與對應索引。
所有 SQL 使用參數化查詢，遵循安全規範。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_EVENTS_SCHEMA = """\
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    event_type  TEXT    NOT NULL,
    instance_name TEXT,
    data        TEXT    NOT NULL DEFAULT '{}',
    CHECK (event_type IN (
        'instance_started', 'instance_stopped', 'instance_crashed',
        'message_sent', 'message_received',
        'cost_warning', 'cost_limit_reached',
        'hang_detected', 'context_rotated',
        'schedule_triggered', 'access_denied',
        'tool_decision', 'hang_action'
    ))
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_instance ON events(instance_name);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
"""

_COST_RECORDS_SCHEMA = """\
CREATE TABLE IF NOT EXISTS cost_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_name   TEXT    NOT NULL,
    amount_usd      REAL    NOT NULL,
    recorded_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    date_key        TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cost_date ON cost_records(date_key, instance_name);
"""


def init_db(path: str | Path) -> sqlite3.Connection:
    """建立 events.db schema 並回傳連線。

    Args:
        path: SQLite 資料庫檔案路徑，或 ``":memory:"`` 用於測試。

    Returns:
        已建立 schema 的 ``sqlite3.Connection``。
    """
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_EVENTS_SCHEMA)
    conn.executescript(_COST_RECORDS_SCHEMA)
    return conn
