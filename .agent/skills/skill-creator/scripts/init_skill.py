#!/usr/bin/env python3
"""
技能初始化器 — 從範本建立新技能

用法：
    py scripts/init_skill.py <skill-name> --path <path>

範例：
    py scripts/init_skill.py my-new-skill --path .agent/skills
    py scripts/init_skill.py my-api-helper --path .agent/skills
"""

import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: "[待完成：完整說明此技能的功能與使用時機。包含觸發情境、檔案類型或任務。]"
---

# {skill_title}

## 概述

[待完成：1-2 句說明此技能能做什麼]

## 結構建議

[待完成：選擇最適合此技能用途的結構。常見模式：

**1. 工作流程型**（適合循序流程）
- 有明確的步驟式程序時效果最佳
- 結構：## 概述 → ## 工作流程決策樹 → ## 步驟 1 → ## 步驟 2...

**2. 任務型**（適合工具集合）
- 技能提供不同操作/功能時效果最佳
- 結構：## 概述 → ## 快速開始 → ## 任務類別 1 → ## 任務類別 2...

**3. 參考/指引型**（適合標準或規範）
- 品牌指引、編碼標準或需求規範時效果最佳
- 結構：## 概述 → ## 指引 → ## 規範 → ## 用法...

**4. 能力型**（適合整合系統）
- 技能提供多個相互關聯的功能時效果最佳
- 結構：## 概述 → ## 核心能力 → ### 1. 功能 → ### 2. 功能...

模式可混合搭配。完成後請刪除此「結構建議」章節。]

## [待完成：依據選擇的結構替換為第一個主要章節]

[待完成：在此加入內容]

## 資源

### scripts/
可直接執行的程式碼（Python/Bash 等）。

### references/
載入上下文的文件與參考資料。

### assets/
不載入上下文，但用於輸出的檔案（範本、圖片等）。

---

**不需要的目錄可以刪除。** 並非每個技能都需要全部三種資源。
"""


def title_case_skill_name(skill_name):
    """將連字號技能名稱轉換為標題大小寫。"""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def init_skill(skill_name, path):
    """
    初始化新技能目錄並套用範本 SKILL.md。

    參數：
        skill_name: 技能名稱
        path: 技能目錄的建立路徑

    回傳：
        建立的技能目錄路徑，錯誤時回傳 None
    """
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

    # 從範本建立 SKILL.md
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content, encoding='utf-8')
        print("✅ 已建立 SKILL.md")
    except Exception as e:
        print(f"❌ 建立 SKILL.md 時發生錯誤：{e}")
        return None

    # 建立資源目錄
    try:
        for subdir in ['scripts', 'references', 'examples']:
            (skill_dir / subdir).mkdir(exist_ok=True)
        print("✅ 已建立 scripts/、references/、examples/ 目錄")
    except Exception as e:
        print(f"❌ 建立資源目錄時發生錯誤：{e}")
        return None

    print(f"\n✅ 技能 '{skill_name}' 已成功初始化於 {skill_dir}")
    print("\n後續步驟：")
    print("1. 編輯 SKILL.md 完成待辦項目並更新描述")
    print("2. 自訂或刪除 scripts/、references/、examples/ 中的範例檔案")
    print("3. 準備好後執行驗證器檢查技能結構")

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--path':
        print("用法：py scripts/init_skill.py <skill-name> --path <path>")
        print("\n技能名稱要求：")
        print("  - 連字號命名（例如 'data-analyzer'）")
        print("  - 僅限小寫字母、數字與連字號")
        print("  - 最多 40 字元")
        print("\n範例：")
        print("  py scripts/init_skill.py my-new-skill --path .agent/skills")
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
