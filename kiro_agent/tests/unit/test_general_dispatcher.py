"""General_Dispatcher 單元測試。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from kiro_agent.config import FleetConfig, InstanceConfig, TeamConfig
from kiro_agent.general_dispatcher import DispatchResult, GeneralDispatcher


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_instances() -> list[InstanceConfig]:
    return [
        InstanceConfig(name="app-dev", project="my-app", description="主應用開發 Agent"),
        InstanceConfig(name="lib-dev", project="my-lib", description="函式庫開發 Agent"),
        InstanceConfig(name="docs-dev", project="my-docs", description="文件撰寫 Agent"),
    ]


def _make_teams() -> list[TeamConfig]:
    return [
        TeamConfig(name="frontend", members=["app-dev", "lib-dev"], description="前端開發團隊"),
    ]


def _make_fleet_manager(
    instances: list[InstanceConfig] | None = None,
    teams: list[TeamConfig] | None = None,
) -> Any:
    """建立模擬的 FleetManager。"""
    fm = MagicMock()
    fm.config = MagicMock()
    fm.config.instances = instances or _make_instances()
    fm.config.teams = teams or _make_teams()
    return fm


def _make_llm_response(data: dict) -> Any:
    """建立模擬的 LLM 回應物件。"""
    resp = MagicMock()
    resp.text = json.dumps(data)
    return resp


# ---------------------------------------------------------------------------
# DispatchResult dataclass
# ---------------------------------------------------------------------------


class TestDispatchResult:
    """DispatchResult dataclass 欄位測試。"""

    def test_fields(self) -> None:
        result = DispatchResult(
            target="app-dev",
            target_type="instance",
            confidence=0.95,
            explanation="路由到 app-dev",
        )
        assert result.target == "app-dev"
        assert result.target_type == "instance"
        assert result.confidence == 0.95
        assert result.explanation == "路由到 app-dev"

    def test_unknown_result(self) -> None:
        result = DispatchResult(
            target=None,
            target_type="unknown",
            confidence=0.0,
            explanation="無法識別",
        )
        assert result.target is None
        assert result.target_type == "unknown"
        assert result.confidence == 0.0

    def test_team_result(self) -> None:
        result = DispatchResult(
            target="frontend",
            target_type="team",
            confidence=0.8,
            explanation="廣播到 frontend 團隊",
        )
        assert result.target_type == "team"


# ---------------------------------------------------------------------------
# _build_routing_prompt
# ---------------------------------------------------------------------------


class TestBuildRoutingPrompt:
    """_build_routing_prompt 測試。"""

    def test_includes_all_instance_names(self) -> None:
        fm = _make_fleet_manager()
        dispatcher = GeneralDispatcher(fm, llm_client=None)
        instances = _make_instances()
        teams = _make_teams()
        prompt = dispatcher._build_routing_prompt("測試訊息", instances, teams)

        for inst in instances:
            assert inst.name in prompt
            if inst.description:
                assert inst.description in prompt

    def test_includes_team_names(self) -> None:
        fm = _make_fleet_manager()
        dispatcher = GeneralDispatcher(fm, llm_client=None)
        instances = _make_instances()
        teams = _make_teams()
        prompt = dispatcher._build_routing_prompt("測試訊息", instances, teams)

        for team in teams:
            assert team.name in prompt

    def test_includes_user_message(self) -> None:
        fm = _make_fleet_manager()
        dispatcher = GeneralDispatcher(fm, llm_client=None)
        msg = "幫我修改 app 的登入頁面"
        prompt = dispatcher._build_routing_prompt(msg, _make_instances())
        assert msg in prompt

    def test_no_teams(self) -> None:
        fm = _make_fleet_manager()
        dispatcher = GeneralDispatcher(fm, llm_client=None)
        prompt = dispatcher._build_routing_prompt("test", _make_instances(), None)
        assert "可用 Team" not in prompt


# ---------------------------------------------------------------------------
# dispatch — LLM 為 None
# ---------------------------------------------------------------------------


class TestDispatchWithoutLLM:
    """dispatch() 在 LLM 不可用時的行為。"""

    @pytest.mark.asyncio
    async def test_returns_unknown_when_llm_is_none(self) -> None:
        fm = _make_fleet_manager()
        dispatcher = GeneralDispatcher(fm, llm_client=None)
        # 確保 llm 為 None
        dispatcher.llm = None

        result = await dispatcher.dispatch("幫我修改 app")
        assert result.target is None
        assert result.target_type == "unknown"
        assert result.confidence == 0.0
        # explanation 應列出可用 Instance
        assert "app-dev" in result.explanation
        assert "lib-dev" in result.explanation

    @pytest.mark.asyncio
    async def test_unknown_lists_teams(self) -> None:
        fm = _make_fleet_manager()
        dispatcher = GeneralDispatcher(fm, llm_client=None)
        dispatcher.llm = None

        result = await dispatcher.dispatch("test")
        assert "frontend" in result.explanation


# ---------------------------------------------------------------------------
# dispatch — LLM 正常回應
# ---------------------------------------------------------------------------


class TestDispatchWithLLM:
    """dispatch() 在 LLM 正常回應時的行為。"""

    @pytest.mark.asyncio
    async def test_routes_to_instance(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        mock_llm.models.generate_content.return_value = _make_llm_response({
            "target": "app-dev",
            "target_type": "instance",
            "confidence": 0.92,
            "explanation": "訊息提到 app 開發",
        })

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("幫我修改 app 的登入頁面")

        assert result.target == "app-dev"
        assert result.target_type == "instance"
        assert result.confidence == 0.92
        mock_llm.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_team(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        mock_llm.models.generate_content.return_value = _make_llm_response({
            "target": "frontend",
            "target_type": "team",
            "confidence": 0.85,
            "explanation": "廣播到前端團隊",
        })

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("前端團隊全部更新依賴")

        assert result.target == "frontend"
        assert result.target_type == "team"

    @pytest.mark.asyncio
    async def test_llm_returns_unknown(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        mock_llm.models.generate_content.return_value = _make_llm_response({
            "target": None,
            "target_type": "unknown",
            "confidence": 0.1,
            "explanation": "無法判斷",
        })

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("今天天氣如何")

        assert result.target is None
        assert result.target_type == "unknown"
        assert "app-dev" in result.explanation  # 列出可用 Instance


# ---------------------------------------------------------------------------
# dispatch — LLM 錯誤處理
# ---------------------------------------------------------------------------


class TestDispatchErrorHandling:
    """dispatch() 在 LLM 錯誤時的行為。"""

    @pytest.mark.asyncio
    async def test_handles_llm_exception(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        mock_llm.models.generate_content.side_effect = RuntimeError("API 錯誤")

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("test")

        assert result.target is None
        assert result.target_type == "unknown"
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        resp = MagicMock()
        resp.text = "這不是 JSON"
        mock_llm.models.generate_content.return_value = resp

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("test")

        assert result.target is None
        assert result.target_type == "unknown"

    @pytest.mark.asyncio
    async def test_handles_none_text_response(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        resp = MagicMock()
        resp.text = None
        mock_llm.models.generate_content.return_value = resp

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("test")

        assert result.target is None
        assert result.target_type == "unknown"

    @pytest.mark.asyncio
    async def test_handles_markdown_wrapped_json(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        resp = MagicMock()
        resp.text = '```json\n{"target": "app-dev", "target_type": "instance", "confidence": 0.9, "explanation": "test"}\n```'
        mock_llm.models.generate_content.return_value = resp

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("修改 app")

        assert result.target == "app-dev"
        assert result.target_type == "instance"

    @pytest.mark.asyncio
    async def test_handles_nonexistent_target(self) -> None:
        fm = _make_fleet_manager()
        mock_llm = MagicMock()
        mock_llm.models.generate_content.return_value = _make_llm_response({
            "target": "nonexistent-agent",
            "target_type": "instance",
            "confidence": 0.8,
            "explanation": "test",
        })

        dispatcher = GeneralDispatcher(fm, llm_client=mock_llm)
        result = await dispatcher.dispatch("test")

        # 不存在的 target 應回傳 unknown
        assert result.target is None
        assert result.target_type == "unknown"


# ---------------------------------------------------------------------------
# _create_default_client
# ---------------------------------------------------------------------------


class TestCreateDefaultClient:
    """_create_default_client 測試。"""

    def test_returns_none_without_api_key(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            # 確保 GOOGLE_API_KEY 不存在
            import os
            os.environ.pop("GOOGLE_API_KEY", None)
            client = GeneralDispatcher._create_default_client()
            assert client is None

    def test_returns_none_on_import_error(self) -> None:
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            with patch("kiro_agent.general_dispatcher.os.environ.get", return_value="test-key"):
                # 模擬 import 失敗
                with patch.dict("sys.modules", {"google.genai": None}):
                    # 這會觸發 ImportError
                    pass
