"""ModelFailover 單元測試。

驗證模型故障轉移的順序、事件記錄與邊界條件。
"""

from __future__ import annotations

import sqlite3

import pytest

from kiro_agent.db import init_db
from kiro_agent.event_logger import EventLogger
from kiro_agent.model_failover import ModelFailover


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
def failover(event_logger: EventLogger) -> ModelFailover:
    return ModelFailover(event_logger=event_logger)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_operation(fail_models: set[str] | None = None):
    """建立一個 async operation，指定哪些模型會失敗。"""
    fail_models = fail_models or set()
    call_order: list[str] = []

    async def operation(model: str):
        call_order.append(model)
        if model in fail_models:
            raise RuntimeError(f"Model {model} unavailable")
        return f"result-from-{model}"

    return operation, call_order


def _make_try_fn(fail_models: set[str] | None = None):
    """建立一個 async try_model_fn，指定哪些模型會失敗（回傳 False）。"""
    fail_models = fail_models or set()
    call_order: list[str] = []

    async def try_fn(model: str) -> bool:
        call_order.append(model)
        return model not in fail_models

    return try_fn, call_order


# ---------------------------------------------------------------------------
# execute_with_failover tests
# ---------------------------------------------------------------------------


class TestExecuteWithFailover:
    """驗證 execute_with_failover 的故障轉移邏輯。"""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_model_no_failover(
        self, failover: ModelFailover, conn: sqlite3.Connection
    ) -> None:
        """第一個模型成功 → 直接回傳結果，不記錄 model_switched。"""
        op, call_order = _make_operation()
        result = await failover.execute_with_failover(
            "agent-1", ["claude-sonnet-4", "claude-haiku-4.5"], op
        )

        assert result == "result-from-claude-sonnet-4"
        assert call_order == ["claude-sonnet-4"]

        # 不應有 model_switched 事件
        events = conn.execute(
            "SELECT * FROM events WHERE data LIKE '%model_switched%'"
        ).fetchall()
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_first_fails_second_succeeds(
        self, failover: ModelFailover, conn: sqlite3.Connection
    ) -> None:
        """第一個失敗、第二個成功 → 回傳第二個結果，記錄 model_switched。"""
        op, call_order = _make_operation(fail_models={"claude-sonnet-4"})
        result = await failover.execute_with_failover(
            "agent-1", ["claude-sonnet-4", "claude-haiku-4.5"], op
        )

        assert result == "result-from-claude-haiku-4.5"
        assert call_order == ["claude-sonnet-4", "claude-haiku-4.5"]

        events = conn.execute(
            "SELECT * FROM events WHERE data LIKE '%model_switched%'"
        ).fetchall()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_all_fail_returns_none(
        self, failover: ModelFailover, conn: sqlite3.Connection
    ) -> None:
        """全部失敗 → 回傳 None，記錄 all_models_failed。"""
        op, call_order = _make_operation(
            fail_models={"claude-sonnet-4", "claude-haiku-4.5"}
        )
        result = await failover.execute_with_failover(
            "agent-1", ["claude-sonnet-4", "claude-haiku-4.5"], op
        )

        assert result is None
        assert call_order == ["claude-sonnet-4", "claude-haiku-4.5"]

        events = conn.execute(
            "SELECT * FROM events WHERE data LIKE '%all_models_failed%'"
        ).fetchall()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_empty_failover_list_returns_none(
        self, failover: ModelFailover, conn: sqlite3.Connection
    ) -> None:
        """空的 failover 清單 → 直接回傳 None。"""
        op, call_order = _make_operation()
        result = await failover.execute_with_failover("agent-1", [], op)

        assert result is None
        assert call_order == []

    @pytest.mark.asyncio
    async def test_order_is_preserved(self, failover: ModelFailover) -> None:
        """驗證嘗試順序與 failover_models 陣列一致。"""
        models = ["model-a", "model-b", "model-c", "model-d"]
        op, call_order = _make_operation(
            fail_models={"model-a", "model-b", "model-c"}
        )
        result = await failover.execute_with_failover("agent-1", models, op)

        assert result == "result-from-model-d"
        assert call_order == ["model-a", "model-b", "model-c", "model-d"]


# ---------------------------------------------------------------------------
# attempt_failover tests
# ---------------------------------------------------------------------------


class TestAttemptFailover:
    """驗證 attempt_failover 的簡化介面。"""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_model(
        self, failover: ModelFailover
    ) -> None:
        """第一個模型成功 → 回傳該模型名稱。"""
        try_fn, call_order = _make_try_fn()
        result = await failover.attempt_failover(
            "agent-1", ["claude-sonnet-4", "claude-haiku-4.5"], try_fn
        )

        assert result == "claude-sonnet-4"
        assert call_order == ["claude-sonnet-4"]

    @pytest.mark.asyncio
    async def test_first_fails_second_succeeds(
        self, failover: ModelFailover, conn: sqlite3.Connection
    ) -> None:
        """第一個失敗、第二個成功 → 回傳第二個模型名稱。"""
        try_fn, call_order = _make_try_fn(fail_models={"claude-sonnet-4"})
        result = await failover.attempt_failover(
            "agent-1", ["claude-sonnet-4", "claude-haiku-4.5"], try_fn
        )

        assert result == "claude-haiku-4.5"
        assert call_order == ["claude-sonnet-4", "claude-haiku-4.5"]

        # 應記錄 model_switched 事件
        events = conn.execute(
            "SELECT * FROM events WHERE data LIKE '%model_switched%'"
        ).fetchall()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_all_fail_returns_none(
        self, failover: ModelFailover, conn: sqlite3.Connection
    ) -> None:
        """全部失敗 → 回傳 None。"""
        try_fn, _ = _make_try_fn(
            fail_models={"claude-sonnet-4", "claude-haiku-4.5"}
        )
        result = await failover.attempt_failover(
            "agent-1", ["claude-sonnet-4", "claude-haiku-4.5"], try_fn
        )

        assert result is None

        events = conn.execute(
            "SELECT * FROM events WHERE data LIKE '%all_models_failed%'"
        ).fetchall()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_empty_failover_list_returns_none(
        self, failover: ModelFailover
    ) -> None:
        """空的 failover 清單 → 直接回傳 None。"""
        try_fn, call_order = _make_try_fn()
        result = await failover.attempt_failover("agent-1", [], try_fn)

        assert result is None
        assert call_order == []

    @pytest.mark.asyncio
    async def test_order_is_preserved(self, failover: ModelFailover) -> None:
        """驗證嘗試順序與 failover_models 陣列一致。"""
        models = ["model-a", "model-b", "model-c"]
        try_fn, call_order = _make_try_fn(fail_models={"model-a", "model-b"})
        result = await failover.attempt_failover("agent-1", models, try_fn)

        assert result == "model-c"
        assert call_order == ["model-a", "model-b", "model-c"]

    @pytest.mark.asyncio
    async def test_exception_in_try_fn_treated_as_failure(
        self, failover: ModelFailover
    ) -> None:
        """try_model_fn 拋出例外時視為失敗，繼續嘗試下一個。"""
        call_order: list[str] = []

        async def try_fn(model: str) -> bool:
            call_order.append(model)
            if model == "model-a":
                raise RuntimeError("unexpected error")
            return True

        result = await failover.attempt_failover(
            "agent-1", ["model-a", "model-b"], try_fn
        )

        assert result == "model-b"
        assert call_order == ["model-a", "model-b"]
