"""General Topic 自然語言路由。

使用 google-genai (Gemini) 分析使用者訊息意圖，
將訊息路由到正確的 Instance 或 Team。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.genai import Client as GenaiClient

    from kiro_agent.config import InstanceConfig, TeamConfig

logger = logging.getLogger(__name__)

# 專案標準模型
_MODEL = "models/gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# 資料模型
# ---------------------------------------------------------------------------


@dataclass
class DispatchResult:
    """路由結果。"""

    target: str | None
    target_type: str  # "instance" | "team" | "unknown"
    confidence: float  # 0.0 ~ 1.0
    explanation: str


# ---------------------------------------------------------------------------
# GeneralDispatcher
# ---------------------------------------------------------------------------


class GeneralDispatcher:
    """General Topic 自然語言路由 — 使用 Gemini 分析訊息意圖。"""

    def __init__(self, fleet_manager: Any, llm_client: GenaiClient | None = None) -> None:
        self.fleet_manager = fleet_manager
        self.llm = llm_client or self._create_default_client()

    # ------------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------------

    async def dispatch(self, user_message: str) -> DispatchResult:
        """分析使用者訊息，識別目標 Instance 或 Team。"""
        instances: list[InstanceConfig] = self.fleet_manager.config.instances
        teams: list[TeamConfig] = self.fleet_manager.config.teams

        # 無 LLM 可用 → 回傳 unknown 並列出可用 Instance
        if self.llm is None:
            return self._unknown_result(instances, teams)

        prompt = self._build_routing_prompt(user_message, instances, teams)

        try:
            response = self.llm.models.generate_content(
                model=_MODEL,
                contents=prompt,
            )
            return self._parse_response(response.text or "", instances, teams)
        except Exception:
            logger.exception("LLM 路由呼叫失敗")
            return self._unknown_result(instances, teams)

    def _build_routing_prompt(
        self,
        message: str,
        instances: list[InstanceConfig],
        teams: list[TeamConfig] | None = None,
    ) -> str:
        """建構路由 prompt，包含所有 Instance 與 Team 的名稱與描述。"""
        lines = [
            "你是一個訊息路由器。根據使用者訊息，判斷應該由哪個 Agent Instance 或 Team 處理。",
            "",
            "## 可用 Instance",
        ]
        for inst in instances:
            desc = inst.description or "(無描述)"
            lines.append(f"- {inst.name}: {desc}")

        if teams:
            lines.append("")
            lines.append("## 可用 Team")
            for team in teams:
                desc = team.description or "(無描述)"
                members = ", ".join(team.members)
                lines.append(f"- {team.name}: {desc} (成員: {members})")

        lines.extend([
            "",
            "## 使用者訊息",
            message,
            "",
            "## 回覆格式",
            "請以 JSON 格式回覆，包含以下欄位：",
            '- target: 目標名稱（Instance 或 Team 名稱），無法判斷時為 null',
            '- target_type: "instance" | "team" | "unknown"',
            "- confidence: 0.0 ~ 1.0 的信心分數",
            "- explanation: 路由理由（繁體中文）",
            "",
            "僅回覆 JSON，不要包含其他文字或 markdown 標記。",
        ])
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 內部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _create_default_client() -> GenaiClient | None:
        """嘗試建立預設的 google-genai Client。"""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY 未設定，General Dispatcher 將以 unknown 模式運作")
            return None
        try:
            from google.genai import Client  # noqa: WPS433

            return Client(api_key=api_key)
        except Exception:
            logger.exception("無法建立 google-genai Client")
            return None

    def _parse_response(
        self,
        text: str,
        instances: list[InstanceConfig],
        teams: list[TeamConfig],
    ) -> DispatchResult:
        """解析 LLM 回應為 DispatchResult。"""
        # 嘗試從回應中提取 JSON
        cleaned = text.strip()
        # 移除可能的 markdown code block 標記
        if cleaned.startswith("```"):
            first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            logger.warning("LLM 回應無法解析為 JSON: %s", text[:200])
            return self._unknown_result(instances, teams)

        target = data.get("target")
        target_type = data.get("target_type", "unknown")
        confidence = float(data.get("confidence", 0.0))
        explanation = data.get("explanation", "")

        # 驗證 target 是否存在
        if target_type == "instance":
            instance_names = {inst.name for inst in instances}
            if target not in instance_names:
                return self._unknown_result(instances, teams)
        elif target_type == "team":
            team_names = {t.name for t in teams}
            if target not in team_names:
                return self._unknown_result(instances, teams)
        elif target_type == "unknown" or target is None:
            return self._unknown_result(instances, teams)

        return DispatchResult(
            target=target,
            target_type=target_type,
            confidence=confidence,
            explanation=explanation,
        )

    @staticmethod
    def _unknown_result(
        instances: list[InstanceConfig],
        teams: list[TeamConfig],
    ) -> DispatchResult:
        """建構 unknown 結果，列出所有可用 Instance 與 Team。"""
        parts = ["無法識別目標，可用的 Instance："]
        for inst in instances:
            desc = f" — {inst.description}" if inst.description else ""
            parts.append(f"  • {inst.name}{desc}")
        if teams:
            parts.append("可用的 Team：")
            for team in teams:
                desc = f" — {team.description}" if team.description else ""
                parts.append(f"  • {team.name}{desc}")

        return DispatchResult(
            target=None,
            target_type="unknown",
            confidence=0.0,
            explanation="\n".join(parts),
        )
