import os
from google import genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("❌ 錯誤: 請先在 .env 中填寫您的 GOOGLE_API_KEY。")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        
        print("🚀 正在啟動 API 預熱測試...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="你好! 請用兩句話回覆，測試 API 是否連通正常。"
        )
        
        print(f"\n✅ 測試成功! 回覆內容:\n{response.text}")
        return True
    
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    main()
