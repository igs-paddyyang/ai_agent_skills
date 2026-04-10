"""EventLogger 與 db.py 單元測試。

使用 :memory: SQLite 資料庫，無需檔案系統。
"""

from __future__ import annotations

import sqlite3

import pytest

from kiro_agent.db import init_db
from kiro_agent.event_logger import EventLogger, VALID_EVENT_TYPES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def conn() -> sqlite3.Connection:
    """建立 in-memory DB 並回傳連線。"""
    return init_db(":memory:")


@pytest.fixture()
def logger(conn: sqlite3.Connection) -> EventLogger:
    """建立使用 in-memory DB 的 EventLogger。"""
    return EventLogger(conn=conn)


# ---------------------------------------------------------------------------
# init_db tests
# ---------------------------------------------------------------------------


class TestInitDb:
    """驗證 init_db 建立正確的 schema。"""

    def test_events_table_exists(self, conn: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "events" in tables

    def test_cost_records_table_exists(self, conn: sqlite3.Connection) -> None:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "cost_records" in tables

    def test_events_indexes_exist(self, conn: sqlite3.Connection) -> None:
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "idx_events_type" in indexes
        assert "idx_events_instance" in indexes
        assert "idx_events_timestamp" in indexes

    def test_cost_records_index_exists(self, conn: sqlite3.Connection) -> None:
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "idx_cost_date" in indexes

    def test_row_factory_is_row(self, conn: sqlite3.Connection) -> None:
        assert conn.row_factory is sqlite3.Row


# ---------------------------------------------------------------------------
# EventLogger.log tests
# ---------------------------------------------------------------------------


class TestLog:
    """驗證 EventLogger.log() 行為。"""

    def test_log_valid_event(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        logger.log("instance_started", "agent-1", {"pid": 1234})
        rows = conn.execute("SELECT * FROM events").fetchall()
        assert len(rows) == 1
        row = dict(rows[0])
        assert row["event_type"] == "instance_started"
        assert row["instance_name"] == "agent-1"
        assert '"pid": 1234' in row["data"]

    def test_log_without_instance_name(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        logger.log("access_denied")
        rows = conn.execute("SELECT * FROM events").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["instance_name"] is None

    def test_log_without_data(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        logger.log("instance_stopped", "agent-2")
        row = dict(conn.execute("SELECT * FROM events").fetchone())
        assert row["data"] == "{}"

    def test_log_invalid_event_type_raises(self, logger: EventLogger) -> None:
        with pytest.raises(ValueError, match="Invalid event_type"):
            logger.log("not_a_real_event", "agent-1")

    def test_log_all_valid_event_types(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        for et in VALID_EVENT_TYPES:
            logger.log(et, "test-instance")
        count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        assert count == len(VALID_EVENT_TYPES)

    def test_timestamp_auto_generated(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        logger.log("instance_started", "agent-1")
        row = dict(conn.execute("SELECT * FROM events").fetchone())
        assert row["timestamp"] is not None
        assert "T" in row["timestamp"]  # ISO 8601 格式


# ---------------------------------------------------------------------------
# EventLogger.query tests
# ---------------------------------------------------------------------------


class TestQuery:
    """驗證 EventLogger.query() 行為。"""

    def test_query_returns_all(self, logger: EventLogger) -> None:
        logger.log("instance_started", "a1")
        logger.log("instance_stopped", "a2")
        results = logger.query()
        assert len(results) == 2

    def test_query_filter_by_event_type(self, logger: EventLogger) -> None:
        logger.log("instance_started", "a1")
        logger.log("instance_stopped", "a2")
        logger.log("instance_started", "a3")
        results = logger.query(event_type="instance_started")
        assert len(results) == 2
        assert all(r["event_type"] == "instance_started" for r in results)

    def test_query_filter_by_instance_name(self, logger: EventLogger) -> None:
        logger.log("instance_started", "a1")
        logger.log("instance_stopped", "a1")
        logger.log("instance_started", "a2")
        results = logger.query(instance_name="a1")
        assert len(results) == 2
        assert all(r["instance_name"] == "a1" for r in results)

    def test_query_filter_combined(self, logger: EventLogger) -> None:
        logger.log("instance_started", "a1")
        logger.log("instance_stopped", "a1")
        logger.log("instance_started", "a2")
        results = logger.query(event_type="instance_started", instance_name="a1")
        assert len(results) == 1

    def test_query_limit(self, logger: EventLogger) -> None:
        for i in range(10):
            logger.log("message_sent", f"a{i}")
        results = logger.query(limit=3)
        assert len(results) == 3

    def test_query_order_desc(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        # 手動插入帶有明確時間戳的記錄以確保排序
        conn.execute(
            "INSERT INTO events (timestamp, event_type, instance_name, data) VALUES (?, ?, ?, ?)",
            ("2024-01-01T00:00:00.000Z", "instance_started", "first", "{}"),
        )
        conn.execute(
            "INSERT INTO events (timestamp, event_type, instance_name, data) VALUES (?, ?, ?, ?)",
            ("2024-12-31T23:59:59.000Z", "instance_stopped", "last", "{}"),
        )
        conn.commit()
        results = logger.query()
        assert results[0]["instance_name"] == "last"
        assert results[1]["instance_name"] == "first"

    def test_query_data_parsed_as_dict(self, logger: EventLogger) -> None:
        logger.log("cost_warning", "a1", {"amount": 5.5, "limit": 10.0})
        results = logger.query()
        assert isinstance(results[0]["data"], dict)
        assert results[0]["data"]["amount"] == 5.5

    def test_query_empty_db(self, logger: EventLogger) -> None:
        results = logger.query()
        assert results == []


# ---------------------------------------------------------------------------
# EventLogger.cleanup tests
# ---------------------------------------------------------------------------


class TestCleanup:
    """驗證 EventLogger.cleanup() 行為。"""

    def test_cleanup_removes_old_events(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        # 插入一筆 60 天前的記錄
        conn.execute(
            "INSERT INTO events (timestamp, event_type, instance_name, data) VALUES (?, ?, ?, ?)",
            ("2020-01-01T00:00:00.000Z", "instance_started", "old", "{}"),
        )
        # 插入一筆近期記錄
        logger.log("instance_started", "new")
        conn.commit()

        deleted = logger.cleanup(days=30)
        assert deleted == 1
        remaining = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        assert remaining == 1

    def test_cleanup_keeps_recent_events(self, logger: EventLogger) -> None:
        logger.log("instance_started", "a1")
        logger.log("instance_stopped", "a2")
        deleted = logger.cleanup(days=30)
        assert deleted == 0
        assert len(logger.query()) == 2

    def test_cleanup_returns_count(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        for i in range(5):
            conn.execute(
                "INSERT INTO events (timestamp, event_type, instance_name, data) VALUES (?, ?, ?, ?)",
                ("2019-01-01T00:00:00.000Z", "message_sent", f"old-{i}", "{}"),
            )
        conn.commit()
        deleted = logger.cleanup(days=1)
        assert deleted == 5

    def test_cleanup_custom_days(self, logger: EventLogger, conn: sqlite3.Connection) -> None:
        # 插入 10 天前的記錄
        conn.execute(
            "INSERT INTO events (timestamp, event_type, instance_name, data) VALUES (?, ?, ?, ?)",
            ("2020-06-01T00:00:00.000Z", "hang_detected", "mid", "{}"),
        )
        conn.commit()
        # days=3650（10 年）不應刪除
        deleted_none = logger.cleanup(days=3650)
        assert deleted_none == 0
        # days=1 應刪除
        deleted_one = logger.cleanup(days=1)
        assert deleted_one == 1
