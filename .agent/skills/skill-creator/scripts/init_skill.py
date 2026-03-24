#!/usr/bin/env python3
"""
技能初始化器 — 從範本建立新技能

用法：
    python scripts/init_skill.py <skill-name> --path <path>

範例：
    python scripts/init_skill.py my-new-skill --path .kiro/skills
"""

import sys
from datetime import date
from pathlib import Path

# 預設範本路徑（相對於此腳本）
TEMPLATE_DIR = Path(__file__).parent.parent / 'templates'
DEFAULT_TEMPLATE = TEMPLATE_DIR / 'default.md'
README_TEMPLATE = TEMPLATE_DIR / 'readme.md'


def title_case_skill_name(skill_name):
    """將 kebab-case 技能名稱轉換為標題大小寫。"""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def load_template(template_path=None):
    """載入範本檔案。"""
    path = template_path or DEFAULT_TEMPLATE
    if path.exists():
        return path.read_text(encoding='utf-8')
    # 內建 fallback 範本（僅 SKILL.md）
    return """---
name: {{SKILL_NAME}}
author: paddyyang
description: "[待完成：說明此技能的功能與使用時機]"
---

# {{SKILL_TITLE}}

## 概述

[待完成：說明此技能能做什麼]
"""


def init_skill(skill_name, path):
    """初始化新技能目錄並套用範本 SKILL.md。"""
    skill_dir = Path(path).resolve() / skill_name

    if skill_dir.exists():
        print(f"❌ 錯誤：技能目錄已存在：{skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ 已建立技能目錄：{skill_dir}")
    except Exception as e:
        print(f"❌ 建立目錄時發生錯誤：{e}")
        return None

    # 共用替換變數
    skill_title = title_case_skill_name(skill_name)
    today = date.today().strftime('%Y-%m-%d')
    replacements = {
        '{{SKILL_NAME}}': skill_name,
        '{{SKILL_TITLE}}': skill_title,
        '{{CREATED_DATE}}': today,
        '{{SKILL_DESCRIPTION}}': '[待完成：一句話說明此技能的功能]',
    }

    def apply_replacements(text):
        for key, val in replacements.items():
            text = text.replace(key, val)
        return text

    # 從範本建立 SKILL.md
    template = load_template()
    skill_content = apply_replacements(template)

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content, encoding='utf-8')
        print("✅ 已建立 SKILL.md")
    except Exception as e:
        print(f"❌ 建立 SKILL.md 時發生錯誤：{e}")
        return None

    # 從範本建立 README.md（含版本號）
    readme_template = load_template(README_TEMPLATE)
    if readme_template:
        readme_content = apply_replacements(readme_template)
        readme_path = skill_dir / 'README.md'
        try:
            readme_path.write_text(readme_content, encoding='utf-8')
            print("✅ 已建立 README.md（v0.1.0）")
        except Exception as e:
            print(f"❌ 建立 README.md 時發生錯誤：{e}")

    # 建立資源目錄
    try:
        for subdir in ['scripts', 'references', 'assets']:
            (skill_dir / subdir).mkdir(exist_ok=True)
        print("✅ 已建立 scripts/、references/、assets/ 目錄")
    except Exception as e:
        print(f"❌ 建立資源目錄時發生錯誤：{e}")
        return None

    print(f"\n✅ 技能 '{skill_name}' 已成功初始化於 {skill_dir}")
    print("\n後續步驟：")
    print("1. 編輯 SKILL.md 完成待辦項目並更新描述")
    print("2. 編輯 README.md 補充功能說明與使用方式")
    print("3. 自訂或刪除 scripts/、references/、assets/ 中的範例檔案")
    print("4. 執行 quick_validate.py 檢查技能結構")

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--path':
        print("用法：python scripts/init_skill.py <skill-name> --path <path>")
        print("\n技能名稱要求：")
        print("  - kebab-case（例如 'data-analyzer'）")
        print("  - 僅限小寫字母、數字與連字號")
        print("  - 最多 64 字元")
        print("\n範例：")
        print("  python scripts/init_skill.py my-new-skill --path .kiro/skills")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    print(f"🚀 正在初始化技能：{skill_name}")
    print(f"   位置：{path}")
    print()

    result = init_skill(skill_name, path)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
