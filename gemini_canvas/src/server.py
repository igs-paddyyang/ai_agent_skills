import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import json
import random
import os

# 作者: paddyyang
# 最後修改日期: 2026-03-11

app = FastAPI(title="Gemini Canvas Data Provider")

# 數據契約 (Data Models)
class DashboardData(BaseModel):
    kpi_cards: List[dict]
    trend_data: List[dict]
    category_ratio: List[dict]
    recent_transactions: List[dict]

# 靜態數據檔案路徑
DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/data.json")

# 從 data.json 讀取靜態數據
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 模擬數據產生器（隨機模式）
def generate_mock_data():
    return {
        "kpi_cards": [
            {"title": "今日活躍用戶", "value": f"{random.randint(1000, 5000)}", "trend": "+12%", "color": "blue"},
            {"title": "總營收", "value": f"${random.randint(50000, 100000)}", "trend": "+5%", "color": "green"},
            {"title": "轉換率", "value": f"{random.uniform(2.5, 5.0):.1f}%", "trend": "-1%", "color": "purple"},
            {"title": "異常率", "value": f"{random.uniform(0.1, 8.0):.1f}%", "trend": "+0.5%", "color": "red"},
        ],
        "trend_data": [
            {"date": f"03-{i:02d}", "users": random.randint(200, 1000), "revenue": random.randint(5000, 15000)}
            for i in range(1, 11)
        ],
        "category_ratio": [
            {"name": "遊戲研發", "value": 45},
            {"name": "自動化工具", "value": 30},
            {"name": "AI 助手", "value": 15},
            {"name": "其他", "value": 10},
        ],
        "recent_transactions": [
            {"id": f"TX{1000+i}", "user": f"User_{i}", "amount": f"${random.randint(50, 500)}", "status": random.choice(["成功", "處理中", "失敗"])}
            for i in range(1, 6)
        ]
    }

# API 接口
@app.get("/api/data", response_model=DashboardData)
async def get_dashboard_data(mock: bool = Query(False, description="啟用隨機模擬模式")):
    """
    提供結構化的 JSON 數據接口。
    預設從 data/data.json 讀取靜態數據；加上 ?mock=true 啟用隨機模式。
    """
    if mock:
        return generate_mock_data()
    return load_data()

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """
    導向至 Dashboard 預覽頁面。
    目前回傳基礎 HTML 佔位符，待 Phase 2/3 生成正式 index.html。
    """
    html_path = os.path.join(os.path.dirname(__file__), "../web/index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    
    return """
    <html>
        <head><title>Gemini Canvas placeholder</title></head>
        <body style="display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif; background:#f0f2f5;">
            <div style="text-align:center; padding:40px; background:white; border-radius:12px; shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);">
                <h1 style="color:#1a73e8;">🚀 Canvas 準備中</h1>
                <p>FastAPI 數據源已就緒 (/api/data)</p>
                <p style="color:#666;">等待 Phase 2 生成正式 index.html ...</p>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
