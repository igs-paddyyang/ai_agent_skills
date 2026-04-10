"""Dashboard 單元測試 — 使用 httpx.AsyncClient 測試 FastAPI 端點。"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest
import httpx

from kiro_agent.dashboard import app, create_app, init_dashboard, push_event, _sse_clients
from kiro_agent.models import InstanceState, InstanceStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_fleet_manager():
    """建立帶有測試 Instance 的 mock FleetManager。"""
    fm = MagicMock()
    fm.instances = {
        "agent-1": InstanceState(
            name="agent-1",
            status=InstanceStatus.RUNNING,
            backend="kiro-cli",
            model="claude-sonnet-4",
            context_usage_pct=42.5,
            daily_cost_usd=3.21,
        ),
        "agent-2": InstanceState(
            name="agent-2",
            status=InstanceStatus.STOPPED,
            backend="claude-code",
            model="auto",
            context_usage_pct=0.0,
            daily_cost_usd=0.0,
        ),
    }
    return fm


@pytest.fixture()
def mock_event_logger():
    """建立 mock EventLogger，query 回傳固定事件。"""
    logger = MagicMock()
    logger.query.return_value = [
        {"id": 1, "event_type": "instance_started", "instance_name": "agent-1", "data": {}},
        {"id": 2, "event_type": "instance_stopped", "instance_name": "agent-2", "data": {}},
    ]
    return logger


@pytest.fixture()
def configured_app(mock_fleet_manager, mock_event_logger):
    """透過 create_app 建立已配置的 app。"""
    return create_app(mock_fleet_manager, mock_event_logger)


# ---------------------------------------------------------------------------
# Tests: GET /api/instances
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_instances_returns_correct_data(configured_app, mock_fleet_manager):
    """GET /api/instances 回傳所有 Instance 的即時狀態。"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=configured_app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/instances")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    names = {d["name"] for d in data}
    assert names == {"agent-1", "agent-2"}

    agent1 = next(d for d in data if d["name"] == "agent-1")
    assert agent1["status"] == "running"
    assert agent1["backend"] == "kiro-cli"
    assert agent1["model"] == "claude-sonnet-4"
    assert agent1["context_usage_pct"] == 42.5
    assert agent1["daily_cost_usd"] == 3.21


@pytest.mark.asyncio
async def test_get_instances_empty_when_no_manager():
    """未初始化 FleetManager 時回傳空清單。"""
    init_dashboard(None, None)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/instances")

    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Tests: GET /api/events
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_events_returns_events(configured_app, mock_event_logger):
    """GET /api/events 回傳事件日誌。"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=configured_app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/events")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["event_type"] == "instance_started"
    mock_event_logger.query.assert_called_once_with(limit=50)


@pytest.mark.asyncio
async def test_get_events_with_limit(configured_app, mock_event_logger):
    """GET /api/events?limit=10 傳遞 limit 參數。"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=configured_app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/events?limit=10")

    assert resp.status_code == 200
    mock_event_logger.query.assert_called_once_with(limit=10)


@pytest.mark.asyncio
async def test_get_events_empty_when_no_logger():
    """未初始化 EventLogger 時回傳空清單。"""
    init_dashboard(None, None)  # type: ignore[arg-type]
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get("/api/events")

    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Tests: create_app factory
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_app_returns_fastapi(mock_fleet_manager, mock_event_logger):
    """create_app 回傳可用的 FastAPI 實例。"""
    from fastapi import FastAPI as _FastAPI

    result = create_app(mock_fleet_manager, mock_event_logger)
    assert isinstance(result, _FastAPI)
    assert result.title == "kiro-agent Dashboard"


# ---------------------------------------------------------------------------
# Tests: push_event
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_push_event_delivers_to_clients():
    """push_event 將事件推送到所有已連線的 SSE 客戶端。"""
    q1: asyncio.Queue[dict] = asyncio.Queue()
    q2: asyncio.Queue[dict] = asyncio.Queue()
    _sse_clients.clear()
    _sse_clients.extend([q1, q2])

    try:
        event = {"type": "status_change", "instance": "agent-1"}
        await push_event(event)

        assert not q1.empty()
        assert not q2.empty()
        assert await q1.get() == event
        assert await q2.get() == event
    finally:
        _sse_clients.clear()
