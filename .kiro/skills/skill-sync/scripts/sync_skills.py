"""
技能同步工具 — 將 .kiro/skills 的技能同步備份到 .agent/skills（或反向還原）。

用法：
    py .kiro/skills/skill-sync/scripts/sync_skills.py [--skills NAME ...] [--reverse] [--dry-run]

範例：
    py .kiro/skills/skill-sync/scripts/sync_skills.py                    # 全量同步（預設）
    py .kiro/skills/skill-sync/scripts/sync_skills.py --skills env-smoke-test skill-creator
    py .kiro/skills/skill-sync/scripts/sync_skills.py --reverse --skills skill-creator
    py .kiro/skills/skill-sync/scripts/sync_skills.py --dry-run
"""

import argparse
import shutil
from pathlib import Path

KIRO_SKILLS = Path(".kiro/skills")
AGENT_SKILLS = Path(".agent/skills")


def get_skill_list(args, src: Path) -> list[str]:
    """決定技能清單：--skills 指定 > 預設全量掃描。"""
    if args.skills:
        return args.skills
    if not src.exists():
        return []
    return sorted(d.name for d in src.iterdir() if d.is_dir())


def sync_one(name: str, src_root: Path, dst_root: Path, dry_run: bool) -> str:
    """同步單一技能，回傳狀態標記（success / skipped / failed）。"""
    src = src_root / name
    dst = dst_root / name

    if not src.exists():
        print(f"  ⚠ {name} — 來源不存在，跳過")
        return "skipped"

    existed = dst.exists()
    try:
        if dry_run:
            tag = "♻ 將清除舊備份 → " if existed else ""
            print(f"  🔍 {tag}{name} → {dst}")
            return "success"

        if existed:
            shutil.rmtree(dst)

        shutil.copytree(src, dst)
        tag = "♻" if existed else "✅"
        extra = "（已清除舊備份）" if existed else ""
        print(f"  {tag} {name}{extra} → {dst}")
        return "success"
    except Exception as e:
        print(f"  ❌ {name} — {e}")
        return "failed"


def main():
    parser = argparse.ArgumentParser(description="技能同步工具")
    parser.add_argument("-s", "--skills", nargs="*", help="指定技能名稱（空格分隔），覆蓋預設全量同步")
    parser.add_argument("-r", "--reverse", action="store_true", help="反向同步：.agent/skills → .kiro/skills")
    parser.add_argument("-d", "--dry-run", action="store_true", help="預覽模式，不實際複製")
    args = parser.parse_args()

    if args.reverse:
        src_root, dst_root = AGENT_SKILLS, KIRO_SKILLS
        direction = ".agent/skills → .kiro/skills"
    else:
        src_root, dst_root = KIRO_SKILLS, AGENT_SKILLS
        direction = ".kiro/skills → .agent/skills"

    skills = get_skill_list(args, src_root)
    if not skills:
        print(f"⚠ 來源目錄 {src_root} 不存在或為空")
        return

    mode = "（預覽模式）" if args.dry_run else ""
    source = "指定技能" if args.skills else "全部技能"
    print(f"🔄 技能同步開始{mode}（{direction}）— {source}\n")

    counts = {"success": 0, "skipped": 0, "failed": 0}
    for name in skills:
        result = sync_one(name, src_root, dst_root, args.dry_run)
        counts[result] += 1

    print(f"\n{'─' * 40}")
    print(f"📊 同步完成：成功 {counts['success']} / 跳過 {counts['skipped']} / 失敗 {counts['failed']}")


if __name__ == "__main__":
    main()
