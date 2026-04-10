"""HangDetector 單元測試。

使用 datetime 注入（now_fn）控制時間，驗證掛起偵測邏輯。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from kiro_agent.config import HangDetectorConfig
from kiro_agent.db import init_db
from kiro_agent.event_logger import EventLogger
from kiro_agent.hang_detector import HangDetector


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
def config() -> HangDetectorConfig:
    return HangDetectorConfig(enabled=True, timeout_minutes=30)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_detector(
    config: HangDetectorConfig,
    event_logger: EventLogger,
    now: datetime,
) -> tuple[HangDetector, list[datetime]]:
    """建立 HangDetector，回傳 (detector, now_holder)。

    now_holder 是一個單元素 list，修改 now_holder[0] 可改變 now_fn 回傳值。
    """
    now_holder = [now]
    detector = HangDetector(
        config=config,
        event_logger=event_logger,
        now_fn=lambda: now_holder[0],
    )
    return detector, now_holder


# ---------------------------------------------------------------------------
# update_activity tests
# ---------------------------------------------------------------------------

class TestUpdateActivity:
    """驗證 update_activity 正確記錄時間戳。"""

    def test_records_timestamp(self, config: HangDetectorConfig, event_logger: EventLogger) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, _ = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        assert detector._last_activity["agent-1"] == t0

    def test_updates_existing_timestamp(self, config: HangDetectorConfig, event_logger: EventLogger) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        assert detector._last_activity["agent-1"] == t0

        t1 = t0 + timedelta(minutes=5)
        now_holder[0] = t1
        detector.update_activity("agent-1")
        assert detector._last_activity["agent-1"] == t1

    def test_multiple_instances(self, config: HangDetectorConfig, event_logger: EventLogger) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=1)
        detector.update_activity("agent-2")

        assert detector._last_activity["agent-1"] == t0
        assert detector._last_activity["agent-2"] == t0 + timedelta(minutes=1)


# ---------------------------------------------------------------------------
# check_all tests
# ---------------------------------------------------------------------------

class TestCheckAll:
    """驗證 check_all 的超時判斷邏輯。"""

    def test_returns_empty_when_all_active(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        # 只過了 10 分鐘，timeout 是 30 分鐘
        now_holder[0] = t0 + timedelta(minutes=10)
        alerts = detector.check_all(["agent-1"])
        assert alerts == []

    def test_returns_alert_when_exceeded(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        # 過了 31 分鐘，超過 30 分鐘 timeout
        now_holder[0] = t0 + timedelta(minutes=31)
        alerts = detector.check_all(["agent-1"])

        assert len(alerts) == 1
        assert alerts[0].instance_name == "agent-1"
        assert alerts[0].last_activity == t0
        assert alerts[0].timeout_minutes == 30

    def test_exact_timeout_not_triggered(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        """剛好等於 timeout_minutes 不觸發（需要 > 而非 >=）。"""
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=30)
        alerts = detector.check_all(["agent-1"])
        assert alerts == []

    def test_unknown_instance_gets_initial_timestamp(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        """從未 update_activity 的 Instance 在 check_all 時自動記錄當前時間。"""
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, _ = _make_detector(config, event_logger, t0)

        alerts = detector.check_all(["agent-new"])
        assert alerts == []
        assert detector._last_activity["agent-new"] == t0

    def test_multiple_instances_mixed(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=20)
        detector.update_activity("agent-2")

        # 再過 15 分鐘：agent-1 已 35 分鐘（超時），agent-2 只 15 分鐘（正常）
        now_holder[0] = t0 + timedelta(minutes=35)
        alerts = detector.check_all(["agent-1", "agent-2"])

        assert len(alerts) == 1
        assert alerts[0].instance_name == "agent-1"

    def test_logs_hang_detected_event(
        self, config: HangDetectorConfig, event_logger: EventLogger, conn: sqlite3.Connection
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=31)
        detector.check_all(["agent-1"])

        rows = conn.execute(
            "SELECT * FROM events WHERE event_type = 'hang_detected'"
        ).fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["instance_name"] == "agent-1"

    def test_only_checks_provided_instances(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        """check_all 只檢查傳入的 running_instances，不檢查其他已記錄的。"""
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        detector.update_activity("agent-2")
        now_holder[0] = t0 + timedelta(minutes=31)

        # 只檢查 agent-1
        alerts = detector.check_all(["agent-1"])
        assert len(alerts) == 1
        assert alerts[0].instance_name == "agent-1"


# ---------------------------------------------------------------------------
# is_hung tests
# ---------------------------------------------------------------------------

class TestIsHung:
    """驗證 is_hung 回傳正確的布林值。"""

    def test_returns_true_when_exceeded(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=31)
        assert detector.is_hung("agent-1") is True

    def test_returns_false_when_active(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=10)
        assert detector.is_hung("agent-1") is False

    def test_returns_false_for_unknown_instance(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, _ = _make_detector(config, event_logger, t0)

        assert detector.is_hung("nonexistent") is False

    def test_returns_false_at_exact_timeout(
        self, config: HangDetectorConfig, event_logger: EventLogger
    ) -> None:
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=30)
        assert detector.is_hung("agent-1") is False


# ---------------------------------------------------------------------------
# Disabled detector tests
# ---------------------------------------------------------------------------

class TestDisabledDetector:
    """驗證 enabled=False 時所有檢查回傳空結果。"""

    def test_check_all_returns_empty(self, event_logger: EventLogger) -> None:
        config = HangDetectorConfig(enabled=False, timeout_minutes=30)
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=60)
        alerts = detector.check_all(["agent-1"])
        assert alerts == []

    def test_is_hung_returns_false(self, event_logger: EventLogger) -> None:
        config = HangDetectorConfig(enabled=False, timeout_minutes=30)
        t0 = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        detector, now_holder = _make_detector(config, event_logger, t0)

        detector.update_activity("agent-1")
        now_holder[0] = t0 + timedelta(minutes=60)
        assert detector.is_hung("agent-1") is False
