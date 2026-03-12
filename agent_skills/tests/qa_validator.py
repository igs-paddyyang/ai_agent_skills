import os
from google import genai
from dotenv import load_dotenv

def validate_gdd(file_path):
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: Missing GOOGLE_API_KEY")
        return

    client = genai.Client(api_key=api_key)
    MODEL = "gemini-2.0-flash"

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
    
    report_filename = f"qa_analysis_report_2026-03-11.md"
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    report_path = os.path.join(project_root, "reports", report_filename)
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🛡️ GDD 品質校準與一致性分析報告\n\n")
        f.write(f"**分析對象：** `{file_path}`\n")
        f.write(f"**分析日期：** 2026-03-11\n\n")
        f.write("## ⚖️ AI 審計結果\n")
        f.write(response.text)
        f.write("\n\n---\n*Verified by Antigravity QA Suite*")
 
    print(f"✅ QA Analysis Complete: reports/{report_filename}")

if __name__ == "__main__":
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else "深海科研站"
    safe_theme = "".join(x for x in theme if x.isalnum() or x in " _-")
    validate_gdd(f"antigravity-awesome-skills/docs/{safe_theme}.md")
