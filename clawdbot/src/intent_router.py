import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 作者: paddyyang
# 最後修改日期: 2026-03-11

class ClawdBrain:
    def __init__(self, env_path=None):
        # 預設搜尋路徑向上跳兩級尋找根目錄的 .env
        if env_path is None:
            env_path = os.path.join(os.path.dirname(__file__), "../../.env")
            
        load_dotenv(env_path)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(f"❌ 錯誤: 在 {os.path.abspath(env_path)} 中缺少 GOOGLE_API_KEY")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

    def classify_intent(self, user_input):
        """
        核心任務：判斷意圖並識別 URL。
        """
        print(f"🧠 [Brain] 正在分析意圖: {user_input[:20]}...")
        
        system_prompt = """
        Role: Intelligent Intent Router
        Task: Analyze the user's input and categorize it as either 'RESEARCH' or 'CASUAL'.
        
        Criteria:
        - RESEARCH: If the user provides a URL or asks to analyze/crawl a specific link.
        - CASUAL: General greetings, chit-chat, or questions that don't involve a URL.
        
        Constraint: 
        Your output MUST be a valid JSON object with 'intent' and 'url' fields.
        Example 1: {"intent": "RESEARCH", "url": "https://example.com"}
        Example 2: {"intent": "CASUAL", "url": null}
        """

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
        )
        
        try:
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"⚠️ [Brain Warning] JSON 解析失敗: {e}")
            return {"intent": "CASUAL", "url": None}

    def summarize_content(self, content_md, url=""):
        """
        核心任務：將獵取到的內容進行結構化摘要，並使用繁體中文。
        """
        print(f"🔬 [Brain] 正在生成內容摘要...")
        
        prompt = f"""
        請針對以下 Markdown 內容進行專業摘要。
        要求：
        1. 使用繁體中文 (Traditional Chinese)。
        2. 採用結構化列表。
        3. 如果有數據或關鍵結論，請使用類似腳註 [1] 的方式標註來源（參考自網址：{url}）。
        
        內容：
        {content_md[:10000]} 
        """

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        
        return response.text

    def chat(self, user_input):
        """
        閒聊模式：直接以友善對話方式回應，不做摘要格式處理。
        """
        print(f"💬 [Brain] 閒聊模式回應...")
        
        prompt = f"""
        你是一個友善、輕鬆的 AI 助理，名叫 ClawdBot。
        請直接、簡潔地回應使用者的訊息，不要使用條列摘要格式。
        使用繁體中文回應。
        
        使用者說：{user_input}
        """
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        
        return response.text
if __name__ == "__main__":
    try:
        brain = ClawdBrain()
        
        # 測試 1: 意圖分類
        test_inputs = [
            "你好啊，今天天氣如何？",
            "幫我分析這篇文章：https://example.com"
        ]
        
        for inp in test_inputs:
            res = brain.classify_intent(inp)
            print(f"Input: {inp} => Result: {res}")
            
        # 測試 2: 摘要生成 (Mock 内容)
        mock_content = "# 遊戲開發趨勢\nAI 正在改變遊戲開發流程。透過使用代理人工作流，開發速度提升了 300%。"
        summary = brain.summarize_content(mock_content, "https://sample.com")
        print("\n--- 摘要測試 ---")
        print(summary)
        
    except Exception as e:
        print(e)
