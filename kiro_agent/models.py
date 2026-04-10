"""kiro-agent 資料模型與自訂例外類別。

定義艦隊管理系統中所有核心資料結構（dataclass）與例外類別。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InstanceStatus(Enum):
    """Agent Instance 的運行狀態。"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    HUNG = "hung"
    PAUSED_COST = "paused_cost"
    PAUSED_FAILOVER = "paused_failover"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class InstanceState:
    """單一 Agent Instance 的即時狀態。"""

    name: str
    status: InstanceStatus
    backend: str
    model: str
    context_usage_pct: float = 0.0
    daily_cost_usd: float = 0.0
    last_activity: datetime | None = None
    topic_id: int | None = None
    tmux_session: str | None = None


@dataclass
class RotationSnapshot:
    """Context 輪替時產生的狀態快照。"""

    instance_name: str
    timestamp: datetime
    summary: str
    key_decisions: list[str] = field(default_factory=list)
    pending_tasks: list[str] = field(default_factory=list)


@dataclass
class CostAlert:
    """費用警告事件。"""

    instance_name: str
    daily_cost_usd: float
    limit_usd: float
    alert_type: str  # "warning" | "limit_reached"


@dataclass
class HangAlert:
    """掛起偵測警告事件。"""

    instance_name: str
    last_activity: datetime
    timeout_minutes: int


@dataclass
class ScheduleEntry:
    """排程項目。"""

    id: int
    cron_expr: str
    message: str
    target_instance: str
    enabled: bool
    last_run: datetime | None = None


# ---------------------------------------------------------------------------
# 自訂例外類別
# ---------------------------------------------------------------------------

class KiroAgentError(Exception):
    """kiro-agent 基礎例外。"""


class ConfigError(KiroAgentError):
    """配置驗證錯誤，包含欄位名稱與問題描述。"""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Config error in '{field}': {message}")


class BackendError(KiroAgentError):
    """後端操作錯誤，包含後端名稱、錯誤類型與建議修復步驟。"""

    def __init__(self, backend: str, error_type: str, suggestion: str):
        self.backend = backend
        self.error_type = error_type
        self.suggestion = suggestion
        super().__init__(f"Backend '{backend}' {error_type}: {suggestion}")


class InstanceError(KiroAgentError):
    """Instance 操作錯誤。"""


class DispatchError(KiroAgentError):
    """訊息路由錯誤。"""
