import asyncio
from playwright.async_api import async_playwright
import subprocess
import time
import os
import sys

# 作者: paddyyang
# 最後修改日期: 2026-03-11

async def run_e2e_test():
    print("🧪 開始進行 E2E 全自動化測試...")
    
    # 1. 啟動後端服務
    python_exe = sys.executable
    server_script = os.path.join(os.path.dirname(__file__), "../src/server.py")
    server_process = subprocess.Popen([python_exe, server_script])
    
    time.sleep(3) # 等待伺服器啟動
    
    async with async_playwright() as p:
        # 啟動瀏覽器
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "http://127.0.0.1:8000/dashboard"
        print(f"🔍 正在存取: {url}")
        
        try:
            # 2. 測試連通性
            response = await page.goto(url)
            assert response.status == 200, f"無法存取頁面，狀態碼: {response.status}"
            print("✅ 頁面連通性驗證成功 (200 OK)")
            
            # 3. 測試 API 數據加載
            # 等待 Last Update 文字出現 (代表 fetchData 已執行)
            await page.wait_for_selector("#last-update")
            last_update_text = await page.inner_text("#last-update")
            assert "--:--:--" not in last_update_text, "數據加載失敗，更新時間未更新"
            print(f"✅ 數據連動驗證成功 (上次更新: {last_update_text})")
            
            # 4. 測試圖表渲染 (檢測 Canvas)
            canvas_count = await page.locator("canvas").count()
            assert canvas_count >= 2, f"圖表渲染失敗，Canvas 數量不足 ({canvas_count})"
            print(f"✅ 圖表渲染驗證成功 (偵測到 {canvas_count} 個圖表)")
            
            # 5. 測試異常預警邏輯 (檢測是否有 pulse-red 動畫)
            # 在 API 回傳隨機數據的情況下，我們不一定能捕捉到 Anomaly
            # 但可以檢查結構是否正確
            kpis = await page.locator("#kpi-grid > div").count()
            assert kpis == 4, f"KPI 卡片數量錯誤: {kpis}"
            print(f"✅ KPI 佈局驗證成功 (偵測到 {kpis} 個卡片)")
            
            print("\n🎉 所有測試案例通過！系統穩定。")
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
        finally:
            await browser.close()
            server_process.terminate()

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
