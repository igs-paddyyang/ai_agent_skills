"""MCP Bridge 單元測試。

測試項目：
- init_bridge 注入 FleetManager
- list_instances 回傳所有 Instance 資訊
- send_to_instance 傳送訊息 / 目標不存在時回傳錯誤
- request_information 加上 prefix 傳送
- delegate_task 自動喚醒停止的 Instance
- report_result 回傳結果給委派者
- create_team 建立 Team / 重複名稱 / 成員不存在
- broadcast 廣播到 Team 所有成員
- _require_fleet_manager 未初始化時 raise RuntimeError
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from kiro_agent.config import (
    AccessConfig,
    CostGuardConfig,
    FleetConfig,
    HangDetectorConfig,
    InstanceConfig,
    TeamConfig,
)
from kiro_agent.models import InstanceState, InstanceStatus

import kiro_agent.mcp_bridge as bridge


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(
    instances: list[InstanceConfig] | None = None,
    teams: list[TeamConfig] | None = None,
) -> FleetConfig:
    if instances is None:
        instances = [
            InstanceConfig(
                name="agent-1", project="proj-a",
                description="主開發 Agent", backend="kiro-cli",
            ),
            InstanceConfig(
                name="agent-2", project="proj-b",
                description="函式庫 Agent", backend="claude-code",
            ),
        ]
    return FleetConfig(
        project_roots={"proj-a": "/tmp/a", "proj-b": "/tmp/b"},
        channel={"bot_token_env": "TOK", "group_id": -100, "general_topic_id": 1},
        defaults={"backend": "kiro-cli", "model": "auto"},
        instances=instances,
        teams=teams or [],
        cost_guard=CostGuardConfig(),
        hang_detector=HangDetectorConfig(),
        access=AccessConfig(),
    )



def _make_fleet_manager(
    config: FleetConfig | None = None,
    instances: dict[str, InstanceState] | None = None,
) -> MagicMock:
    """建立 mock FleetManager。"""
    fm = MagicMock()
    fm.config = config or _make_config()
    fm.instances = instances or {
        "agent-1": InstanceState(
            name="agent-1", status=InstanceStatus.RUNNING,
            backend="kiro-cli", model="auto",
        ),
        "agent-2": InstanceState(
            name="agent-2", status=InstanceStatus.STOPPED,
            backend="claude-code", model="auto",
        ),
    }
    fm.send_message_to_instance = AsyncMock()
    fm.start_instance = AsyncMock()
    return fm


@pytest.fixture(autouse=True)
def _reset_bridge():
    """每個測試前後重置 module-level _fleet_manager。"""
    bridge._fleet_manager = None
    yield
    bridge._fleet_manager = None


# ---------------------------------------------------------------------------
# init_bridge
# ---------------------------------------------------------------------------


class TestInitBridge:
    def test_init_bridge_sets_fleet_manager(self):
        fm = _make_fleet_manager()
        result = bridge.init_bridge(fm)
        assert bridge._fleet_manager is fm
        assert result is bridge.mcp

    def test_require_fleet_manager_raises_when_not_initialized(self):
        with pytest.raises(RuntimeError, match="尚未初始化"):
            bridge._require_fleet_manager()

    def test_require_fleet_manager_returns_fm_after_init(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)
        assert bridge._require_fleet_manager() is fm


# ---------------------------------------------------------------------------
# list_instances
# ---------------------------------------------------------------------------


class TestListInstances:
    async def test_returns_all_instances(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.list_instances()
        data = json.loads(raw)

        assert len(data) == 2
        names = {d["name"] for d in data}
        assert names == {"agent-1", "agent-2"}

    async def test_includes_status_description_backend(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.list_instances()
        data = json.loads(raw)

        a1 = next(d for d in data if d["name"] == "agent-1")
        assert a1["status"] == "running"
        assert a1["description"] == "主開發 Agent"
        assert a1["backend"] == "kiro-cli"

    async def test_unknown_status_when_state_missing(self):
        fm = _make_fleet_manager()
        # 移除 agent-2 的 state 但保留 config
        del fm.instances["agent-2"]
        bridge.init_bridge(fm)

        raw = await bridge.list_instances()
        data = json.loads(raw)

        a2 = next(d for d in data if d["name"] == "agent-2")
        assert a2["status"] == "unknown"


# ---------------------------------------------------------------------------
# send_to_instance
# ---------------------------------------------------------------------------


class TestSendToInstance:
    async def test_sends_message_successfully(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.send_to_instance("agent-1", "hello")
        data = json.loads(raw)

        assert data["ok"] is True
        assert data["target"] == "agent-1"
        fm.send_message_to_instance.assert_awaited_once_with("agent-1", "hello")

    async def test_target_not_found(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.send_to_instance("no-such", "hello")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "not found" in data["error"]
        assert "available_instances" in data

    async def test_send_failure_returns_error(self):
        fm = _make_fleet_manager()
        fm.send_message_to_instance = AsyncMock(side_effect=RuntimeError("tmux dead"))
        bridge.init_bridge(fm)

        raw = await bridge.send_to_instance("agent-1", "hello")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "tmux dead" in data["error"]


# ---------------------------------------------------------------------------
# request_information
# ---------------------------------------------------------------------------


class TestRequestInformation:
    async def test_sends_prefixed_question(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.request_information("agent-1", "What is the API?")
        data = json.loads(raw)

        assert data["ok"] is True
        fm.send_message_to_instance.assert_awaited_once_with(
            "agent-1", "[INFO REQUEST] What is the API?"
        )

    async def test_target_not_found(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.request_information("ghost", "question")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "not found" in data["error"]


# ---------------------------------------------------------------------------
# delegate_task
# ---------------------------------------------------------------------------


class TestDelegateTask:
    async def test_delegates_to_running_instance(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.delegate_task("agent-1", "fix bug #42")
        data = json.loads(raw)

        assert data["ok"] is True
        assert data["target"] == "agent-1"
        fm.start_instance.assert_not_awaited()
        fm.send_message_to_instance.assert_awaited_once()

    async def test_auto_wakes_stopped_instance(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.delegate_task("agent-2", "build lib")
        data = json.loads(raw)

        assert data["ok"] is True
        fm.start_instance.assert_awaited_once_with("agent-2")

    async def test_includes_context_in_message(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        await bridge.delegate_task("agent-1", "task", context="extra info")

        sent_msg = fm.send_message_to_instance.call_args[0][1]
        assert "[DELEGATED TASK] task" in sent_msg
        assert "[CONTEXT] extra info" in sent_msg

    async def test_target_not_found(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.delegate_task("ghost", "task")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "not found" in data["error"]
        assert "available_instances" in data

    async def test_wake_failure_returns_error(self):
        fm = _make_fleet_manager()
        fm.start_instance = AsyncMock(side_effect=RuntimeError("tmux failed"))
        bridge.init_bridge(fm)

        raw = await bridge.delegate_task("agent-2", "task")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "Failed to wake" in data["error"]


# ---------------------------------------------------------------------------
# report_result
# ---------------------------------------------------------------------------


class TestReportResult:
    async def test_reports_result_to_requester(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.report_result("agent-1", "done: all tests pass")
        data = json.loads(raw)

        assert data["ok"] is True
        fm.send_message_to_instance.assert_awaited_once_with(
            "agent-1", "[TASK RESULT] done: all tests pass"
        )

    async def test_requester_not_found(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.report_result("ghost", "result")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "not found" in data["error"]


# ---------------------------------------------------------------------------
# create_team
# ---------------------------------------------------------------------------


class TestCreateTeam:
    async def test_creates_team_successfully(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.create_team("frontend", ["agent-1", "agent-2"], "FE team")
        data = json.loads(raw)

        assert data["ok"] is True
        assert data["team"] == "frontend"
        assert len(fm.config.teams) == 1
        assert fm.config.teams[0].name == "frontend"

    async def test_member_not_found(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.create_team("team", ["agent-1", "ghost"])
        data = json.loads(raw)

        assert data["ok"] is False
        assert "ghost" in str(data["error"])

    async def test_duplicate_team_name(self):
        config = _make_config(
            teams=[TeamConfig(name="existing", members=["agent-1"])],
        )
        fm = _make_fleet_manager(config=config)
        bridge.init_bridge(fm)

        raw = await bridge.create_team("existing", ["agent-1"])
        data = json.loads(raw)

        assert data["ok"] is False
        assert "already exists" in data["error"]


# ---------------------------------------------------------------------------
# broadcast
# ---------------------------------------------------------------------------


class TestBroadcast:
    async def test_broadcasts_to_all_members(self):
        config = _make_config(
            teams=[TeamConfig(name="dev", members=["agent-1", "agent-2"])],
        )
        fm = _make_fleet_manager(config=config)
        bridge.init_bridge(fm)

        raw = await bridge.broadcast("dev", "deploy now")
        data = json.loads(raw)

        assert data["ok"] is True
        assert len(data["results"]) == 2
        assert all(r["ok"] for r in data["results"])
        assert fm.send_message_to_instance.await_count == 2

    async def test_team_not_found(self):
        fm = _make_fleet_manager()
        bridge.init_bridge(fm)

        raw = await bridge.broadcast("no-team", "msg")
        data = json.loads(raw)

        assert data["ok"] is False
        assert "not found" in data["error"]

    async def test_partial_failure(self):
        config = _make_config(
            teams=[TeamConfig(name="dev", members=["agent-1", "agent-2"])],
        )
        fm = _make_fleet_manager(config=config)
        call_count = 0

        async def _side_effect(name: str, msg: str) -> None:
            nonlocal call_count
            call_count += 1
            if name == "agent-2":
                raise RuntimeError("agent-2 offline")

        fm.send_message_to_instance = AsyncMock(side_effect=_side_effect)
        bridge.init_bridge(fm)

        raw = await bridge.broadcast("dev", "msg")
        data = json.loads(raw)

        assert data["ok"] is True
        results = data["results"]
        a1 = next(r for r in results if r["member"] == "agent-1")
        a2 = next(r for r in results if r["member"] == "agent-2")
        assert a1["ok"] is True
        assert a2["ok"] is False
        assert "offline" in a2["error"]
