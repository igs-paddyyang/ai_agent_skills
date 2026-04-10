"""單元測試 — kiro_agent.__main__ CLI 入口。

測試 build_parser 子命令解析與 format_status_table 表格格式化。
"""

import pytest

from kiro_agent.__main__ import build_parser, format_status_table
from kiro_agent.models import InstanceState, InstanceStatus


# ---------------------------------------------------------------------------
# build_parser 測試
# ---------------------------------------------------------------------------

class TestBuildParser:
    """測試 argparse 子命令結構。"""

    def setup_method(self):
        self.parser = build_parser()

    # -- fleet 子命令 --

    def test_fleet_start(self):
        args = self.parser.parse_args(["fleet", "start"])
        assert args.command == "fleet"
        assert args.fleet_action == "start"

    def test_fleet_stop(self):
        args = self.parser.parse_args(["fleet", "stop"])
        assert args.command == "fleet"
        assert args.fleet_action == "stop"

    def test_fleet_status(self):
        args = self.parser.parse_args(["fleet", "status"])
        assert args.command == "fleet"
        assert args.fleet_action == "status"

    # -- instance 子命令 --

    def test_instance_create(self):
        args = self.parser.parse_args(["instance", "create"])
        assert args.command == "instance"
        assert args.instance_action == "create"

    def test_instance_delete(self):
        args = self.parser.parse_args(["instance", "delete", "my-agent"])
        assert args.command == "instance"
        assert args.instance_action == "delete"
        assert args.name == "my-agent"

    def test_instance_delete_requires_name(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args(["instance", "delete"])

    # -- backend 子命令 --

    def test_backend_doctor(self):
        args = self.parser.parse_args(["backend", "doctor", "kiro-cli"])
        assert args.command == "backend"
        assert args.backend_action == "doctor"
        assert args.backend_name == "kiro-cli"

    def test_backend_doctor_requires_name(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args(["backend", "doctor"])

    # -- 無子命令 --

    def test_no_command(self):
        args = self.parser.parse_args([])
        assert args.command is None

    def test_version_flag(self):
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(["--version"])
        assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# format_status_table 測試
# ---------------------------------------------------------------------------

class TestFormatStatusTable:
    """測試 Instance 狀態表格格式化。"""

    def test_empty_instances(self):
        result = format_status_table([])
        assert result == "(no instances)"

    def test_single_instance(self):
        instances = [
            InstanceState(
                name="app-dev",
                status=InstanceStatus.RUNNING,
                backend="kiro-cli",
                model="claude-sonnet-4",
                context_usage_pct=45.0,
            ),
        ]
        result = format_status_table(instances)
        lines = result.split("\n")

        # 標題列
        assert "Name" in lines[0]
        assert "Status" in lines[0]
        assert "Backend" in lines[0]
        assert "Model" in lines[0]
        assert "Context%" in lines[0]

        # 分隔線
        assert set(lines[1].replace(" ", "")) == {"-"}

        # 資料列
        assert "app-dev" in lines[2]
        assert "running" in lines[2]
        assert "kiro-cli" in lines[2]
        assert "claude-sonnet-4" in lines[2]
        assert "45%" in lines[2]

    def test_multiple_instances(self):
        instances = [
            InstanceState(
                name="agent-1",
                status=InstanceStatus.RUNNING,
                backend="kiro-cli",
                model="auto",
                context_usage_pct=20.0,
            ),
            InstanceState(
                name="agent-2",
                status=InstanceStatus.STOPPED,
                backend="claude-code",
                model="claude-sonnet-4",
                context_usage_pct=0.0,
            ),
            InstanceState(
                name="long-name-agent",
                status=InstanceStatus.HUNG,
                backend="gemini-cli",
                model="gemini-2.5-pro",
                context_usage_pct=82.0,
            ),
        ]
        result = format_status_table(instances)
        lines = result.split("\n")

        # 標題 + 分隔線 + 3 資料列 = 5 行
        assert len(lines) == 5

        # 每個 instance 的名稱都出現在表格中
        assert "agent-1" in result
        assert "agent-2" in result
        assert "long-name-agent" in result

        # 狀態值
        assert "running" in result
        assert "stopped" in result
        assert "hung" in result

    def test_table_contains_all_fields(self):
        """確認表格包含每個 Instance 的所有必要欄位。"""
        instances = [
            InstanceState(
                name="test-inst",
                status=InstanceStatus.PAUSED_COST,
                backend="codex",
                model="gpt-4",
                context_usage_pct=99.0,
            ),
        ]
        result = format_status_table(instances)

        assert "test-inst" in result
        assert "paused_cost" in result
        assert "codex" in result
        assert "gpt-4" in result
        assert "99%" in result

    def test_zero_context_usage(self):
        instances = [
            InstanceState(
                name="idle",
                status=InstanceStatus.STOPPED,
                backend="kiro-cli",
                model="auto",
                context_usage_pct=0.0,
            ),
        ]
        result = format_status_table(instances)
        assert "0%" in result

    def test_column_alignment(self):
        """確認欄位對齊 — 每列的欄位數量一致。"""
        instances = [
            InstanceState(
                name="a",
                status=InstanceStatus.RUNNING,
                backend="kiro-cli",
                model="auto",
            ),
            InstanceState(
                name="very-long-instance-name",
                status=InstanceStatus.STOPPED,
                backend="claude-code",
                model="claude-sonnet-4.5",
            ),
        ]
        result = format_status_table(instances)
        lines = result.split("\n")

        # 所有資料列長度應相同（因為 ljust 對齊）
        data_lines = [lines[0]] + lines[2:]
        lengths = [len(line) for line in data_lines]
        assert len(set(lengths)) == 1, f"行長度不一致: {lengths}"
