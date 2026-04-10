"""KiroCliAdapter 單元測試。

Mock subprocess 呼叫，不實際執行 tmux。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from kiro_agent.backend_adapter import (
    KiroCliAdapter,
    _escape_for_tmux,
    _run_tmux,
    _tmux_session_name,
)
from kiro_agent.config import InstanceConfig
from kiro_agent.models import BackendError, InstanceState, InstanceStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter() -> KiroCliAdapter:
    return KiroCliAdapter()


@pytest.fixture
def instance() -> InstanceConfig:
    return InstanceConfig(
        name="agent-1",
        project="my-app",
        backend="kiro-cli",
        model="auto",
        description="Test agent",
    )


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    """建立含 .kiro/steering/ 的臨時工作目錄。"""
    steering = tmp_path / ".kiro" / "steering"
    steering.mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# tmux session 命名
# ---------------------------------------------------------------------------


class TestTmuxSessionName:
    def test_prefix(self) -> None:
        assert _tmux_session_name("agent-1") == "ka-agent-1"

    def test_different_names(self) -> None:
        assert _tmux_session_name("dev") == "ka-dev"
        assert _tmux_session_name("lib-worker") == "ka-lib-worker"


# ---------------------------------------------------------------------------
# tmux 跳脫
# ---------------------------------------------------------------------------


class TestEscapeForTmux:
    def test_plain_text_unchanged(self) -> None:
        assert _escape_for_tmux("hello world") == "hello world"

    def test_semicolon_escaped(self) -> None:
        assert _escape_for_tmux("a;b") == "a\\;b"

    def test_double_quote_escaped(self) -> None:
        assert _escape_for_tmux('say "hi"') == 'say \\"hi\\"'

    def test_backslash_escaped(self) -> None:
        assert _escape_for_tmux("a\\b") == "a\\\\b"

    def test_combined_special_chars(self) -> None:
        result = _escape_for_tmux('run "cmd"; exit')
        assert '\\"' in result
        assert "\\;" in result


# ---------------------------------------------------------------------------
# supported_models
# ---------------------------------------------------------------------------


class TestSupportedModels:
    def test_contains_expected_models(self) -> None:
        expected = {"auto", "claude-sonnet-4.5", "claude-sonnet-4", "claude-haiku-4.5"}
        assert set(KiroCliAdapter.supported_models) == expected

    def test_is_list(self) -> None:
        assert isinstance(KiroCliAdapter.supported_models, list)


# ---------------------------------------------------------------------------
# start_session
# ---------------------------------------------------------------------------


class TestStartSession:
    @pytest.mark.asyncio
    async def test_raises_if_steering_dir_missing(
        self, adapter: KiroCliAdapter, instance: InstanceConfig, tmp_path: Path,
    ) -> None:
        """工作目錄缺少 .kiro/steering/ 時應 raise BackendError。"""
        with pytest.raises(BackendError) as exc_info:
            await adapter.start_session(instance, tmp_path)
        assert exc_info.value.error_type == "missing_steering"
        assert ".kiro/steering/" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_if_unsupported_model(
        self, adapter: KiroCliAdapter, work_dir: Path,
    ) -> None:
        """不支援的模型應 raise BackendError。"""
        bad_instance = InstanceConfig(
            name="bad", project="p", model="gpt-4o",
        )
        with pytest.raises(BackendError) as exc_info:
            await adapter.start_session(bad_instance, work_dir)
        assert exc_info.value.error_type == "unsupported_model"

    @pytest.mark.asyncio
    async def test_writes_fleet_context_md(
        self, adapter: KiroCliAdapter, instance: InstanceConfig, work_dir: Path,
    ) -> None:
        """start_session 應寫入 fleet-context.md。"""
        with patch(
            "kiro_agent.backend_adapter._run_tmux",
            new_callable=AsyncMock,
            return_value=(0, "", ""),
        ):
            await adapter.start_session(instance, work_dir)

        ctx_path = work_dir / ".kiro" / "steering" / "fleet-context.md"
        assert ctx_path.exists()
        content = ctx_path.read_text(encoding="utf-8")
        assert instance.name in content
        assert "Fleet Context" in content

    @pytest.mark.asyncio
    async def test_calls_tmux_new_session_and_send_keys(
        self, adapter: KiroCliAdapter, instance: InstanceConfig, work_dir: Path,
    ) -> None:
        """應依序呼叫 tmux new-session 和 send-keys。"""
        calls: list[tuple[str, ...]] = []

        async def mock_run_tmux(*args: str) -> tuple[int, str, str]:
            calls.append(args)
            return (0, "", "")

        with patch("kiro_agent.backend_adapter._run_tmux", side_effect=mock_run_tmux):
            await adapter.start_session(instance, work_dir)

        assert len(calls) == 2
        # 第一次呼叫: new-session
        assert calls[0][0] == "new-session"
        assert "ka-agent-1" in calls[0]
        # 第二次呼叫: send-keys
        assert calls[1][0] == "send-keys"
        assert "kiro-cli --model auto" in calls[1]

    @pytest.mark.asyncio
    async def test_raises_on_tmux_new_session_failure(
        self, adapter: KiroCliAdapter, instance: InstanceConfig, work_dir: Path,
    ) -> None:
        """tmux new-session 失敗時應 raise BackendError。"""
        async def mock_run_tmux(*args: str) -> tuple[int, str, str]:
            if args[0] == "new-session":
                return (1, "", "duplicate session")
            return (0, "", "")

        with patch("kiro_agent.backend_adapter._run_tmux", side_effect=mock_run_tmux):
            with pytest.raises(BackendError) as exc_info:
                await adapter.start_session(instance, work_dir)
            assert exc_info.value.error_type == "tmux_error"


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_sends_escaped_message(self, adapter: KiroCliAdapter) -> None:
        """send_message 應透過 tmux send-keys 傳送跳脫後的訊息。"""
        calls: list[tuple[str, ...]] = []

        async def mock_run_tmux(*args: str) -> tuple[int, str, str]:
            calls.append(args)
            return (0, "", "")

        with patch("kiro_agent.backend_adapter._run_tmux", side_effect=mock_run_tmux):
            await adapter.send_message("agent-1", "hello world")

        assert len(calls) == 1
        assert calls[0][0] == "send-keys"
        assert "ka-agent-1" in calls[0]

    @pytest.mark.asyncio
    async def test_raises_on_send_failure(self, adapter: KiroCliAdapter) -> None:
        with patch(
            "kiro_agent.backend_adapter._run_tmux",
            new_callable=AsyncMock,
            return_value=(1, "", "session not found"),
        ):
            with pytest.raises(BackendError) as exc_info:
                await adapter.send_message("agent-1", "test")
            assert exc_info.value.error_type == "send_failed"


# ---------------------------------------------------------------------------
# stop_session
# ---------------------------------------------------------------------------


class TestStopSession:
    @pytest.mark.asyncio
    async def test_sends_exit_then_kills(self, adapter: KiroCliAdapter) -> None:
        """stop_session 應先送 /exit，再 kill-session。"""
        calls: list[tuple[str, ...]] = []

        async def mock_run_tmux(*args: str) -> tuple[int, str, str]:
            calls.append(args)
            # has-session 回傳 0 表示 session 仍存在
            if args[0] == "has-session":
                return (0, "", "")
            return (0, "", "")

        with patch("kiro_agent.backend_adapter._run_tmux", side_effect=mock_run_tmux):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.stop_session("agent-1")

        cmds = [c[0] for c in calls]
        assert "send-keys" in cmds
        assert "has-session" in cmds
        assert "kill-session" in cmds

    @pytest.mark.asyncio
    async def test_skips_kill_if_already_exited(self, adapter: KiroCliAdapter) -> None:
        """session 已退出時不呼叫 kill-session。"""
        calls: list[tuple[str, ...]] = []

        async def mock_run_tmux(*args: str) -> tuple[int, str, str]:
            calls.append(args)
            # has-session 回傳 1 表示 session 不存在
            if args[0] == "has-session":
                return (1, "", "")
            return (0, "", "")

        with patch("kiro_agent.backend_adapter._run_tmux", side_effect=mock_run_tmux):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.stop_session("agent-1")

        cmds = [c[0] for c in calls]
        assert "kill-session" not in cmds


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    @pytest.mark.asyncio
    async def test_running_when_session_exists(self, adapter: KiroCliAdapter) -> None:
        with patch(
            "kiro_agent.backend_adapter._run_tmux",
            new_callable=AsyncMock,
            return_value=(0, "", ""),
        ):
            state = await adapter.get_status("agent-1")

        assert isinstance(state, InstanceState)
        assert state.status == InstanceStatus.RUNNING
        assert state.name == "agent-1"
        assert state.backend == "kiro-cli"
        assert state.tmux_session == "ka-agent-1"

    @pytest.mark.asyncio
    async def test_stopped_when_session_missing(self, adapter: KiroCliAdapter) -> None:
        with patch(
            "kiro_agent.backend_adapter._run_tmux",
            new_callable=AsyncMock,
            return_value=(1, "", "session not found"),
        ):
            state = await adapter.get_status("agent-1")

        assert state.status == InstanceStatus.STOPPED


# ---------------------------------------------------------------------------
# generate_fleet_context
# ---------------------------------------------------------------------------


class TestGenerateFleetContext:
    def test_contains_instance_identity(self) -> None:
        inst = InstanceConfig(
            name="dev-1", project="app", model="claude-sonnet-4",
            description="Main dev agent",
        )
        content = KiroCliAdapter.generate_fleet_context(inst)
        assert "dev-1" in content
        assert "claude-sonnet-4" in content
        assert "Main dev agent" in content

    def test_contains_peer_info(self) -> None:
        inst = InstanceConfig(name="dev-1", project="app")
        peers = [
            InstanceConfig(name="dev-2", project="lib", description="Library agent"),
            InstanceConfig(name="dev-3", project="docs", description="Docs agent"),
        ]
        content = KiroCliAdapter.generate_fleet_context(inst, peers=peers)
        assert "dev-2" in content
        assert "Library agent" in content
        assert "dev-3" in content
        assert "Docs agent" in content

    def test_no_peers_shows_placeholder(self) -> None:
        inst = InstanceConfig(name="solo", project="app")
        content = KiroCliAdapter.generate_fleet_context(inst)
        assert "no peers" in content

    def test_contains_collaboration_rules(self) -> None:
        inst = InstanceConfig(name="dev-1", project="app")
        content = KiroCliAdapter.generate_fleet_context(inst)
        assert "Collaboration Rules" in content
        assert "MCP tools" in content
        assert "delegate_task" in content

    def test_contains_fleet_context_header(self) -> None:
        inst = InstanceConfig(name="dev-1", project="app")
        content = KiroCliAdapter.generate_fleet_context(inst)
        assert content.startswith("# Fleet Context")
