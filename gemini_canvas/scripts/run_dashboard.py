import subprocess
import time
import webbrowser
import os
import sys

# 作者: paddyyang
# 最後修改日期: 2026-03-11

def run():
    print("🚀 正在啟動 Gemini Canvas 數據儀表板...")
    
    # 獲取 Python 路徑
    python_exe = sys.executable
    server_script = os.path.join(os.path.dirname(__file__), "../src/server.py")
    
    # 啟動 FastAPI 服務
    process = subprocess.Popen([python_exe, server_script])
    
    print("⏳ 等待伺服器啟動...")
    time.sleep(3)  # 等待 3 秒確保伺服器就緒
    
    # 打開預覽頁面
    url = "http://127.0.0.1:8000/dashboard"
    print(f"🌐 正在打開瀏覽器預覽: {url}")
    webbrowser.open(url)
    
    try:
        print("\n✅ 儀表板已運行。按下 Ctrl+C 可停止服務。")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在停止服務...")
        process.terminate()
        print("👋 已關閉。")

if __name__ == "__main__":
    run()
