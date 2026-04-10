"""ContextGuardian 單元測試。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from kiro_agent.context_guardian import ContextGuardian
from kiro_agent.db import init_db
from kiro_agent.event_logger import EventLogger
from kiro_agent.models import RotationSnapshot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def conn() -> sqlite3.Connection:
    return init_db(":memory:")


@pytest.fixture()
def event_logger(conn: sqlite3.Connection) -> EventLogger:
    return EventLogger(conn=conn)


@pytest.fixture()
def fixed_now() -> datetime:
    return datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_guardian(
    tmp_path: Path,
    event_logger: EventLogger,
    threshold: float = 80.0,
    *,
    now_fn: callable | None = None,
) -> ContextGuardian:
    return ContextGuardian(
        runtime_dir=tmp_path,
        event_logger=event_logger,
        threshold=threshold,
        now_fn=now_fn,
    )


def _write_statusline(tmp_path: Path, instance_name: str, data: dict) -> None:
    """Helper: 寫入 statusline.json。"""
    instance_dir = tmp_path / "instances" / instance_name
    instance_dir.mkdir(parents=True, exist_ok=True)
    (instance_dir / "statusline.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Tests: _read_statusline
# ---------------------------------------------------------------------------


class TestReadStatusline:
    def test_returns_dict_when_file_exists(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "agent-1", {"context_usage_pct": 50.0})
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian._read_statusline("agent-1")

        assert result == {"context_usage_pct": 50.0}

    def test_returns_none_when_file_missing(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian._read_statusline("nonexistent")

        assert result is None

    def test_returns_none_for_invalid_json(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        instance_dir = tmp_path / "instances" / "bad-json"
        instance_dir.mkdir(parents=True, exist_ok=True)
        (instance_dir / "statusline.json").write_text("not json", encoding="utf-8")
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian._read_statusline("bad-json")

        assert result is None

    def test_returns_none_for_non_dict_json(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        instance_dir = tmp_path / "instances" / "array-json"
        instance_dir.mkdir(parents=True, exist_ok=True)
        (instance_dir / "statusline.json").write_text("[1, 2]", encoding="utf-8")
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian._read_statusline("array-json")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: get_context_usage
# ---------------------------------------------------------------------------


class TestGetContextUsage:
    def test_extracts_percentage(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "agent-1", {"context_usage_pct": 75.5})
        guardian = _make_guardian(tmp_path, event_logger)

        assert guardian.get_context_usage("agent-1") == 75.5

    def test_returns_none_when_no_file(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        guardian = _make_guardian(tmp_path, event_logger)

        assert guardian.get_context_usage("missing") is None

    def test_returns_none_when_key_missing(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "agent-1", {"other_field": 42})
        guardian = _make_guardian(tmp_path, event_logger)

        assert guardian.get_context_usage("agent-1") is None

    def test_returns_none_for_non_numeric_value(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "agent-1", {"context_usage_pct": "not_a_number"})
        guardian = _make_guardian(tmp_path, event_logger)

        assert guardian.get_context_usage("agent-1") is None


# ---------------------------------------------------------------------------
# Tests: check_all
# ---------------------------------------------------------------------------


class TestCheckAll:
    def test_returns_instances_above_threshold(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "high", {"context_usage_pct": 85.0})
        _write_statusline(tmp_path, "low", {"context_usage_pct": 50.0})
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian.check_all(["high", "low"])

        assert result == ["high"]

    def test_skips_instances_without_statusline(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "has-file", {"context_usage_pct": 90.0})
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian.check_all(["has-file", "no-file"])

        assert result == ["has-file"]

    def test_exact_threshold_not_exceeded(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "exact", {"context_usage_pct": 80.0})
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian.check_all(["exact"])

        assert result == []

    def test_returns_empty_when_all_below(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "a", {"context_usage_pct": 30.0})
        _write_statusline(tmp_path, "b", {"context_usage_pct": 79.9})
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian.check_all(["a", "b"])

        assert result == []

    def test_custom_threshold(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        _write_statusline(tmp_path, "agent-1", {"context_usage_pct": 55.0})
        guardian = _make_guardian(tmp_path, event_logger, threshold=50.0)

        result = guardian.check_all(["agent-1"])

        assert result == ["agent-1"]

    def test_empty_instance_list(
        self, tmp_path: Path, event_logger: EventLogger
    ) -> None:
        guardian = _make_guardian(tmp_path, event_logger)

        result = guardian.check_all([])

        assert result == []


# ---------------------------------------------------------------------------
# Tests: rotate
# ---------------------------------------------------------------------------


class TestRotate:
    def test_creates_rotation_snapshot(
        self, tmp_path: Path, event_logger: EventLogger, fixed_now: datetime
    ) -> None:
        guardian = _make_guardian(
            tmp_path, event_logger, now_fn=lambda: fixed_now
        )

        snapshot = guardian.rotate("agent-1")

        assert isinstance(snapshot, RotationSnapshot)
        assert snapshot.instance_name == "agent-1"
        assert snapshot.timestamp == fixed_now
        assert "agent-1" in snapshot.summary

    def test_saves_snapshot_file(
        self, tmp_path: Path, event_logger: EventLogger, fixed_now: datetime
    ) -> None:
        guardian = _make_guardian(
            tmp_path, event_logger, now_fn=lambda: fixed_now
        )

        guardian.rotate("agent-1")

        snapshot_path = tmp_path / "instances" / "agent-1" / "rotation_snapshot.md"
        assert snapshot_path.exists()
        content = snapshot_path.read_text(encoding="utf-8")
        assert "agent-1" in content
        assert fixed_now.isoformat() in content

    def test_logs_context_rotated_event(
        self, tmp_path: Path, event_logger: EventLogger, fixed_now: datetime
    ) -> None:
        guardian = _make_guardian(
            tmp_path, event_logger, now_fn=lambda: fixed_now
        )

        guardian.rotate("agent-1")

        events = event_logger.query(event_type="context_rotated")
        assert len(events) == 1
        assert events[0]["instance_name"] == "agent-1"
        assert events[0]["data"]["timestamp"] == fixed_now.isoformat()
