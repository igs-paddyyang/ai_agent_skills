#!/usr/bin/env python3
"""
技能打包器 — 將技能資料夾打包為可分發的 .skill 檔案

用法：
    py scripts/package_skill.py <path/to/skill-folder> [output-directory]

範例：
    py scripts/package_skill.py .agent/skills/my-skill
    py scripts/package_skill.py .agent/skills/my-skill ./dist
"""

import sys
import zipfile
from pathlib import Path
from quick_validate import validate_skill


def package_skill(skill_path, output_dir=None):
    """
    將技能資料夾打包為 .skill 檔案。

    參數：
        skill_path: 技能資料夾路徑
        output_dir: 選用的 .skill 檔案輸出目錄（預設為當前目錄）

    回傳：
        建立的 .skill 檔案路徑，錯誤時回傳 None
    """
    skill_path = Path(skill_path).resolve()

    if not skill_path.exists():
        print(f"❌ 錯誤：找不到技能資料夾：{skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"❌ 錯誤：路徑不是目錄：{skill_path}")
        return None

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ 錯誤：在 {skill_path} 中找不到 SKILL.md")
        return None

    # 打包前先執行驗證
    print("🔍 正在驗證技能...")
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"❌ 驗證失敗：{message}")
        print("   請先修正驗證錯誤再進行打包。")
        return None
    print(f"{message}\n")

    # 決定輸出位置
    skill_name = skill_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    skill_filename = output_path / f"{skill_name}.skill"

    # 建立 .skill 檔案（zip 格式）
    try:
        with zipfile.ZipFile(skill_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill_path.parent)
                    zipf.write(file_path, arcname)
                    print(f"  已加入：{arcname}")

        print(f"\n✅ 技能已成功打包至：{skill_filename}")
        return skill_filename

    except Exception as e:
        print(f"❌ 建立 .skill 檔案時發生錯誤：{e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法：py scripts/package_skill.py <path/to/skill-folder> [output-directory]")
        print("\n範例：")
        print("  py scripts/package_skill.py .agent/skills/my-skill")
        print("  py scripts/package_skill.py .agent/skills/my-skill ./dist")
        sys.exit(1)

    skill_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"📦 正在打包技能：{skill_path}")
    if output_dir:
        print(f"   輸出目錄：{output_dir}")
    print()

    result = package_skill(skill_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
