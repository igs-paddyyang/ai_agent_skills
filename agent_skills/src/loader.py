import os
from pathlib import Path
from dotenv import load_dotenv

# 載入根目錄 .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)


def scan_skills(base_path):
    """掃描 .agent/skills/ 下的所有技能（含 antigravity 子技能）"""
    skills_path = Path(base_path)
    if not skills_path.exists():
        print(f"❌ 錯誤: 找不到技能路徑 {skills_path}")
        return []

    print(f"🔍 開始掃描技能目錄: {skills_path}")
    skills = []

    for entry in skills_path.iterdir():
        if entry.is_dir() and not entry.name.startswith('.'):
            skill_md = entry / "SKILL.md"
            readme_file = entry / "README.md"
            config_file = entry / "skill.json"

            # 檢查是否為 antigravity 技能庫（含子技能）
            sub_skills_dir = entry / "skills"
            is_library = sub_skills_dir.exists() and sub_skills_dir.is_dir()

            skill_info = {
                "id": entry.name,
                "path": str(entry),
                "has_skill_md": skill_md.exists(),
                "has_readme": readme_file.exists(),
                "has_config": config_file.exists(),
                "is_library": is_library,
            }
            skills.append(skill_info)

            # 若為技能庫，掃描子技能
            if is_library:
                sub_count = 0
                for sub in sub_skills_dir.iterdir():
                    if sub.is_dir():
                        sub_count += 1
                skill_info["sub_skill_count"] = sub_count

    return skills


def load_skill_definition(skill_name, base_path=None):
    """載入指定技能的 SKILL.md 內容"""
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent.parent / ".agent" / "skills"
    skill_md = Path(base_path) / skill_name / "SKILL.md"
    if not skill_md.exists():
        return None
    return skill_md.read_text(encoding="utf-8")


def main():
    # 掃描 .agent/skills/ 下的頂層技能
    project_root = Path(__file__).resolve().parent.parent.parent
    skill_root = project_root / ".agent" / "skills"

    found_skills = scan_skills(skill_root)

    print(f"\n✅ 掃描完成! 共找到 {len(found_skills)} 個頂層技能。\n")

    # 分類顯示
    standalone = [s for s in found_skills if not s.get("is_library")]
    libraries = [s for s in found_skills if s.get("is_library")]

    if standalone:
        print("📋 獨立技能：")
        for s in standalone:
            icon = "🟢" if s["has_skill_md"] else "⚪"
            print(f"  {icon} {s['id']}")

    if libraries:
        print("\n📚 技能庫：")
        for s in libraries:
            count = s.get("sub_skill_count", 0)
            print(f"  📦 {s['id']} ({count} 個子技能)")


if __name__ == "__main__":
    main()
