"""單元測試 — kiro_agent.models 資料模型與例外類別。"""

from datetime import datetime

import pytest

from kiro_agent.models import (
    BackendError,
    ConfigError,
    CostAlert,
    DispatchError,
    HangAlert,
    InstanceError,
    InstanceState,
    InstanceStatus,
    KiroAgentError,
    RotationSnapshot,
    ScheduleEntry,
)


# ---------------------------------------------------------------------------
# InstanceStatus enum
# ---------------------------------------------------------------------------

class TestInstanceStatus:
    def test_all_members_exist(self):
        expected = {"stopped", "starting", "running", "hung", "paused_cost", "paused_failover"}
        assert {s.value for s in InstanceStatus} == expected

    def test_lookup_by_value(self):
        assert InstanceStatus("running") is InstanceStatus.RUNNING


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

class TestInstanceState:
    def test_required_fields(self):
        state = InstanceState(
            name="dev",
            status=InstanceStatus.RUNNING,
            backend="kiro-cli",
            model="auto",
        )
        assert state.name == "dev"
        assert state.status is InstanceStatus.RUNNING
        assert state.context_usage_pct == 0.0
        assert state.daily_cost_usd == 0.0
        assert state.last_activity is None
        assert state.topic_id is None
        assert state.tmux_session is None


class TestRotationSnapshot:
    def test_defaults(self):
        now = datetime.now()
        snap = RotationSnapshot(instance_name="a", timestamp=now, summary="s")
        assert snap.key_decisions == []
        assert snap.pending_tasks == []


class TestCostAlert:
    def test_fields(self):
        alert = CostAlert(instance_name="x", daily_cost_usd=8.5, limit_usd=10.0, alert_type="warning")
        assert alert.alert_type == "warning"


class TestHangAlert:
    def test_fields(self):
        now = datetime.now()
        alert = HangAlert(instance_name="x", last_activity=now, timeout_minutes=30)
        assert alert.timeout_minutes == 30


class TestScheduleEntry:
    def test_last_run_default(self):
        entry = ScheduleEntry(id=1, cron_expr="* * * * *", message="hi", target_instance="a", enabled=True)
        assert entry.last_run is None


# ---------------------------------------------------------------------------
# 自訂例外
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_config_error_message_and_field(self):
        err = ConfigError("channel.bot_token_env", "missing value")
        assert err.field == "channel.bot_token_env"
        assert "channel.bot_token_env" in str(err)
        assert "missing value" in str(err)

    def test_config_error_is_kiro_agent_error(self):
        assert issubclass(ConfigError, KiroAgentError)

    def test_backend_error_attributes(self):
        err = BackendError("gemini-cli", "not_installed", "run: pip install gemini-cli")
        assert err.backend == "gemini-cli"
        assert err.error_type == "not_installed"
        assert err.suggestion == "run: pip install gemini-cli"
        assert "gemini-cli" in str(err)

    def test_backend_error_is_kiro_agent_error(self):
        assert issubclass(BackendError, KiroAgentError)

    def test_instance_error_is_kiro_agent_error(self):
        assert issubclass(InstanceError, KiroAgentError)

    def test_dispatch_error_is_kiro_agent_error(self):
        assert issubclass(DispatchError, KiroAgentError)

    def test_all_exceptions_catchable_as_base(self):
        for exc_cls in (ConfigError, BackendError, InstanceError, DispatchError):
            with pytest.raises(KiroAgentError):
                if exc_cls is ConfigError:
                    raise exc_cls("f", "m")
                elif exc_cls is BackendError:
                    raise exc_cls("b", "t", "s")
                else:
                    raise exc_cls("test")
