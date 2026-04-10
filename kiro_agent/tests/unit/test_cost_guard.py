"""CostGuard 單元測試。

使用 :memory: SQLite 資料庫，透過 monkeypatch 控制 date_key。
"""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest

from kiro_agent.config import CostGuardConfig
from kiro_agent.cost_guard import CostGuard
from kiro_agent.db import init_db
from kiro_agent.event_logger import EventLogger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def conn() -> sqlite3.Connection:
    """建立 in-memory DB 並回傳連線。"""
    return init_db(":memory:")


@pytest.fixture()
def event_logger(conn: sqlite3.Connection) -> EventLogger:
    return EventLogger(conn=conn)


@pytest.fixture()
def config() -> CostGuardConfig:
    return CostGuardConfig(
        daily_limit_usd=10.0,
        warn_at_percentage=80.0,
        timezone="Asia/Taipei",
    )


@pytest.fixture()
def guard(config: CostGuardConfig, conn: sqlite3.Connection, event_logger: EventLogger) -> CostGuard:
    return CostGuard(config=config, db_conn=conn, event_logger=event_logger)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixed_today_key(key: str):
    """回傳一個 patch，讓 CostGuard._today_key 固定回傳指定 date_key。"""
    return patch.object(CostGuard, "_today_key", return_value=key)


# ---------------------------------------------------------------------------
# record_cost tests
# ---------------------------------------------------------------------------

class TestRecordCost:
    """驗證 record_cost 正確寫入 cost_records 表。"""

    def test_inserts_into_db(self, guard: CostGuard, conn: sqlite3.Connection) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 1.5)

        rows = conn.execute("SELECT * FROM cost_records").fetchall()
        assert len(rows) == 1
        row = dict(rows[0])
        assert row["instance_name"] == "agent-1"
        assert row["amount_usd"] == 1.5
        assert row["date_key"] == "2025-01-15"

    def test_multiple_records(self, guard: CostGuard, conn: sqlite3.Connection) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 1.0)
            guard.record_cost("agent-1", 2.0)
            guard.record_cost("agent-2", 3.0)

        count = conn.execute("SELECT COUNT(*) FROM cost_records").fetchone()[0]
        assert count == 3


# ---------------------------------------------------------------------------
# get_daily_cost tests
# ---------------------------------------------------------------------------

class TestGetDailyCost:
    """驗證 get_daily_cost 回傳正確的今日累計費用。"""

    def test_returns_sum(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 1.5)
            guard.record_cost("agent-1", 2.5)
            total = guard.get_daily_cost("agent-1")
        assert total == pytest.approx(4.0)

    def test_returns_zero_when_no_records(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            total = guard.get_daily_cost("agent-1")
        assert total == 0.0

    def test_different_instances_independent(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 5.0)
            guard.record_cost("agent-2", 3.0)
            assert guard.get_daily_cost("agent-1") == pytest.approx(5.0)
            assert guard.get_daily_cost("agent-2") == pytest.approx(3.0)

    def test_different_date_keys_dont_interfere(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 5.0)

        with _fixed_today_key("2025-01-16"):
            guard.record_cost("agent-1", 2.0)
            assert guard.get_daily_cost("agent-1") == pytest.approx(2.0)

        # 切回前一天也只看到前一天的
        with _fixed_today_key("2025-01-15"):
            assert guard.get_daily_cost("agent-1") == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# check_limits tests
# ---------------------------------------------------------------------------

class TestCheckLimits:
    """驗證 check_limits 的閾值判斷邏輯。"""

    def test_no_alerts_below_threshold(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 3.0)  # 30% of 10.0, below 80%
            alerts = guard.check_limits(["agent-1"])
        assert alerts == []

    def test_warning_at_warn_percentage(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 8.0)  # 80% of 10.0
            alerts = guard.check_limits(["agent-1"])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "warning"
        assert alerts[0].instance_name == "agent-1"
        assert alerts[0].daily_cost_usd == pytest.approx(8.0)
        assert alerts[0].limit_usd == pytest.approx(10.0)

    def test_warning_between_warn_and_limit(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 9.0)  # 90%, above warn but below limit
            alerts = guard.check_limits(["agent-1"])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "warning"

    def test_limit_reached_at_daily_limit(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 10.0)  # exactly at limit
            alerts = guard.check_limits(["agent-1"])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "limit_reached"

    def test_limit_reached_above_daily_limit(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 12.0)  # above limit
            alerts = guard.check_limits(["agent-1"])
        assert len(alerts) == 1
        assert alerts[0].alert_type == "limit_reached"

    def test_multiple_instances(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 8.5)   # warning
            guard.record_cost("agent-2", 10.5)  # limit_reached
            guard.record_cost("agent-3", 2.0)   # safe
            alerts = guard.check_limits(["agent-1", "agent-2", "agent-3"])

        assert len(alerts) == 2
        types = {a.instance_name: a.alert_type for a in alerts}
        assert types["agent-1"] == "warning"
        assert types["agent-2"] == "limit_reached"

    def test_auto_discover_instances(self, guard: CostGuard) -> None:
        """check_limits(None) 自動查詢今日有記錄的 Instance。"""
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 9.0)
            guard.record_cost("agent-2", 11.0)
            alerts = guard.check_limits()

        assert len(alerts) == 2

    def test_logs_cost_warning_event(
        self, guard: CostGuard, conn: sqlite3.Connection
    ) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 8.0)
            guard.check_limits(["agent-1"])

        rows = conn.execute(
            "SELECT * FROM events WHERE event_type = 'cost_warning'"
        ).fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["instance_name"] == "agent-1"

    def test_logs_cost_limit_reached_event(
        self, guard: CostGuard, conn: sqlite3.Connection
    ) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 10.0)
            guard.check_limits(["agent-1"])

        rows = conn.execute(
            "SELECT * FROM events WHERE event_type = 'cost_limit_reached'"
        ).fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["instance_name"] == "agent-1"


# ---------------------------------------------------------------------------
# reset_daily tests
# ---------------------------------------------------------------------------

class TestResetDaily:
    """驗證 reset_daily 語意正確（date_key 機制自動隔離）。"""

    def test_reset_daily_does_not_delete_records(
        self, guard: CostGuard, conn: sqlite3.Connection
    ) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 5.0)
            guard.reset_daily()

        count = conn.execute("SELECT COUNT(*) FROM cost_records").fetchone()[0]
        assert count == 1  # 記錄仍在

    def test_new_day_starts_fresh(self, guard: CostGuard) -> None:
        with _fixed_today_key("2025-01-15"):
            guard.record_cost("agent-1", 9.0)

        # 新的一天，費用歸零
        with _fixed_today_key("2025-01-16"):
            assert guard.get_daily_cost("agent-1") == 0.0
