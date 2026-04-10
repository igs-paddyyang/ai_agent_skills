"""Web Dashboard — FastAPI 即時艦隊狀態監控。

提供 HTTP API 端點回傳 Instance 狀態與事件日誌，
以及 SSE 即時推送狀態更新。

Requirements: 13.1, 13.2, 13.3, 13.4
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

if TYPE_CHECKING:
    from kiro_agent.event_logger import EventLogger
    from kiro_agent.fleet_manager import FleetManager

# ---------------------------------------------------------------------------
# Module-level references (set via init_dashboard or create_app)
# ---------------------------------------------------------------------------

_fleet_manager: FleetManager | None = None
_event_logger: EventLogger | None = None

# Connected SSE clients — each gets its own asyncio.Queue
_sse_clients: list[asyncio.Queue[dict]] = []


# ---------------------------------------------------------------------------
# Initialisation helpers
# ---------------------------------------------------------------------------

def init_dashboard(
    fleet_manager: FleetManager,
    event_logger: EventLogger,
) -> None:
    """設定 Dashboard 使用的 FleetManager 與 EventLogger 參照。"""
    global _fleet_manager, _event_logger  # noqa: PLW0603
    _fleet_manager = fleet_manager
    _event_logger = event_logger


def create_app(
    fleet_manager: FleetManager,
    event_logger: EventLogger,
) -> FastAPI:
    """工廠函式 — 建立並配置 Dashboard FastAPI app。

    Args:
        fleet_manager: 艦隊管理器實例。
        event_logger: 事件日誌記錄器實例。

    Returns:
        已配置的 FastAPI 應用程式。
    """
    init_dashboard(fleet_manager, event_logger)
    return app


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(title="kiro-agent Dashboard")


@app.get("/api/instances")
async def get_instances() -> list[dict]:
    """回傳所有 Instance 的即時狀態。"""
    if _fleet_manager is None:
        return []
    result: list[dict] = []
    for state in _fleet_manager.instances.values():
        result.append({
            "name": state.name,
            "status": state.status.value,
            "backend": state.backend,
            "model": state.model,
            "context_usage_pct": state.context_usage_pct,
            "daily_cost_usd": state.daily_cost_usd,
        })
    return result


@app.get("/api/events")
async def get_events(limit: int = 50) -> list[dict]:
    """回傳最近的事件日誌。"""
    if _event_logger is None:
        return []
    return _event_logger.query(limit=limit)


@app.get("/sse")
async def sse_stream(request: Request) -> StreamingResponse:
    """SSE 即時狀態推送端點。"""
    queue: asyncio.Queue[dict] = asyncio.Queue()
    _sse_clients.append(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive comment to detect disconnects
                    yield ": keep-alive\n\n"
        finally:
            _sse_clients.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Event push helper
# ---------------------------------------------------------------------------

async def push_event(event_data: dict) -> None:
    """推送事件到所有已連線的 SSE 客戶端。

    Args:
        event_data: 要推送的事件資料字典。
    """
    for queue in list(_sse_clients):
        try:
            queue.put_nowait(event_data)
        except asyncio.QueueFull:
            pass
