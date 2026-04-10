"""config.py 單元測試 — FleetConfig 載入、驗證、序列化與 defaults 合併。"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from kiro_agent.config import (
    AccessConfig,
    CostGuardConfig,
    FleetConfig,
    HangDetectorConfig,
    InstanceConfig,
    TeamConfig,
    dump_config,
    load_config,
    load_config_from_string,
)
from kiro_agent.models import ConfigError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_YAML = textwrap.dedent("""\
    project_roots:
      my-app: /home/user/my-app

    channel:
      bot_token_env: TELEGRAM_BOT_TOKEN
      group_id: -1001234567890
      general_topic_id: 1

    defaults:
      backend: kiro-cli
      model: auto

    instances:
      - name: dev
        project: my-app
""")

FULL_YAML = textwrap.dedent("""\
    project_roots:
      my-app: /home/user/my-app
      my-lib: /home/user/my-lib

    channel:
      bot_token_env: TELEGRAM_BOT_TOKEN
      group_id: -1001234567890
      general_topic_id: 1

    defaults:
      backend: kiro-cli
      model: claude-sonnet-4

    instances:
      - name: app-dev
        project: my-app
        backend: claude-code
        model: claude-sonnet-4.5
        description: "主應用開發"
        auto_start: true
        model_failover:
          - claude-sonnet-4
          - claude-haiku-4.5
        mcp_tools:
          - list_instances
      - name: lib-dev
        project: my-lib
        description: "函式庫開發"

    teams:
      - name: frontend
        members: [app-dev, lib-dev]
        description: "前端團隊"

    cost_guard:
      daily_limit_usd: 15.0
      warn_at_percentage: 75
      timezone: UTC

    hang_detector:
      enabled: false
      timeout_minutes: 60

    access:
      mode: locked
      allowed_users:
        - 111
        - 222

    health_port: 9090
""")


# ---------------------------------------------------------------------------
# load_config_from_string — 正常路徑
# ---------------------------------------------------------------------------


class TestLoadConfigMinimal:
    """最小有效配置的載入。"""

    def test_loads_project_roots(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.project_roots == {"my-app": "/home/user/my-app"}

    def test_loads_channel(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.channel["bot_token_env"] == "TELEGRAM_BOT_TOKEN"
        assert cfg.channel["group_id"] == -1001234567890
        assert cfg.channel["general_topic_id"] == 1

    def test_loads_defaults(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.defaults == {"backend": "kiro-cli", "model": "auto"}

    def test_loads_instance_with_defaults_merged(self) -> None:
        """Instance 未指定 backend/model 時使用 defaults 值。"""
        cfg = load_config_from_string(MINIMAL_YAML)
        inst = cfg.instances[0]
        assert inst.name == "dev"
        assert inst.project == "my-app"
        assert inst.backend == "kiro-cli"
        assert inst.model == "auto"

    def test_default_cost_guard(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.cost_guard == CostGuardConfig()

    def test_default_hang_detector(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.hang_detector == HangDetectorConfig()

    def test_default_access(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.access == AccessConfig()

    def test_default_health_port(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.health_port == 8470

    def test_empty_teams(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        assert cfg.teams == []


class TestLoadConfigFull:
    """完整配置的載入。"""

    def test_instance_explicit_values(self) -> None:
        cfg = load_config_from_string(FULL_YAML)
        app = cfg.instances[0]
        assert app.backend == "claude-code"
        assert app.model == "claude-sonnet-4.5"
        assert app.auto_start is True
        assert app.model_failover == ["claude-sonnet-4", "claude-haiku-4.5"]
        assert app.mcp_tools == ["list_instances"]

    def test_instance_defaults_merged(self) -> None:
        """lib-dev 未指定 backend/model，應使用 defaults。"""
        cfg = load_config_from_string(FULL_YAML)
        lib = cfg.instances[1]
        assert lib.backend == "kiro-cli"
        assert lib.model == "claude-sonnet-4"

    def test_teams_loaded(self) -> None:
        cfg = load_config_from_string(FULL_YAML)
        assert len(cfg.teams) == 1
        assert cfg.teams[0].name == "frontend"
        assert cfg.teams[0].members == ["app-dev", "lib-dev"]

    def test_cost_guard(self) -> None:
        cfg = load_config_from_string(FULL_YAML)
        assert cfg.cost_guard.daily_limit_usd == 15.0
        assert cfg.cost_guard.warn_at_percentage == 75.0
        assert cfg.cost_guard.timezone == "UTC"

    def test_hang_detector(self) -> None:
        cfg = load_config_from_string(FULL_YAML)
        assert cfg.hang_detector.enabled is False
        assert cfg.hang_detector.timeout_minutes == 60

    def test_access(self) -> None:
        cfg = load_config_from_string(FULL_YAML)
        assert cfg.access.mode == "locked"
        assert cfg.access.allowed_users == [111, 222]

    def test_health_port(self) -> None:
        cfg = load_config_from_string(FULL_YAML)
        assert cfg.health_port == 9090


# ---------------------------------------------------------------------------
# load_config_from_string — 錯誤路徑
# ---------------------------------------------------------------------------


class TestLoadConfigErrors:
    """缺少必要欄位或無效值時 raise ConfigError。"""

    def test_empty_yaml(self) -> None:
        with pytest.raises(ConfigError, match="root"):
            load_config_from_string("")

    def test_invalid_yaml(self) -> None:
        with pytest.raises(ConfigError, match="yaml"):
            load_config_from_string("{{invalid")

    def test_missing_project_roots(self) -> None:
        yaml_str = textwrap.dedent("""\
            channel:
              bot_token_env: T
              group_id: 1
              general_topic_id: 1
            defaults:
              backend: kiro-cli
              model: auto
            instances:
              - name: x
                project: a
        """)
        with pytest.raises(ConfigError, match="project_roots"):
            load_config_from_string(yaml_str)

    def test_missing_channel(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            defaults:
              backend: kiro-cli
              model: auto
            instances:
              - name: x
                project: a
        """)
        with pytest.raises(ConfigError, match="channel"):
            load_config_from_string(yaml_str)

    def test_missing_channel_bot_token_env(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            channel:
              group_id: 1
              general_topic_id: 1
            defaults:
              backend: kiro-cli
              model: auto
            instances:
              - name: x
                project: a
        """)
        with pytest.raises(ConfigError, match="bot_token_env"):
            load_config_from_string(yaml_str)

    def test_missing_defaults(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            channel:
              bot_token_env: T
              group_id: 1
              general_topic_id: 1
            instances:
              - name: x
                project: a
        """)
        with pytest.raises(ConfigError, match="defaults"):
            load_config_from_string(yaml_str)

    def test_missing_instances(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            channel:
              bot_token_env: T
              group_id: 1
              general_topic_id: 1
            defaults:
              backend: kiro-cli
              model: auto
        """)
        with pytest.raises(ConfigError, match="instances"):
            load_config_from_string(yaml_str)

    def test_empty_instances(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            channel:
              bot_token_env: T
              group_id: 1
              general_topic_id: 1
            defaults:
              backend: kiro-cli
              model: auto
            instances: []
        """)
        with pytest.raises(ConfigError, match="instances"):
            load_config_from_string(yaml_str)

    def test_instance_missing_name(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            channel:
              bot_token_env: T
              group_id: 1
              general_topic_id: 1
            defaults:
              backend: kiro-cli
              model: auto
            instances:
              - project: a
        """)
        with pytest.raises(ConfigError, match="name"):
            load_config_from_string(yaml_str)

    def test_instance_missing_project(self) -> None:
        yaml_str = textwrap.dedent("""\
            project_roots:
              a: /a
            channel:
              bot_token_env: T
              group_id: 1
              general_topic_id: 1
            defaults:
              backend: kiro-cli
              model: auto
            instances:
              - name: x
        """)
        with pytest.raises(ConfigError, match="project"):
            load_config_from_string(yaml_str)


# ---------------------------------------------------------------------------
# load_config — 檔案路徑
# ---------------------------------------------------------------------------


class TestLoadConfigFile:
    """從檔案載入。"""

    def test_file_not_found(self) -> None:
        with pytest.raises(ConfigError, match="path"):
            load_config("/nonexistent/fleet.yaml")

    def test_load_from_file(self, tmp_path: Path) -> None:
        p = tmp_path / "fleet.yaml"
        p.write_text(MINIMAL_YAML, encoding="utf-8")
        cfg = load_config(p)
        assert cfg.instances[0].name == "dev"


# ---------------------------------------------------------------------------
# dump_config — 序列化
# ---------------------------------------------------------------------------


class TestDumpConfig:
    """dump_config 序列化。"""

    def test_dump_produces_valid_yaml(self) -> None:
        cfg = load_config_from_string(MINIMAL_YAML)
        yaml_str = dump_config(cfg)
        data = __import__("yaml").safe_load(yaml_str)
        assert "project_roots" in data
        assert "instances" in data

    def test_round_trip(self) -> None:
        """load → dump → load 產生等價物件。"""
        cfg1 = load_config_from_string(FULL_YAML)
        yaml_str = dump_config(cfg1)
        cfg2 = load_config_from_string(yaml_str)
        assert cfg1 == cfg2

    def test_round_trip_minimal(self) -> None:
        cfg1 = load_config_from_string(MINIMAL_YAML)
        yaml_str = dump_config(cfg1)
        cfg2 = load_config_from_string(yaml_str)
        assert cfg1 == cfg2
