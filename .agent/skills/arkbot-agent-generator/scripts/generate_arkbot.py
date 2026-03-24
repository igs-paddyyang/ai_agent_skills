#!/usr/bin/env python3
"""
ArkBot 專案產生器（Deprecated — 請改用 generate.py arkbot）

用法：
    python generate_arkbot.py [project_name] [--output-dir DIR]

⚠️ 此腳本已棄用，請改用：
    python generate.py arkbot [project_name] [--output-dir DIR]
"""

import argparse
import warnings

from generator import Generator, load_manifest


def generate(project_name: str = "arkbot", output_dir: str = "."):
    """產生完整 ArkBot 專案（向後相容入口）"""
    warnings.warn(
        "generate_arkbot.py 已棄用，請改用：python generate.py arkbot",
        DeprecationWarning,
        stacklevel=2,
    )
    print("⚠️  generate_arkbot.py 已棄用，請改用：python generate.py arkbot\n")

    manifest = load_manifest("arkbot")
    gen = Generator(
        manifest=manifest,
        project_name=project_name,
        output_dir=output_dir,
    )
    gen.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArkBot 專案產生器（Deprecated）")
    parser.add_argument("name", nargs="?", default="arkbot", help="專案名稱")
    parser.add_argument("--output-dir", default=".", help="輸出目錄")
    args = parser.parse_args()
    generate(args.name, args.output_dir)
