import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import random
import time

# 作者: paddyyang
# 最後修改日期: 2026-03-11

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

class ClawdCrawler:
    def __init__(self, db_path=None):
        # 確保在獨立腳本運行時也能載入環境變數
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
        if os.path.exists(env_path):
            from dotenv import load_dotenv
            load_dotenv(env_path)
            
        if db_path is None:
            # 優先從環境變數讀取，否則預設為 brain.db
            db_path = os.getenv("DATABASE_PATH", "clawdbot/data/brain.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # 確保資料庫路徑正確（相對於專案根目錄解析）
        if not os.path.isabs(self.db_path):
            # 腳本位在 d:/Project/2026/ai_agent/clawdbot/src/
            # 專案根目錄在 ../../
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
            self.db_path = os.path.join(base_dir, self.db_path)

    def fetch_and_save(self, url):
        """
        核心獵取邏輯：快取優先 (Cache First) -> 網路獵取 -> 存儲 -> 回傳
        """
        # 1. 檢查快取
        cached_content = self._check_cache(url)
        if cached_content:
            print(f"📦 [Cache Hit] 發現快取內容: {url}")
            return cached_content, True

        # 2. 網路獵取
        print(f"🕸️ [Web Pull] 正在獵取新內容: {url}")
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            # 加入 verify=False 解決部分環境 SSL 報錯問題
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            # 自動偵測編碼
            response.encoding = response.apparent_encoding
            html_content = response.text
            
            # 3. 解析與轉換
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 獲取標題
            title = soup.title.string if soup.title else "無標題"
            
            # 清理不必要的標籤 (腳本, 樣式, 導航等)
            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.decompose()
            
            # 轉換為 Markdown
            markdown_text = md(str(soup), heading_style="ATX")
            
            # 4. 存儲到資料庫
            self._save_to_db(url, title, markdown_text)
            
            return markdown_text, False

        except requests.exceptions.RequestException as e:
            print(f"❌ [Error] 獵取失敗: {e}")
            return f"Error: 獵取失敗 - {str(e)}", False

    def _check_cache(self, url):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content_md FROM raw_crawls WHERE url = ?", (url,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def _save_to_db(self, url, title, content_md):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO raw_crawls (url, title, content_md) VALUES (?, ?, ?)", 
                           (url, title, content_md))
            conn.commit()
            conn.close()
            print(f"💾 [Saved] 內容已存入資料庫")
        except Exception as e:
            print(f"⚠️ [DB Warning] 存儲時發生錯誤: {e}")

if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    
    crawler = ClawdCrawler()
    content, is_cache = crawler.fetch_and_save(test_url)
    
    print("-" * 30)
    print(f"標題測試: {content[:100]}...")
    print("-" * 30)
    if is_cache:
        print("💡 驗證成果: 成功從快取讀取。")
    else:
        print("💡 驗證成果: 成功從網路獵取並存儲。")
