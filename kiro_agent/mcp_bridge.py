"""MCP Bridge — Agent 間 P2P 協作的 MCP Tool 橋接層。

使用 FastMCP 建立 MCP Server，提供七個 MCP Tool 讓 Agent 之間
可以互相發現、傳訊、委派任務與廣播訊息。

透過 init_bridge() 注入 FleetManager 參考，各 Tool 透過
module-level _fleet_manager 存取艦隊狀態。
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from kiro_agent.fleet_manager import FleetManager

logger = logging.getLogger(__name__)

mcp = FastMCP("kiro-agent-bridge")

_fleet_manager: FleetManager | None = None


def init_bridge(fleet_manager: FleetManager) -> FastMCP:
    """初始化 MCP Bridge，注入 FleetManager 參考。

    Args:
        fleet_manager: 艦隊管理核心實例。

    Returns:
        已配置的 FastMCP Server 實例。
    """
    global _fleet_manager
    _fleet_manager = fleet_manager
    return mcp


def _require_fleet_manager() -> FleetManager:
    """取得 FleetManager，未初始化時 raise RuntimeError。"""
    if _fleet_manager is None:
        raise RuntimeError("MCP Bridge 尚未初始化，請先呼叫 init_bridge()")
    return _fleet_manager



# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_instances() -> str:
    """列出所有 Instance 的名稱、狀態、描述與後端類型。"""
    fm = _require_fleet_manager()
    result = []
    for inst_cfg in fm.config.instances:
        state = fm.instances.get(inst_cfg.name)
        status = state.status.value if state else "unknown"
        result.append({
            "name": inst_cfg.name,
            "status": status,
            "description": inst_cfg.description,
            "backend": inst_cfg.backend,
        })
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def send_to_instance(target: str, message: str) -> str:
    """透過 IPC 將訊息傳送到目標 Instance 的 tmux Session。

    Args:
        target: 目標 Instance 名稱。
        message: 要傳送的訊息。
    """
    fm = _require_fleet_manager()
    if target not in fm.instances:
        available = [cfg.name for cfg in fm.config.instances]
        return json.dumps({
            "ok": False,
            "error": f"Instance '{target}' not found",
            "available_instances": available,
        }, ensure_ascii=False)

    try:
        await fm.send_message_to_instance(target, message)
        return json.dumps({"ok": True, "target": target}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({
            "ok": False,
            "error": str(exc),
        }, ensure_ascii=False)


@mcp.tool()
async def request_information(target: str, question: str) -> str:
    """向目標 Instance 請求資訊。

    Args:
        target: 目標 Instance 名稱。
        question: 要詢問的問題。
    """
    fm = _require_fleet_manager()
    if target not in fm.instances:
        available = [cfg.name for cfg in fm.config.instances]
        return json.dumps({
            "ok": False,
            "error": f"Instance '{target}' not found",
            "available_instances": available,
        }, ensure_ascii=False)

    prefixed = f"[INFO REQUEST] {question}"
    try:
        await fm.send_message_to_instance(target, prefixed)
        return json.dumps({
            "ok": True,
            "target": target,
            "question": question,
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({
            "ok": False,
            "error": str(exc),
        }, ensure_ascii=False)


@mcp.tool()
async def delegate_task(target: str, task: str, context: str = "") -> str:
    """委派任務到目標 Instance（若未啟動則自動喚醒）。

    Args:
        target: 目標 Instance 名稱。
        task: 任務描述。
        context: 額外上下文資訊（選填）。
    """
    fm = _require_fleet_manager()
    if target not in fm.instances:
        available = [cfg.name for cfg in fm.config.instances]
        return json.dumps({
            "ok": False,
            "error": f"Instance '{target}' not found",
            "available_instances": available,
        }, ensure_ascii=False)

    state = fm.instances[target]

    # 自動喚醒未啟動的 Instance
    if state.status.value in ("stopped", "paused_cost", "paused_failover"):
        try:
            await fm.start_instance(target)
        except Exception as exc:
            return json.dumps({
                "ok": False,
                "error": f"Failed to wake instance '{target}': {exc}",
            }, ensure_ascii=False)

    # 組合任務訊息
    msg = f"[DELEGATED TASK] {task}"
    if context:
        msg += f"\n\n[CONTEXT] {context}"

    try:
        await fm.send_message_to_instance(target, msg)
        return json.dumps({
            "ok": True,
            "target": target,
            "task": task,
            "auto_woke": True,
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({
            "ok": False,
            "error": str(exc),
        }, ensure_ascii=False)


@mcp.tool()
async def report_result(requester: str, result: str) -> str:
    """將任務結果回傳給委派者。

    Args:
        requester: 委派者 Instance 名稱。
        result: 任務結果。
    """
    fm = _require_fleet_manager()
    if requester not in fm.instances:
        available = [cfg.name for cfg in fm.config.instances]
        return json.dumps({
            "ok": False,
            "error": f"Instance '{requester}' not found",
            "available_instances": available,
        }, ensure_ascii=False)

    msg = f"[TASK RESULT] {result}"
    try:
        await fm.send_message_to_instance(requester, msg)
        return json.dumps({
            "ok": True,
            "requester": requester,
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({
            "ok": False,
            "error": str(exc),
        }, ensure_ascii=False)


@mcp.tool()
async def create_team(name: str, members: list[str], description: str = "") -> str:
    """建立新的 Team。

    Args:
        name: Team 名稱。
        members: 成員 Instance 名稱清單。
        description: Team 描述（選填）。
    """
    from kiro_agent.config import TeamConfig

    fm = _require_fleet_manager()

    # 驗證成員是否存在
    missing = [m for m in members if m not in fm.instances]
    if missing:
        return json.dumps({
            "ok": False,
            "error": f"Members not found: {missing}",
            "available_instances": [cfg.name for cfg in fm.config.instances],
        }, ensure_ascii=False)

    # 檢查 Team 名稱是否重複
    existing_names = {t.name for t in fm.config.teams}
    if name in existing_names:
        return json.dumps({
            "ok": False,
            "error": f"Team '{name}' already exists",
        }, ensure_ascii=False)

    team = TeamConfig(name=name, members=list(members), description=description)
    fm.config.teams.append(team)

    return json.dumps({
        "ok": True,
        "team": name,
        "members": members,
        "description": description,
    }, ensure_ascii=False)


@mcp.tool()
async def broadcast(team: str, message: str) -> str:
    """廣播訊息到 Team 的所有成員 Instance。

    Args:
        team: Team 名稱。
        message: 要廣播的訊息。
    """
    fm = _require_fleet_manager()

    # 找到 Team
    team_cfg = None
    for t in fm.config.teams:
        if t.name == team:
            team_cfg = t
            break

    if team_cfg is None:
        available_teams = [t.name for t in fm.config.teams]
        return json.dumps({
            "ok": False,
            "error": f"Team '{team}' not found",
            "available_teams": available_teams,
        }, ensure_ascii=False)

    results: list[dict[str, object]] = []
    for member in team_cfg.members:
        try:
            await fm.send_message_to_instance(member, f"[BROADCAST from {team}] {message}")
            results.append({"member": member, "ok": True})
        except Exception as exc:
            results.append({"member": member, "ok": False, "error": str(exc)})

    return json.dumps({
        "ok": True,
        "team": team,
        "results": results,
    }, ensure_ascii=False)
