"""
Gemini Canvas 通用儀表板產生器
讀取任意 JSON → 呼叫 Gemini API → 產出獨立 HTML 儀表板。

用法：
    py scripts/generate_canvas.py --input data.json
    py scripts/generate_canvas.py --input data.json --output dashboard.html --title "我的儀表板"

作者: paddyyang
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime


def find_env_file():
    """向上搜尋 tigerbot/.env 取得 GOOGLE_API_KEY"""
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        current = os.path.dirname(current)
        env_path = os.path.join(current, "tigerbot", ".env")
        if os.path.exists(env_path):
            return env_path
        # 也可能直接在 tigerbot 目錄下
        env_path2 = os.path.join(current, ".env")
        if os.path.exists(env_path2):
            return env_path2
    return None


def load_api_key():
    """從 .env 載入 GOOGLE_API_KEY"""
    # 先檢查環境變數
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    # 從 .env 檔案讀取
    env_path = find_env_file()
    if env_path:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GOOGLE_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None


def load_prompt_template():
    """讀取提詞模板"""
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "assets", "prompt_template.txt"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_html(text: str) -> str:
    """從 Gemini 回應中提取 HTML"""
    # 嘗試提取 ```html ... ``` 區塊
    match = re.search(r'```html\s*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 嘗試提取 <!DOCTYPE ... </html>
    match = re.search(r'(<!DOCTYPE html>.*?</html>)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 回傳原文（可能本身就是 HTML）
    return text.strip()


def generate_dashboard(input_path: str, output_path: str = None, title: str = None) -> str:
    """
    核心函式：讀取 JSON → 呼叫 Gemini → 產出 HTML。
    回傳輸出檔案路徑。
    """
    # 讀取 JSON
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 決定標題
    if not title:
        title = data.get("title", "Data Dashboard")

    # 決定輸出路徑
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_dashboard.html"

    # 載入 API Key
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("找不到 GOOGLE_API_KEY，請設定環境變數或 tigerbot/.env")

    # 組合 prompt
    template = load_prompt_template()
    data_str = json.dumps(data, ensure_ascii=False, indent=2)
    prompt = template.replace("{title}", title).replace("{data}", data_str)

    # 呼叫 Gemini API
    print(f"🤖 呼叫 Gemini API 產生儀表板...")
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    if not response.text:
        raise RuntimeError("Gemini API 回應為空")

    # 提取 HTML
    html = extract_html(response.text)

    # 寫入檔案
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 儀表板已產生: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Gemini Canvas 通用儀表板產生器")
    parser.add_argument("--input", required=True, help="JSON 資料檔案路徑")
    parser.add_argument("--output", default=None, help="HTML 輸出路徑")
    parser.add_argument("--title", default=None, help="儀表板標題")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 找不到檔案: {args.input}")
        sys.exit(1)

    try:
        output = generate_dashboard(args.input, args.output, args.title)
        print(f"📊 請在瀏覽器開啟: {output}")
    except Exception as e:
        print(f"❌ 產生失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
