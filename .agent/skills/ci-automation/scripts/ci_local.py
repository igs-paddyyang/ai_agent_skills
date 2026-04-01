#!/usr/bin/env python3
"""
本地 CI 模擬腳本

三階段流程：Lint → Validate → Sync

用法：
    py .kiro/skills/ci-automation/scripts/ci_local.py
    py .kiro/skills/ci-automation/scripts/ci_local.py --skip-lint
    py .kiro/skills/ci-automation/scripts/ci_local.py --skip-sync
"""

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
SKILLS_DIR = PROJECT_ROOT / ".kiro" / "skills"
VALIDATE_SCRIPT = SKILLS_DIR / "skill-creator" / "scripts" / "quick_validate.py"
SYNC_SCRIPT = SKILLS_DIR / "skill-sync" / "scripts" / "sync_skills.py"


def run_cmd(label: str, cmd: list[str]) -> bool:
    """Execute a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"[STAGE] {label}")
    print(f"[CMD]   {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, encoding="utf-8", errors="replace")

    if result.returncode == 0:
        print(f"[PASS] {label}")
        return True
    else:
        print(f"[FAIL] {label} (exit code: {result.returncode})")
        return False


def stage_lint() -> bool:
    """Stage 1: Lint with ruff."""
    return run_cmd("Lint (ruff check)", [sys.executable, "-m", "ruff", "check", "."])


def stage_validate() -> bool:
    """Stage 2: Validate all skills."""
    if not VALIDATE_SCRIPT.exists():
        print(f"[SKIP] Validate script not found: {VALIDATE_SCRIPT}")
        return True

    skill_dirs = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    passed = 0
    failed = 0

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        result = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), str(skill_dir)],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )

        if result.returncode == 0:
            passed += 1
        else:
            failed += 1
            print(f"  [FAIL] {skill_dir.name}: {result.stdout.strip()}")

    print(f"\n  Validate: {passed} passed, {failed} failed, {passed + failed} total")
    return failed == 0


def stage_sync() -> bool:
    """Stage 3: Sync skills."""
    if not SYNC_SCRIPT.exists():
        print(f"[SKIP] Sync script not found: {SYNC_SCRIPT}")
        return True

    return run_cmd("Skill Sync", [sys.executable, str(SYNC_SCRIPT)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Local CI simulation")
    parser.add_argument("--skip-lint", action="store_true", help="Skip lint stage")
    parser.add_argument("--skip-sync", action="store_true", help="Skip sync stage")
    args = parser.parse_args()

    print("[CI] Local CI simulation started")
    results: dict[str, bool] = {}

    # Stage 1: Lint
    if args.skip_lint:
        print("\n[SKIP] Lint stage skipped")
        results["Lint"] = True
    else:
        results["Lint"] = stage_lint()

    # Stage 2: Validate
    print(f"\n{'='*60}")
    print("[STAGE] Validate (quick_validate.py)")
    print(f"{'='*60}")
    results["Validate"] = stage_validate()

    # Stage 3: Sync
    if args.skip_sync:
        print("\n[SKIP] Sync stage skipped")
        results["Sync"] = True
    else:
        results["Sync"] = stage_sync()

    # Summary
    print(f"\n{'='*60}")
    print("[CI] Summary")
    print(f"{'='*60}")
    all_pass = True
    for stage, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {stage}")
        if not passed:
            all_pass = False

    if all_pass:
        print("\n[CI] All stages passed.")
    else:
        print("\n[CI] Some stages failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
