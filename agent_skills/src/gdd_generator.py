import os
import datetime
from pathlib import Path
from google import genai
from dotenv import load_dotenv


def load_skill(skill_name):
    """從 .agent/skills/{skill_name}/SKILL.md 讀取技能定義"""
    project_root = Path(__file__).resolve().parent.parent.parent
    skill_path = project_root / ".agent" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        print(f"⚠️ 找不到技能定義：{skill_path}")
        return None
    content = skill_path.read_text(encoding="utf-8")
    print(f"  ✅ 已載入技能：.agent/skills/{skill_name}/SKILL.md")
    return content


def main(theme):
    # 載入根目錄 .env
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: Missing GOOGLE_API_KEY in .env")
        return

    client = genai.Client(api_key=api_key)
    MODEL = "models/gemini-2.5-flash-lite"

    # 載入技能定義
    print("📦 正在載入 .agent/skills/ 技能定義...")
    level_skill = load_skill("level-designer")
    character_skill = load_skill("character-creator")

    print(f"\n🚀 開始為主題「{theme}」生成 GDD...")

    # Step 1: Level Design (@level-designer)
    print("🧠 Step 1: 正在設計關卡與環境 (@level-designer)...")
    level_system = ""
    if level_skill:
        level_system = f"以下是你的技能定義，請嚴格遵循：\n\n{level_skill}\n\n"

    level_prompt = f"""{level_system}Role: Senior Level Designer（資深關卡設計師）
Task: 為遊戲關卡建立詳細的環境與挑戰概述。
Theme: {theme}
Guidelines:
- 描述核心環境氛圍（視覺風格、光線、色調）。
- 列出 3 個與主題高度相關的環境危險要素，每個需描述觸發條件與對玩家的影響。
- 說明玩家在此關卡的主要目標。
- 輸出必須為繁體中文。
Format: Markdown"""

    level_response = client.models.generate_content(model=MODEL, contents=level_prompt)
    level_info = level_response.text

    # Step 2: Character Design (@character-creator)
    print("👺 Step 2: 正在設計對應 Boss (@character-creator)...")
    char_system = ""
    if character_skill:
        char_system = f"以下是你的技能定義，請嚴格遵循：\n\n{character_skill}\n\n"

    boss_prompt = f"""{char_system}Role: Senior Character Creator（資深角色設計師）
Task: 設計與現有關卡環境完美契合的 Boss 角色。
Theme: {theme}
Existing Level Design Context:
{level_info}

Guidelines:
- Boss 的名稱與稱號。
- 描述 Boss 的能力，每個技能必須與上方環境危險要素互動。
- Boss 的敘事動機（為何出現在此環境）。
- 邏輯一致性：水下關卡不應出現火焰攻擊。
- 輸出必須為繁體中文。
Format: Markdown"""

    boss_response = client.models.generate_content(model=MODEL, contents=boss_prompt)
    boss_info = boss_response.text

    # Step 3: Global GDD Assembly
    print("📄 Step 3: 正在組裝 GDD 檔案...")
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    final_markdown = f"""# 🎮 遊戲設計文件 (GDD): {theme}

## 🧩 模組 1: 關卡與環境設計 (@level-designer)
{level_info}

---

## 🧩 模組 2: 角色與 Boss 設計 (@character-creator)
{boss_info}

---
*由 Antigravity GDD 生成器自動產生*
*技能來源：.agent/skills/level-designer, .agent/skills/character-creator*
*日期: {today_str}*
"""

    # 輸出至 reports/
    safe_theme = "".join(x for x in theme if x.isalnum() or x in " _-")
    output_filename = f"GDD_{safe_theme}_{today_str}.md"
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / "reports" / output_filename

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_markdown, encoding="utf-8")

    print(f"Generation SUCCESS: reports/{output_filename}")


if __name__ == "__main__":
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else "深海科研站"
    main(theme)
