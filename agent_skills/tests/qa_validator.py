import os
from google import genai
from dotenv import load_dotenv

def validate_gdd(file_path: str, theme: str = "") -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: Missing GOOGLE_API_KEY")
        return

    client = genai.Client(api_key=api_key)
    MODEL = "models/gemini-2.5-flash-lite"

    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"🔍 正在對「{file_path}」進行一致性校核...")

    audit_prompt = f"""
    Role: Professional Game Design Auditor
    Task: Audit the following Game Design Document (GDD) for logical consistency and professional depth.

    GDD Content:
    {content}

    Checklist:
    1. Environmental Consistency: Are the hazards and boss abilities appropriate for the theme? (e.g., No fire bosses in underwater labs unless specifically justified).
    2. Narrative Logic: Does the Boss's motivation align with the level's objective?
    3. Technical Depth: Are the mechanics described in a way that a developer could implement?
    4. Language: Is the output in high-quality Traditional Chinese (繁體中文)?

    Format: Provide a score (1-10) for each point and a brief 'Verdict' in Traditional Chinese.
    """

    response = client.models.generate_content(model=MODEL, contents=audit_prompt)
    
    from datetime import date
    today = date.today().isoformat()
    safe_theme = theme if theme else "unknown"
    report_filename = f"qa_analysis_{safe_theme}_{today}.md"
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    report_path = os.path.join(project_root, "reports", report_filename)
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🛡️ GDD 品質校準與一致性分析報告\n\n")
        f.write(f"**分析對象：** `{file_path}`\n")
        f.write(f"**分析日期：** {today}\n\n")
        f.write("## ⚖️ AI 審計結果\n")
        f.write(response.text)
        f.write("\n\n---\n*Verified by AI Agent Skills Workshop QA*")

    print(f"✅ QA Analysis Complete: reports/{report_filename}")

def find_latest_gdd(theme: str) -> str | None:
    """在 agent_skills/reports/ 下搜尋指定主題最新的 GDD 檔案"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    reports_dir = os.path.join(project_root, "reports")
    if not os.path.exists(reports_dir):
        return None
    matches = sorted(
        [f for f in os.listdir(reports_dir) if f.startswith(f"GDD_{theme}") and f.endswith(".md")],
        reverse=True
    )
    return os.path.join(reports_dir, matches[0]) if matches else None


if __name__ == "__main__":
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else "深海科研站"
    gdd_path = find_latest_gdd(theme)
    if gdd_path:
        validate_gdd(gdd_path, theme=theme)
    else:
        print(f"❌ Error: 在 agent_skills/reports/ 下找不到主題「{theme}」的 GDD 檔案。")
        print(f"   請先執行: py agent_skills/src/gdd_generator.py \"{theme}\"")
