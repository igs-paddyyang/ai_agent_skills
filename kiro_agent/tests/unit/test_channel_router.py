"""ChannelRouter 單元測試。

測試存取控制邏輯、訊息路由、事件日誌記錄。
Telegram API 以 mock 替代。
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from kiro_agent.channel_router import ChannelRouter
from kiro_agent.config import FleetConfig, InstanceConfig, AccessConfig
from kiro_agent.event_logger import EventLogger


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(
    allowed_users: list[int] | None = None,
    mode: str = "locked",
    general_topic_id: int = 1,
) -> FleetConfig:
    """建立測試用 FleetConfig。"""
    return FleetConfig(
        project_roots={"test": "/tmp/test"},
        channel={
            "bot_token_env": "TEST_BOT_TOKEN",
            "group_id": -100123,
            "general_topic_id": general_topic_id,
        },
        defaults={"backend": "kiro-cli", "model": "auto"},
        instances=[
            InstanceConfig(name="agent-1", project="test"),
        ],
        access=AccessConfig(
            mode=mode,
            allowed_users=[111, 222] if allowed_users is None else allowed_users,
        ),
    )


def _make_update(user_id: int, text: str = "hello", topic_id: int | None = None):
    """建立 mock Telegram Update。"""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id

    message = MagicMock()
    message.text = text
    message.message_thread_id = topic_id
    update.effective_message = message

    return update


@pytest.fixture
def event_logger():
    """In-memory EventLogger。"""
    return EventLogger(":memory:")


@pytest.fixture
def fleet_manager():
    """Mock FleetManager。"""
    fm = MagicMock()
    fm.send_message_to_instance = AsyncMock()
    return fm


# ---------------------------------------------------------------------------
# 存取控制測試
# ---------------------------------------------------------------------------


class TestAccessControl:
    """存取控制邏輯測試。"""

    def test_allowed_user_in_locked_mode(self, event_logger, fleet_manager):
        """locked 模式下，白名單使用者應被允許。"""
        config = _make_config(allowed_users=[111, 222], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        assert router.is_user_allowed(111) is True
        assert router.is_user_allowed(222) is True

    def test_denied_user_in_locked_mode(self, event_logger, fleet_manager):
        """locked 模式下，非白名單使用者應被拒絕。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        assert router.is_user_allowed(999) is False

    def test_open_mode_allows_all(self, event_logger, fleet_manager):
        """open 模式下，所有使用者應被允許。"""
        config = _make_config(allowed_users=[111], mode="open")
        router = ChannelRouter(fleet_manager, config, event_logger)

        assert router.is_user_allowed(999) is True
        assert router.is_user_allowed(111) is True

    def test_empty_allowed_users_denies_all_in_locked(self, event_logger, fleet_manager):
        """locked 模式下，空白名單應拒絕所有使用者。"""
        config = _make_config(allowed_users=[], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        assert router.is_user_allowed(111) is False


# ---------------------------------------------------------------------------
# on_message 存取控制整合測試
# ---------------------------------------------------------------------------


class TestOnMessageAccessControl:
    """on_message 中的存取控制行為測試。"""

    @pytest.mark.asyncio
    async def test_denied_user_logs_access_denied_event(self, event_logger, fleet_manager):
        """未授權使用者的訊息應記錄 access_denied 事件。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_update(user_id=999, text="hack")
        await router.on_message(update, MagicMock())

        events = event_logger.query(event_type="access_denied")
        assert len(events) == 1
        assert events[0]["data"]["user_id"] == 999

    @pytest.mark.asyncio
    async def test_denied_user_message_not_routed(self, event_logger, fleet_manager):
        """未授權使用者的訊息不應被路由到任何 Instance。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)
        router.topic_instance_map = {10: "agent-1"}

        update = _make_update(user_id=999, text="hello", topic_id=10)
        await router.on_message(update, MagicMock())

        fleet_manager.send_message_to_instance.assert_not_called()

    @pytest.mark.asyncio
    async def test_allowed_user_message_is_routed(self, event_logger, fleet_manager):
        """授權使用者的訊息應被路由到對應 Instance。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)
        router.topic_instance_map = {10: "agent-1"}

        update = _make_update(user_id=111, text="do something", topic_id=10)
        await router.on_message(update, MagicMock())

        fleet_manager.send_message_to_instance.assert_awaited_once_with(
            "agent-1", "do something"
        )

    @pytest.mark.asyncio
    async def test_no_access_denied_event_for_allowed_user(self, event_logger, fleet_manager):
        """授權使用者不應產生 access_denied 事件。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_update(user_id=111, text="hello", topic_id=None)
        await router.on_message(update, MagicMock())

        events = event_logger.query(event_type="access_denied")
        assert len(events) == 0


# ---------------------------------------------------------------------------
# Topic 路由測試
# ---------------------------------------------------------------------------


class TestTopicRouting:
    """Topic → Instance 路由測試。"""

    @pytest.mark.asyncio
    async def test_mapped_topic_routes_to_instance(self, event_logger, fleet_manager):
        """已映射的 topic_id 應路由到正確的 Instance。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)
        router.topic_instance_map = {10: "agent-1", 20: "agent-2"}

        update = _make_update(user_id=111, text="build it", topic_id=20)
        await router.on_message(update, MagicMock())

        fleet_manager.send_message_to_instance.assert_awaited_once_with(
            "agent-2", "build it"
        )

    @pytest.mark.asyncio
    async def test_unmapped_topic_not_routed(self, event_logger, fleet_manager):
        """未映射的 topic_id 不應路由到任何 Instance。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)
        router.topic_instance_map = {10: "agent-1"}

        update = _make_update(user_id=111, text="hello", topic_id=99)
        await router.on_message(update, MagicMock())

        fleet_manager.send_message_to_instance.assert_not_called()

    @pytest.mark.asyncio
    async def test_general_topic_not_routed_to_instance(self, event_logger, fleet_manager):
        """General Topic 的訊息不應直接路由到 Instance。"""
        config = _make_config(allowed_users=[111], general_topic_id=1)
        router = ChannelRouter(fleet_manager, config, event_logger)
        router.topic_instance_map = {1: "agent-1"}  # 即使有映射也不應路由

        update = _make_update(user_id=111, text="hello", topic_id=1)
        await router.on_message(update, MagicMock())

        fleet_manager.send_message_to_instance.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_message_does_nothing(self, event_logger, fleet_manager):
        """effective_message 為 None 時應直接返回。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = MagicMock()
        update.effective_message = None
        await router.on_message(update, MagicMock())

        fleet_manager.send_message_to_instance.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_user_treated_as_unauthorized(self, event_logger, fleet_manager):
        """effective_user 為 None 時，user_id=0 應被視為未授權。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = MagicMock()
        update.effective_message = MagicMock()
        update.effective_user = None
        await router.on_message(update, MagicMock())

        events = event_logger.query(event_type="access_denied")
        assert len(events) == 1
        assert events[0]["data"]["user_id"] == 0


# ---------------------------------------------------------------------------
# Topic-Instance 映射管理測試
# ---------------------------------------------------------------------------


class TestTopicInstanceMap:
    """register_topic / unregister_topic / get_instance_for_topic 測試。"""

    def test_register_topic_adds_to_map(self, event_logger, fleet_manager):
        """register_topic 應將 topic_id 加入映射。"""
        config = _make_config()
        router = ChannelRouter(fleet_manager, config, event_logger)

        router.register_topic(10, "agent-1")

        assert router.topic_instance_map == {10: "agent-1"}

    def test_register_multiple_topics(self, event_logger, fleet_manager):
        """可以註冊多個不同的 topic 映射。"""
        config = _make_config()
        router = ChannelRouter(fleet_manager, config, event_logger)

        router.register_topic(10, "agent-1")
        router.register_topic(20, "agent-2")

        assert router.topic_instance_map == {10: "agent-1", 20: "agent-2"}

    def test_unregister_topic_removes_by_instance_name(self, event_logger, fleet_manager):
        """unregister_topic 應根據 instance_name 移除映射。"""
        config = _make_config()
        router = ChannelRouter(fleet_manager, config, event_logger)

        router.register_topic(10, "agent-1")
        router.register_topic(20, "agent-2")
        router.unregister_topic("agent-1")

        assert router.topic_instance_map == {20: "agent-2"}

    def test_unregister_nonexistent_instance_is_noop(self, event_logger, fleet_manager):
        """unregister 不存在的 instance 不應拋出例外。"""
        config = _make_config()
        router = ChannelRouter(fleet_manager, config, event_logger)

        router.register_topic(10, "agent-1")
        router.unregister_topic("no-such-agent")

        assert router.topic_instance_map == {10: "agent-1"}

    def test_get_instance_for_topic_returns_name(self, event_logger, fleet_manager):
        """get_instance_for_topic 應回傳對應的 instance_name。"""
        config = _make_config()
        router = ChannelRouter(fleet_manager, config, event_logger)

        router.register_topic(10, "agent-1")

        assert router.get_instance_for_topic(10) == "agent-1"

    def test_get_instance_for_topic_returns_none_for_unmapped(self, event_logger, fleet_manager):
        """get_instance_for_topic 對未映射的 topic_id 應回傳 None。"""
        config = _make_config()
        router = ChannelRouter(fleet_manager, config, event_logger)

        assert router.get_instance_for_topic(99) is None


# ---------------------------------------------------------------------------
# Callback Query 輔助
# ---------------------------------------------------------------------------


def _make_callback_update(
    user_id: int,
    callback_data: str,
):
    """建立 mock Telegram CallbackQuery Update。"""
    update = MagicMock()

    query = AsyncMock()
    query.data = callback_data
    query.from_user = MagicMock()
    query.from_user.id = user_id
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()

    update.callback_query = query
    return update


# ---------------------------------------------------------------------------
# on_callback_query 測試
# ---------------------------------------------------------------------------


class TestOnCallbackQuery:
    """on_callback_query 回調處理測試。"""

    @pytest.mark.asyncio
    async def test_tool_allow_calls_fleet_manager(self, event_logger, fleet_manager):
        """tool_allow 應呼叫 fleet_manager.send_tool_decision 並回覆確認。"""
        fleet_manager.send_tool_decision = AsyncMock()
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="tool_allow:agent-1")
        await router.on_callback_query(update, MagicMock())

        fleet_manager.send_tool_decision.assert_awaited_once_with("agent-1", "allow")
        update.callback_query.answer.assert_awaited_once()
        update.callback_query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_tool_deny_calls_fleet_manager(self, event_logger, fleet_manager):
        """tool_deny 應呼叫 fleet_manager.send_tool_decision(deny)。"""
        fleet_manager.send_tool_decision = AsyncMock()
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="tool_deny:agent-1")
        await router.on_callback_query(update, MagicMock())

        fleet_manager.send_tool_decision.assert_awaited_once_with("agent-1", "deny")

    @pytest.mark.asyncio
    async def test_hang_restart_calls_fleet_manager(self, event_logger, fleet_manager):
        """hang_restart 應呼叫 fleet_manager.restart_instance。"""
        fleet_manager.restart_instance = AsyncMock()
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="hang_restart:agent-1")
        await router.on_callback_query(update, MagicMock())

        fleet_manager.restart_instance.assert_awaited_once_with("agent-1")

    @pytest.mark.asyncio
    async def test_hang_stop_calls_fleet_manager(self, event_logger, fleet_manager):
        """hang_stop 應呼叫 fleet_manager.stop_instance。"""
        fleet_manager.stop_instance = AsyncMock()
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="hang_stop:agent-1")
        await router.on_callback_query(update, MagicMock())

        fleet_manager.stop_instance.assert_awaited_once_with("agent-1")

    @pytest.mark.asyncio
    async def test_hang_wait_does_not_restart_or_stop(self, event_logger, fleet_manager):
        """hang_wait 不應呼叫 restart 或 stop，僅回覆確認。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="hang_wait:agent-1")
        await router.on_callback_query(update, MagicMock())

        update.callback_query.answer.assert_awaited_once()
        update.callback_query.edit_message_text.assert_awaited_once()
        # 不應呼叫 restart 或 stop
        assert not hasattr(fleet_manager, "restart_instance") or \
            not fleet_manager.restart_instance.called

    @pytest.mark.asyncio
    async def test_unauthorized_user_denied(self, event_logger, fleet_manager):
        """未授權使用者的回調應被拒絕並記錄事件。"""
        config = _make_config(allowed_users=[111], mode="locked")
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=999, callback_data="tool_allow:agent-1")
        await router.on_callback_query(update, MagicMock())

        update.callback_query.answer.assert_awaited_once_with("⛔ 未授權操作")
        events = event_logger.query(event_type="access_denied")
        assert len(events) == 1
        assert events[0]["data"]["user_id"] == 999

    @pytest.mark.asyncio
    async def test_invalid_callback_data_no_colon(self, event_logger, fleet_manager):
        """缺少冒號的 callback_data 應回覆錯誤。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="invalid_data")
        await router.on_callback_query(update, MagicMock())

        update.callback_query.answer.assert_awaited_once_with("❌ 無效的回調資料")

    @pytest.mark.asyncio
    async def test_unknown_action_answered(self, event_logger, fleet_manager):
        """未知的 action 應回覆錯誤。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="unknown_action:agent-1")
        await router.on_callback_query(update, MagicMock())

        update.callback_query.answer.assert_awaited_once_with("❌ 未知的動作")

    @pytest.mark.asyncio
    async def test_null_callback_query_returns_early(self, event_logger, fleet_manager):
        """callback_query 為 None 時應直接返回。"""
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = MagicMock()
        update.callback_query = None
        await router.on_callback_query(update, MagicMock())
        # 不應拋出例外

    @pytest.mark.asyncio
    async def test_tool_decision_logs_event(self, event_logger, fleet_manager):
        """tool_allow 應記錄 tool_decision 事件。"""
        fleet_manager.send_tool_decision = AsyncMock()
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="tool_allow:agent-1")
        await router.on_callback_query(update, MagicMock())

        events = event_logger.query(event_type="tool_decision")
        assert len(events) == 1
        assert events[0]["data"]["decision"] == "allow"
        assert events[0]["instance_name"] == "agent-1"

    @pytest.mark.asyncio
    async def test_hang_action_logs_event(self, event_logger, fleet_manager):
        """hang_restart 應記錄 hang_action 事件。"""
        fleet_manager.restart_instance = AsyncMock()
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fleet_manager, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="hang_restart:agent-1")
        await router.on_callback_query(update, MagicMock())

        events = event_logger.query(event_type="hang_action")
        assert len(events) == 1
        assert events[0]["data"]["action"] == "restart"
        assert events[0]["instance_name"] == "agent-1"

    @pytest.mark.asyncio
    async def test_fleet_manager_without_method_does_not_crash(self, event_logger):
        """fleet_manager 缺少方法時不應崩潰（hasattr 保護）。"""
        fm = MagicMock(spec=[])  # 空 spec，無任何方法
        config = _make_config(allowed_users=[111])
        router = ChannelRouter(fm, config, event_logger)

        update = _make_callback_update(user_id=111, callback_data="tool_allow:agent-1")
        await router.on_callback_query(update, MagicMock())

        # 應正常完成，不拋出 AttributeError
        update.callback_query.answer.assert_awaited_once()
