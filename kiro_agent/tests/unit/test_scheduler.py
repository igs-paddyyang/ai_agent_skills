"""Scheduler 單元測試 — 使用 :memory: SQLite。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from kiro_agent.scheduler import Scheduler, TriggeredSchedule


@pytest_asyncio.fixture
async def scheduler() -> Scheduler:
    """建立使用 :memory: DB 的 Scheduler。"""
    return Scheduler(db_path=":memory:")


@pytest.mark.asyncio
async def test_create_schedule_returns_id(scheduler: Scheduler) -> None:
    """create_schedule 插入排程並回傳正整數 id。"""
    sid = await scheduler.create_schedule("*/5 * * * *", "hello", "agent-1")
    assert isinstance(sid, int)
    assert sid > 0


@pytest.mark.asyncio
async def test_create_schedule_invalid_cron_raises(scheduler: Scheduler) -> None:
    """create_schedule 傳入無效 cron 表達式時 raise ValueError。"""
    with pytest.raises(ValueError, match="Invalid cron expression"):
        await scheduler.create_schedule("not-a-cron", "msg", "agent-1")


@pytest.mark.asyncio
async def test_delete_schedule_removes_entry(scheduler: Scheduler) -> None:
    """delete_schedule 成功刪除已存在的排程。"""
    sid = await scheduler.create_schedule("0 9 * * *", "morning", "agent-1")
    assert await scheduler.delete_schedule(sid) is True
    entries = await scheduler.list_schedules()
    assert len(entries) == 0


@pytest.mark.asyncio
async def test_delete_schedule_nonexistent_returns_false(
    scheduler: Scheduler,
) -> None:
    """delete_schedule 刪除不存在的 id 回傳 False。"""
    assert await scheduler.delete_schedule(9999) is False


@pytest.mark.asyncio
async def test_list_schedules_returns_all(scheduler: Scheduler) -> None:
    """list_schedules 回傳所有排程。"""
    await scheduler.create_schedule("0 * * * *", "hourly", "a1")
    await scheduler.create_schedule("30 8 * * 1", "weekly", "a2")
    entries = await scheduler.list_schedules()
    assert len(entries) == 2
    assert entries[0].cron_expr == "0 * * * *"
    assert entries[1].target_instance == "a2"


@pytest.mark.asyncio
async def test_toggle_schedule_flips_enabled(scheduler: Scheduler) -> None:
    """toggle_schedule 切換 enabled 狀態。"""
    sid = await scheduler.create_schedule("0 0 * * *", "daily", "agent-1")

    # 預設 enabled=True，toggle 後應為 False
    new_state = await scheduler.toggle_schedule(sid)
    assert new_state is False

    entries = await scheduler.list_schedules()
    assert entries[0].enabled is False

    # 再 toggle 回 True
    new_state = await scheduler.toggle_schedule(sid)
    assert new_state is True


@pytest.mark.asyncio
async def test_toggle_schedule_nonexistent_raises(scheduler: Scheduler) -> None:
    """toggle_schedule 對不存在的 id raise ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        await scheduler.toggle_schedule(9999)


@pytest.mark.asyncio
async def test_tick_triggers_matching_schedule(scheduler: Scheduler) -> None:
    """tick 觸發匹配當前時間的排程。"""
    # 建立一個每分鐘觸發的排程
    await scheduler.create_schedule("* * * * *", "every-min", "agent-1")

    now = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    triggered = await scheduler.tick(now=now)

    assert len(triggered) == 1
    assert triggered[0].message == "every-min"
    assert triggered[0].target_instance == "agent-1"


@pytest.mark.asyncio
async def test_tick_does_not_retrigger_same_minute(
    scheduler: Scheduler,
) -> None:
    """tick 不會在同一分鐘內重複觸發。"""
    await scheduler.create_schedule("* * * * *", "every-min", "agent-1")

    now = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    # 第一次 tick — 應觸發
    triggered1 = await scheduler.tick(now=now)
    assert len(triggered1) == 1

    # 同一分鐘再次 tick — 不應觸發
    now2 = datetime(2025, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
    triggered2 = await scheduler.tick(now=now2)
    assert len(triggered2) == 0


@pytest.mark.asyncio
async def test_tick_skips_disabled_schedule(scheduler: Scheduler) -> None:
    """tick 跳過已停用的排程。"""
    sid = await scheduler.create_schedule("* * * * *", "every-min", "agent-1")
    await scheduler.toggle_schedule(sid)  # disable

    now = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    triggered = await scheduler.tick(now=now)
    assert len(triggered) == 0


@pytest.mark.asyncio
async def test_tick_non_matching_cron_not_triggered(
    scheduler: Scheduler,
) -> None:
    """tick 不觸發不匹配當前時間的排程。"""
    # 只在每天 9:00 觸發
    await scheduler.create_schedule("0 9 * * *", "morning", "agent-1")

    # 現在是 10:30 — 不應觸發
    now = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    triggered = await scheduler.tick(now=now)
    assert len(triggered) == 0


@pytest.mark.asyncio
async def test_tick_triggers_next_minute(scheduler: Scheduler) -> None:
    """tick 在下一分鐘可以再次觸發。"""
    await scheduler.create_schedule("* * * * *", "every-min", "agent-1")

    t1 = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    await scheduler.tick(now=t1)

    t2 = datetime(2025, 1, 15, 10, 31, 0, tzinfo=timezone.utc)
    triggered = await scheduler.tick(now=t2)
    assert len(triggered) == 1
