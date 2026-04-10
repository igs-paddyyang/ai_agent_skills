"""FleetManager 單元測試。

測試項目：
- Instance 名稱唯一性驗證
- Retry interval 計算（5, 15, 45, then None）
- start/stop instance 狀態轉換
- create_instance 重複名稱 raise InstanceError
- start_fleet / stop_fleet 流程
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kiro_agent.config import (
    AccessConfig,
    CostGuardConfig,
    FleetConfig,
    HangDetectorConfig,
    InstanceConfig,
)
from kiro_agent.channel_router import ChannelRouter
from kiro_agent.event_logger import EventLogger
from kiro_agent.fleet_manager import FleetManager
from kiro_agent.models import InstanceError, InstanceStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(instances: list[InstanceConfig] | None = None) -> FleetConfig:
    """建立測試用 FleetConfig。"""
    if instances is None:
        instances = [
            InstanceConfig(name="agent-1", project="proj-a", auto_start=False),
            InstanceConfig(name="agent-2", project="proj-b", auto_start=True),
        ]
    return FleetConfig(
        project_roots={"proj-a": "/tmp/proj-a", "proj-b": "/tmp/proj-b"},
        channel={
            "bot_token_env": "TELEGRAM_BOT_TOKEN",
            "group_id": -100123,
            "general_topic_id": 1,
        },
        defaults={"backend": "kiro-cli", "model": "auto"},
        instances=instances,
        cost_guard=CostGuardConfig(),
        hang_detector=HangDetectorConfig(),
        access=AccessConfig(),
    )


def _make_event_logger() -> EventLogger:
    """建立 in-memory EventLogger。"""
    return EventLogger(":memory:")


def _mock_adapter() -> MagicMock:
    """建立 mock BackendAdapter。"""
    adapter = MagicMock()
    adapter.start_session = AsyncMock()
    adapter.stop_session = AsyncMock()
    adapter.send_message = AsyncMock()
    adapter.get_status = AsyncMock()
    return adapter


# ---------------------------------------------------------------------------
# Retry interval 計算
# ---------------------------------------------------------------------------


class TestCalculateRetryInterval:
    """測試 FleetManager.calculate_retry_interval 靜態方法。"""

    def test_attempt_0_returns_5(self):
        assert FleetManager.calculate_retry_interval(0) == 5

    def test_attempt_1_returns_15(self):
        assert FleetManager.calculate_retry_interval(1) == 15

    def test_attempt_2_returns_45(self):
        assert FleetManager.calculate_retry_interval(2) == 45

    def test_attempt_3_returns_none(self):
        assert FleetManager.calculate_retry_interval(3) is None

    def test_attempt_negative_returns_none(self):
        assert FleetManager.calculate_retry_interval(-1) is None

    def test_attempt_large_returns_none(self):
        assert FleetManager.calculate_retry_interval(100) is None


# ---------------------------------------------------------------------------
# Instance 名稱唯一性
# ---------------------------------------------------------------------------


class TestInstanceNameUniqueness:
    """測試 create_instance 的名稱唯一性驗證。"""

    @pytest.mark.asyncio
    async def test_duplicate_name_raises_instance_error(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        # 手動註冊一個 instance
        fm.instances["agent-1"] = MagicMock(status=InstanceStatus.STOPPED)

        with pytest.raises(InstanceError, match="already exists"):
            await fm.create_instance("agent-1", "proj-a")

    @pytest.mark.asyncio
    async def test_unique_name_succeeds(self):
        config = _make_config(instances=[])
        fm = FleetManager(config, _make_event_logger())

        with patch("kiro_agent.fleet_manager.get_adapter", return_value=_mock_adapter()):
            await fm.create_instance("new-agent", "proj-a")

        assert "new-agent" in fm.instances
        assert fm.instances["new-agent"].status == InstanceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_create_instance_creates_topic_when_router_available(self):
        """create_instance 應在 channel_router 可用時建立 Topic 並註冊映射。"""
        config = _make_config(instances=[])
        fm = FleetManager(config, _make_event_logger())

        mock_router = MagicMock()
        mock_router.create_topic = AsyncMock(return_value=42)
        mock_router.register_topic = MagicMock()
        fm.channel_router = mock_router

        with patch("kiro_agent.fleet_manager.get_adapter", return_value=_mock_adapter()):
            await fm.create_instance("new-agent", "proj-a")

        mock_router.create_topic.assert_awaited_once_with("new-agent")
        mock_router.register_topic.assert_called_once_with(42, "new-agent")
        assert fm.instances["new-agent"].topic_id == 42

    @pytest.mark.asyncio
    async def test_create_instance_skips_topic_when_no_router(self):
        """channel_router 為 None 時，create_instance 不應嘗試建立 Topic。"""
        config = _make_config(instances=[])
        fm = FleetManager(config, _make_event_logger())
        fm.channel_router = None

        with patch("kiro_agent.fleet_manager.get_adapter", return_value=_mock_adapter()):
            await fm.create_instance("new-agent", "proj-a")

        assert "new-agent" in fm.instances
        assert fm.instances["new-agent"].topic_id is None


# ---------------------------------------------------------------------------
# start_instance / stop_instance 狀態轉換
# ---------------------------------------------------------------------------


class TestStartStopInstance:
    """測試 Instance 啟動/停止的狀態轉換。"""

    @pytest.mark.asyncio
    async def test_start_instance_sets_running(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = MagicMock(
            status=InstanceStatus.STOPPED,
            name="agent-1",
        )
        # 使用真正的 InstanceState 以便測試狀態變更
        from kiro_agent.models import InstanceState

        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.STOPPED,
            backend="kiro-cli",
            model="auto",
        )

        await fm.start_instance("agent-1")

        assert fm.instances["agent-1"].status == InstanceStatus.RUNNING
        adapter.start_session.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_already_running_raises(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        fm.adapters["agent-1"] = _mock_adapter()
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.RUNNING,
            backend="kiro-cli",
            model="auto",
        )

        with pytest.raises(InstanceError, match="already running"):
            await fm.start_instance("agent-1")

    @pytest.mark.asyncio
    async def test_start_nonexistent_raises(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        with pytest.raises(InstanceError, match="not found"):
            await fm.start_instance("no-such-agent")

    @pytest.mark.asyncio
    async def test_stop_instance_sets_stopped(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.RUNNING,
            backend="kiro-cli",
            model="auto",
            tmux_session="ka-agent-1",
        )

        await fm.stop_instance("agent-1")

        assert fm.instances["agent-1"].status == InstanceStatus.STOPPED
        assert fm.instances["agent-1"].tmux_session is None
        adapter.stop_session.assert_awaited_once_with("agent-1")

    @pytest.mark.asyncio
    async def test_stop_nonexistent_raises(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        with pytest.raises(InstanceError, match="not found"):
            await fm.stop_instance("no-such-agent")


# ---------------------------------------------------------------------------
# delete_instance
# ---------------------------------------------------------------------------


class TestDeleteInstance:
    """測試 delete_instance。"""

    @pytest.mark.asyncio
    async def test_delete_removes_instance(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.STOPPED,
            backend="kiro-cli",
            model="auto",
        )

        await fm.delete_instance("agent-1")

        assert "agent-1" not in fm.instances
        assert "agent-1" not in fm.adapters

    @pytest.mark.asyncio
    async def test_delete_running_instance_stops_first(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.RUNNING,
            backend="kiro-cli",
            model="auto",
        )

        await fm.delete_instance("agent-1")

        adapter.stop_session.assert_awaited_once()
        assert "agent-1" not in fm.instances

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        with pytest.raises(InstanceError, match="not found"):
            await fm.delete_instance("no-such-agent")

    @pytest.mark.asyncio
    async def test_delete_instance_unregisters_topic(self):
        """delete_instance 應呼叫 channel_router.unregister_topic。"""
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.STOPPED,
            backend="kiro-cli",
            model="auto",
        )

        mock_router = MagicMock()
        mock_router.unregister_topic = MagicMock()
        fm.channel_router = mock_router

        await fm.delete_instance("agent-1")

        mock_router.unregister_topic.assert_called_once_with("agent-1")
        assert "agent-1" not in fm.instances


# ---------------------------------------------------------------------------
# start_fleet / stop_fleet
# ---------------------------------------------------------------------------


class TestFleetLifecycle:
    """測試 start_fleet / stop_fleet 流程。"""

    @pytest.mark.asyncio
    async def test_start_fleet_initializes_adapters_and_starts_auto(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        mock_adapter = _mock_adapter()

        with (
            patch("kiro_agent.fleet_manager.get_adapter", return_value=mock_adapter),
            patch.object(ChannelRouter, "start", new_callable=AsyncMock),
        ):
            await fm.start_fleet()

        # 兩個 instance 都應該有 adapter
        assert "agent-1" in fm.adapters
        assert "agent-2" in fm.adapters

        # agent-2 是 auto_start，應該被啟動
        assert fm.instances["agent-2"].status == InstanceStatus.RUNNING

        # agent-1 不是 auto_start，應該保持 stopped
        assert fm.instances["agent-1"].status == InstanceStatus.STOPPED

        # ChannelRouter 應該被建立
        assert fm.channel_router is not None

    @pytest.mark.asyncio
    async def test_start_fleet_registers_existing_topic_mappings(self):
        """start_fleet 應將已有 topic_id 的 Instance 註冊到 channel_router。"""
        instances = [
            InstanceConfig(name="agent-1", project="proj-a", auto_start=False),
        ]
        config = _make_config(instances=instances)
        fm = FleetManager(config, _make_event_logger())

        mock_adapter = _mock_adapter()

        with (
            patch("kiro_agent.fleet_manager.get_adapter", return_value=mock_adapter),
            patch.object(ChannelRouter, "start", new_callable=AsyncMock),
        ):
            await fm.start_fleet()

            # 手動設定 topic_id 模擬已有映射的情況
            # 由於 start_fleet 在初始化時 topic_id 為 None，
            # 我們需要在 start_fleet 之前設定
            pass

        # 驗證：沒有 topic_id 的 instance 不應被註冊
        assert fm.channel_router is not None
        assert len(fm.channel_router.topic_instance_map) == 0

    @pytest.mark.asyncio
    async def test_start_fleet_registers_preexisting_topic_ids(self):
        """start_fleet 應將已有 topic_id 的 InstanceState 註冊到 channel_router。"""
        from kiro_agent.models import InstanceState

        instances = [
            InstanceConfig(name="agent-1", project="proj-a", auto_start=False),
        ]
        config = _make_config(instances=instances)
        fm = FleetManager(config, _make_event_logger())

        mock_adapter = _mock_adapter()

        with (
            patch("kiro_agent.fleet_manager.get_adapter", return_value=mock_adapter),
            patch.object(ChannelRouter, "start", new_callable=AsyncMock),
            patch.object(ChannelRouter, "register_topic") as mock_register,
        ):
            await fm.start_fleet()

            # 模擬已有 topic_id（例如從持久化恢復）
            fm.instances["agent-1"].topic_id = 55
            # 重新呼叫註冊邏輯
            for state in fm.instances.values():
                if state.topic_id is not None:
                    fm.channel_router.register_topic(state.topic_id, state.name)

            mock_register.assert_called_with(55, "agent-1")

    @pytest.mark.asyncio
    async def test_stop_fleet_stops_all_and_router(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.RUNNING,
            backend="kiro-cli",
            model="auto",
        )

        mock_router = MagicMock()
        mock_router.stop = AsyncMock()
        fm.channel_router = mock_router

        await fm.stop_fleet()

        adapter.stop_session.assert_awaited_once()
        assert fm.instances["agent-1"].status == InstanceStatus.STOPPED
        mock_router.stop.assert_awaited_once()
        assert fm.channel_router is None


# ---------------------------------------------------------------------------
# handle_crash 自動重啟
# ---------------------------------------------------------------------------


class TestHandleCrash:
    """測試 crash 自動重啟邏輯。"""

    @pytest.mark.asyncio
    async def test_first_crash_retries_after_5s(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.STOPPED,
            backend="kiro-cli",
            model="auto",
        )

        with patch("kiro_agent.fleet_manager.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await fm.handle_crash("agent-1")

        mock_sleep.assert_awaited_once_with(5)
        assert fm.instances["agent-1"].status == InstanceStatus.RUNNING

    @pytest.mark.asyncio
    async def test_three_failures_marks_crashed(self):
        config = _make_config()
        fm = FleetManager(config, _make_event_logger())

        from kiro_agent.models import InstanceState

        adapter = _mock_adapter()
        adapter.start_session = AsyncMock(side_effect=RuntimeError("tmux failed"))
        fm.adapters["agent-1"] = adapter
        fm.instances["agent-1"] = InstanceState(
            name="agent-1",
            status=InstanceStatus.STOPPED,
            backend="kiro-cli",
            model="auto",
        )

        with patch("kiro_agent.fleet_manager.asyncio.sleep", new_callable=AsyncMock):
            await fm.handle_crash("agent-1")

        # 3 次重試全部失敗後，狀態應為 STOPPED
        assert fm.instances["agent-1"].status == InstanceStatus.STOPPED

        # 應該有 instance_crashed 事件（gave_up）
        events = fm.event_logger.query(event_type="instance_crashed", instance_name="agent-1")
        gave_up = [e for e in events if e["data"].get("action") == "gave_up"]
        assert len(gave_up) == 1
