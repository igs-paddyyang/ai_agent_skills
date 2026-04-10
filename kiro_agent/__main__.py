"""kiro-agent CLI 入口點

Usage:
    kiro-agent fleet start
    kiro-agent fleet stop
    kiro-agent fleet status
    kiro-agent instance create
    kiro-agent instance delete <name>
    kiro-agent backend doctor <backend-name>
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from kiro_agent import RUNTIME_DIR, ensure_runtime_dirs
from kiro_agent.backend_adapter import BACKEND_REGISTRY
from kiro_agent.models import InstanceState, InstanceStatus


# ---------------------------------------------------------------------------
# 狀態表格格式化（獨立函式，方便測試）
# ---------------------------------------------------------------------------


def format_status_table(instances: list[InstanceState]) -> str:
    """將 Instance 狀態清單格式化為表格字串。

    Columns: Name | Status | Backend | Model | Context%

    Args:
        instances: InstanceState 物件清單。

    Returns:
        格式化的表格字串。
    """
    headers = ["Name", "Status", "Backend", "Model", "Context%"]

    if not instances:
        return "(no instances)"

    # 準備每列資料
    rows: list[list[str]] = []
    for inst in instances:
        rows.append([
            inst.name,
            inst.status.value,
            inst.backend,
            inst.model,
            f"{inst.context_usage_pct:.0f}%",
        ])

    # 計算每欄最大寬度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    # 建構表格
    def _fmt_row(cells: list[str]) -> str:
        parts = [cell.ljust(col_widths[i]) for i, cell in enumerate(cells)]
        return "  ".join(parts)

    lines: list[str] = []
    lines.append(_fmt_row(headers))
    lines.append("  ".join("-" * w for w in col_widths))
    for row in rows:
        lines.append(_fmt_row(row))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# argparse 建構
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """建構 CLI 參數解析器。"""
    parser = argparse.ArgumentParser(
        prog="kiro-agent",
        description="kiro-agent — 多 Agent 艦隊管理系統",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__import__('kiro_agent').__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # fleet 子命令
    fleet_parser = subparsers.add_parser("fleet", help="艦隊管理")
    fleet_sub = fleet_parser.add_subparsers(dest="fleet_action")
    fleet_sub.add_parser("start", help="啟動艦隊")
    fleet_sub.add_parser("stop", help="停止艦隊")
    fleet_sub.add_parser("status", help="顯示艦隊狀態")

    # instance 子命令
    instance_parser = subparsers.add_parser("instance", help="Instance 管理")
    instance_sub = instance_parser.add_subparsers(dest="instance_action")
    instance_sub.add_parser("create", help="建立新 Instance")
    delete_parser = instance_sub.add_parser("delete", help="刪除 Instance")
    delete_parser.add_argument("name", help="Instance 名稱")

    # backend 子命令
    backend_parser = subparsers.add_parser("backend", help="後端管理")
    backend_sub = backend_parser.add_subparsers(dest="backend_action")
    doctor_parser = backend_sub.add_parser("doctor", help="檢查後端狀態")
    doctor_parser.add_argument("backend_name", help="後端名稱")

    return parser


# ---------------------------------------------------------------------------
# 子命令處理函式
# ---------------------------------------------------------------------------

_CONFIG_PATH = RUNTIME_DIR / "fleet.yaml"
_EVENTS_DB_PATH = RUNTIME_DIR / "events.db"


def _load_fleet_manager():
    """載入配置並建立 FleetManager（共用邏輯）。"""
    from kiro_agent.config import load_config
    from kiro_agent.event_logger import EventLogger
    from kiro_agent.fleet_manager import FleetManager

    config = load_config(_CONFIG_PATH)
    event_logger = EventLogger(str(_EVENTS_DB_PATH))
    return FleetManager(config, event_logger)


def cmd_fleet_start() -> None:
    """fleet start — 啟動艦隊。"""
    ensure_runtime_dirs()
    fm = _load_fleet_manager()
    print("正在啟動艦隊...")
    asyncio.run(fm.start_fleet())
    print("艦隊已啟動")


def cmd_fleet_stop() -> None:
    """fleet stop — 停止艦隊。"""
    fm = _load_fleet_manager()
    print("正在停止艦隊...")
    asyncio.run(fm.stop_fleet())
    print("艦隊已停止")


def cmd_fleet_status() -> None:
    """fleet status — 以表格格式顯示所有 Instance 狀態。"""
    fm = _load_fleet_manager()
    # FleetManager 初始化時會建立 instances dict，
    # 但不會啟動 — 我們只需要讀取配置並顯示狀態
    for inst_cfg in fm.config.instances:
        if inst_cfg.name not in fm.instances:
            fm.instances[inst_cfg.name] = InstanceState(
                name=inst_cfg.name,
                status=InstanceStatus.STOPPED,
                backend=inst_cfg.backend,
                model=inst_cfg.model,
            )

    states = list(fm.instances.values())
    print(format_status_table(states))


def cmd_instance_create() -> None:
    """instance create — 互動式建立新 Instance。"""
    fm = _load_fleet_manager()

    # 互動式輸入
    name = input("Instance 名稱: ").strip()
    if not name:
        print("錯誤: 名稱不可為空", file=sys.stderr)
        sys.exit(1)

    # 顯示可用 project
    print(f"可用 project: {', '.join(fm.config.project_roots.keys())}")
    project = input("Project 名稱: ").strip()
    if not project:
        print("錯誤: project 不可為空", file=sys.stderr)
        sys.exit(1)

    # 顯示可用 backend
    available_backends = ", ".join(sorted(BACKEND_REGISTRY.keys()))
    default_backend = fm.config.defaults.get("backend", "kiro-cli")
    backend = input(f"Backend [{default_backend}] ({available_backends}): ").strip()
    if not backend:
        backend = default_backend

    default_model = fm.config.defaults.get("model", "auto")
    model = input(f"Model [{default_model}]: ").strip()
    if not model:
        model = default_model

    asyncio.run(fm.create_instance(
        name=name,
        project=project,
        backend=backend,
        model=model,
    ))
    print(f"Instance '{name}' 已建立")


def cmd_instance_delete(name: str) -> None:
    """instance delete — 刪除指定 Instance。"""
    fm = _load_fleet_manager()

    # 初始化 instances 狀態以便 delete 能找到
    for inst_cfg in fm.config.instances:
        if inst_cfg.name not in fm.instances:
            fm.instances[inst_cfg.name] = InstanceState(
                name=inst_cfg.name,
                status=InstanceStatus.STOPPED,
                backend=inst_cfg.backend,
                model=inst_cfg.model,
            )

    asyncio.run(fm.delete_instance(name))
    print(f"Instance '{name}' 已刪除")


def cmd_backend_doctor(backend_name: str) -> None:
    """backend doctor — 檢查後端安裝/認證/版本。"""
    # 檢查 backend 是否在 registry 中
    if backend_name not in BACKEND_REGISTRY:
        available = ", ".join(sorted(BACKEND_REGISTRY.keys()))
        print(f"未知的後端 '{backend_name}'")
        print(f"可用的後端: {available}")
        sys.exit(1)

    # 取得 CLI 命令名稱
    adapter_cls = BACKEND_REGISTRY[backend_name]
    cli_command = getattr(adapter_cls, "cli_command", backend_name)

    print(f"Backend: {backend_name}")
    print(f"CLI Tool: {cli_command}")

    # 檢查是否安裝
    path = shutil.which(cli_command)
    if path is None:
        print(f"Installed: NO")
        print(f"  '{cli_command}' not found in PATH")
        sys.exit(1)

    print(f"Installed: YES ({path})")

    # 嘗試取得版本
    try:
        result = subprocess.run(
            [cli_command, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
        )
        version_output = (result.stdout or result.stderr).strip()
        if version_output:
            print(f"Version: {version_output}")
        else:
            print("Version: (unable to determine)")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        print("Version: (unable to determine)")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "fleet":
            if args.fleet_action == "start":
                cmd_fleet_start()
            elif args.fleet_action == "stop":
                cmd_fleet_stop()
            elif args.fleet_action == "status":
                cmd_fleet_status()
            else:
                parser.parse_args(["fleet", "--help"])

        elif args.command == "instance":
            if args.instance_action == "create":
                cmd_instance_create()
            elif args.instance_action == "delete":
                cmd_instance_delete(args.name)
            else:
                parser.parse_args(["instance", "--help"])

        elif args.command == "backend":
            if args.backend_action == "doctor":
                cmd_backend_doctor(args.backend_name)
            else:
                parser.parse_args(["backend", "--help"])

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n中斷操作")
        sys.exit(130)
    except Exception as exc:
        print(f"錯誤: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
