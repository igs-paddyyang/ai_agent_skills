"""kiro-agent 艦隊配置載入與驗證。

從 YAML 載入 FleetConfig，驗證必要欄位，合併 defaults，
並支援序列化回 YAML 字串（round-trip）。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from kiro_agent.models import ConfigError


# ---------------------------------------------------------------------------
# Config Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class InstanceConfig:
    """單一 Agent Instance 的配置。"""

    name: str
    project: str  # project_roots 中的 key
    backend: str = "kiro-cli"
    model: str = "auto"
    description: str = ""
    auto_start: bool = False
    model_failover: list[str] = field(default_factory=list)
    mcp_tools: list[str] = field(default_factory=list)


@dataclass
class TeamConfig:
    """Team 配置。"""

    name: str
    members: list[str]
    description: str = ""


@dataclass
class CostGuardConfig:
    """費用控管配置。"""

    daily_limit_usd: float = 10.0
    warn_at_percentage: float = 80.0
    timezone: str = "Asia/Taipei"


@dataclass
class HangDetectorConfig:
    """掛起偵測配置。"""

    enabled: bool = True
    timeout_minutes: int = 30


@dataclass
class AccessConfig:
    """存取控制配置。"""

    mode: str = "locked"
    allowed_users: list[int] = field(default_factory=list)


@dataclass
class FleetConfig:
    """艦隊配置頂層結構。"""

    project_roots: dict[str, str]
    channel: dict[str, Any]
    defaults: dict[str, str]
    instances: list[InstanceConfig]
    teams: list[TeamConfig] = field(default_factory=list)
    cost_guard: CostGuardConfig = field(default_factory=CostGuardConfig)
    hang_detector: HangDetectorConfig = field(default_factory=HangDetectorConfig)
    access: AccessConfig = field(default_factory=AccessConfig)
    health_port: int = 8470


# ---------------------------------------------------------------------------
# 必要欄位定義
# ---------------------------------------------------------------------------

_REQUIRED_TOP_LEVEL = ("project_roots", "channel", "defaults", "instances")
_REQUIRED_CHANNEL = ("bot_token_env", "group_id", "general_topic_id")


# ---------------------------------------------------------------------------
# 內部解析輔助
# ---------------------------------------------------------------------------


def _parse_instance(raw: dict[str, Any], defaults: dict[str, str]) -> InstanceConfig:
    """將 dict 轉為 InstanceConfig，套用 defaults 合併邏輯。"""
    if not isinstance(raw, dict):
        raise ConfigError("instances", "每個 instance 必須是 dict")
    if "name" not in raw:
        raise ConfigError("instances.name", "instance 缺少必要欄位 'name'")
    if "project" not in raw:
        raise ConfigError(
            f"instances[{raw.get('name', '?')}].project",
            "instance 缺少必要欄位 'project'",
        )

    # defaults 合併：未指定 backend/model 時使用 defaults 值
    if "backend" not in raw:
        raw["backend"] = defaults.get("backend", "kiro-cli")
    if "model" not in raw:
        raw["model"] = defaults.get("model", "auto")

    return InstanceConfig(
        name=raw["name"],
        project=raw["project"],
        backend=raw.get("backend", "kiro-cli"),
        model=raw.get("model", "auto"),
        description=raw.get("description", ""),
        auto_start=bool(raw.get("auto_start", False)),
        model_failover=list(raw.get("model_failover", [])),
        mcp_tools=list(raw.get("mcp_tools", [])),
    )


def _parse_team(raw: dict[str, Any]) -> TeamConfig:
    """將 dict 轉為 TeamConfig。"""
    if not isinstance(raw, dict):
        raise ConfigError("teams", "每個 team 必須是 dict")
    if "name" not in raw:
        raise ConfigError("teams.name", "team 缺少必要欄位 'name'")
    if "members" not in raw:
        raise ConfigError(
            f"teams[{raw.get('name', '?')}].members",
            "team 缺少必要欄位 'members'",
        )
    return TeamConfig(
        name=raw["name"],
        members=list(raw["members"]),
        description=raw.get("description", ""),
    )


def _parse_cost_guard(raw: dict[str, Any] | None) -> CostGuardConfig:
    if raw is None:
        return CostGuardConfig()
    return CostGuardConfig(
        daily_limit_usd=float(raw.get("daily_limit_usd", 10.0)),
        warn_at_percentage=float(raw.get("warn_at_percentage", 80.0)),
        timezone=str(raw.get("timezone", "Asia/Taipei")),
    )


def _parse_hang_detector(raw: dict[str, Any] | None) -> HangDetectorConfig:
    if raw is None:
        return HangDetectorConfig()
    return HangDetectorConfig(
        enabled=bool(raw.get("enabled", True)),
        timeout_minutes=int(raw.get("timeout_minutes", 30)),
    )


def _parse_access(raw: dict[str, Any] | None) -> AccessConfig:
    if raw is None:
        return AccessConfig()
    return AccessConfig(
        mode=str(raw.get("mode", "locked")),
        allowed_users=[int(u) for u in raw.get("allowed_users", [])],
    )


def _validate_raw(data: dict[str, Any]) -> None:
    """驗證原始 YAML dict 的必要欄位。"""
    if not isinstance(data, dict):
        raise ConfigError("root", "配置必須是 YAML mapping")

    for key in _REQUIRED_TOP_LEVEL:
        if key not in data:
            raise ConfigError(key, f"缺少必要頂層欄位 '{key}'")

    # project_roots 驗證
    if not isinstance(data["project_roots"], dict):
        raise ConfigError("project_roots", "project_roots 必須是 mapping")

    # channel 驗證
    ch = data["channel"]
    if not isinstance(ch, dict):
        raise ConfigError("channel", "channel 必須是 mapping")
    for ck in _REQUIRED_CHANNEL:
        if ck not in ch:
            raise ConfigError(f"channel.{ck}", f"channel 缺少必要欄位 '{ck}'")

    # defaults 驗證
    if not isinstance(data["defaults"], dict):
        raise ConfigError("defaults", "defaults 必須是 mapping")

    # instances 驗證
    if not isinstance(data["instances"], list):
        raise ConfigError("instances", "instances 必須是 list")
    if len(data["instances"]) == 0:
        raise ConfigError("instances", "instances 不可為空")


# ---------------------------------------------------------------------------
# 公開 API
# ---------------------------------------------------------------------------


def _parse_config(data: dict[str, Any]) -> FleetConfig:
    """從已解析的 dict 建構 FleetConfig（共用邏輯）。"""
    _validate_raw(data)

    defaults = dict(data["defaults"])
    instances = [_parse_instance(inst, defaults) for inst in data["instances"]]
    teams = [_parse_team(t) for t in data.get("teams", [])]

    return FleetConfig(
        project_roots=dict(data["project_roots"]),
        channel=dict(data["channel"]),
        defaults=defaults,
        instances=instances,
        teams=teams,
        cost_guard=_parse_cost_guard(data.get("cost_guard")),
        hang_detector=_parse_hang_detector(data.get("hang_detector")),
        access=_parse_access(data.get("access")),
        health_port=int(data.get("health_port", 8470)),
    )


def load_config(path: str | Path) -> FleetConfig:
    """從 YAML 檔案載入並驗證 FleetConfig。

    Args:
        path: fleet.yaml 的檔案路徑。

    Returns:
        驗證通過的 FleetConfig 物件。

    Raises:
        ConfigError: 檔案不存在、格式錯誤或缺少必要欄位。
    """
    path = Path(path)
    if not path.exists():
        raise ConfigError("path", f"配置檔不存在: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError("path", f"無法讀取配置檔: {exc}") from exc

    return load_config_from_string(text)


def load_config_from_string(yaml_str: str) -> FleetConfig:
    """從 YAML 字串載入並驗證 FleetConfig（供測試使用）。

    Args:
        yaml_str: YAML 格式的配置字串。

    Returns:
        驗證通過的 FleetConfig 物件。

    Raises:
        ConfigError: 格式錯誤或缺少必要欄位。
    """
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as exc:
        raise ConfigError("yaml", f"YAML 解析失敗: {exc}") from exc

    if data is None:
        raise ConfigError("root", "配置檔內容為空")

    return _parse_config(data)


def dump_config(config: FleetConfig) -> str:
    """將 FleetConfig 序列化為 YAML 字串。

    Args:
        config: FleetConfig 物件。

    Returns:
        YAML 格式的字串。
    """
    data: dict[str, Any] = {
        "project_roots": dict(config.project_roots),
        "channel": dict(config.channel),
        "defaults": dict(config.defaults),
        "instances": [asdict(inst) for inst in config.instances],
        "health_port": config.health_port,
    }

    if config.teams:
        data["teams"] = [asdict(t) for t in config.teams]

    data["cost_guard"] = asdict(config.cost_guard)
    data["hang_detector"] = asdict(config.hang_detector)
    data["access"] = asdict(config.access)

    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
