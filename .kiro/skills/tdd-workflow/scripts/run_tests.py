#!/usr/bin/env python3
"""
測試執行腳本 — tdd-workflow 的測試執行器

封裝 pytest，提供統一的測試執行介面。

用法：
    py .kiro/skills/tdd-workflow/scripts/run_tests.py --path tests/
    py .kiro/skills/tdd-workflow/scripts/run_tests.py --path tests/ --coverage
    py .kiro/skills/tdd-workflow/scripts/run_tests.py --path tests/ --verbose
"""

import argparse
import subprocess
import sys


def run_tests(path: str, coverage: bool = False, verbose: bool = False) -> int:
    """執行 pytest 測試。"""
    cmd = [sys.executable, "-m", "pytest", path]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])

    cmd.append("--tb=short")

    print(f"[RUN] {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(
        cmd,
        encoding="utf-8",
        errors="replace",
    )

    print("-" * 60)
    if result.returncode == 0:
        print("[PASS] All tests passed.")
    else:
        print(f"[FAIL] Tests failed (exit code: {result.returncode}).")

    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="tdd-workflow test runner")
    parser.add_argument("--path", required=True, help="Test directory or file path")
    parser.add_argument("--coverage", action="store_true", help="Enable coverage report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    exit_code = run_tests(args.path, args.coverage, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
