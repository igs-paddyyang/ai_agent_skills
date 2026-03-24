#!/usr/bin/env python3
"""
統一 Agent 專案產生器（Generator Platform）

用法：
    python generate.py <profile> [project_name] [options]

Profiles：
    arkbot      ArkBot 四層架構（Lite 模式，~38 檔）
    arkagent    ArkAgent OS 平台級架構（Full 模式，~80 檔）

選項：
    --output-dir DIR    輸出目錄（預設：當前目錄）
    --no-compat         跳過 src/ 相容層（僅 arkagent）
    --dry-run           只印出檔案清單，不實際產出
    --modules a,b,c     只產出指定模組

範例：
    python generate.py arkbot
    python generate.py arkbot my-bot --output-dir ./projects
    python generate.py arkagent my-agent
    python generate.py arkagent my-agent --no-compat
    python generate.py arkagent my-agent --dry-run
    python generate.py arkagent my-agent --modules kernel,memory,planner
    python generate.py --list    # 列出可用 profiles
"""

import argparse
import sys

from generator import Generator, load_manifest, list_profiles


def main():
    parser = argparse.ArgumentParser(
        description="統一 Agent 專案產生器（Generator Platform）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("profile", nargs="?", help="Profile 名稱（arkbot / arkagent）")
    parser.add_argument("name", nargs="?", help="專案名稱（預設使用 profile 名稱）")
    parser.add_argument("--output-dir", default=".", help="輸出目錄")
    parser.add_argument("--no-compat", action="store_true", help="跳過 src/ 相容層")
    parser.add_argument("--dry-run", action="store_true", help="只印出檔案清單")
    parser.add_argument("--modules", help="只產出指定模組（逗號分隔）")
    parser.add_argument("--list", action="store_true", help="列出可用 profiles")
    args = parser.parse_args()

    # --list：列出可用 profiles
    if args.list:
        print("\nAvailable Profiles:\n")
        for p in list_profiles():
            print(f"  - {p['name']:12s} {p['description']}")
        print()
        return

    # 檢查 profile
    if not args.profile:
        parser.print_help()
        sys.exit(1)

    try:
        manifest = load_manifest(args.profile)
    except ValueError as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)

    # 專案名稱
    project_name = args.name or manifest["default_project_name"]

    # --modules 解析
    modules_filter = None
    if args.modules:
        modules_filter = [m.strip() for m in args.modules.split(",")]

    # 執行
    gen = Generator(
        manifest=manifest,
        project_name=project_name,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        no_compat=args.no_compat,
        modules_filter=modules_filter,
    )
    gen.run()


if __name__ == "__main__":
    main()
