"""設定模板 — START_BAT, SCHEDULES_JSON, ENV_EXAMPLE, REQUIREMENTS_TXT, INIT_DB_PY, BOT_TEST_GUIDE"""

# start.bat 模板（含 --with-scheduler）
START_BAT = '''@echo off
chcp 65001 >nul
echo ============================
echo   ArkBot 一鍵啟動
echo ============================

REM 讀取 .env 中的 WEB_PORT
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="WEB_PORT" set WEB_PORT=%%b
)
if not defined WEB_PORT set WEB_PORT=2141

echo [0/3] 檢查並安裝套件...
py -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ❌ 套件安裝失敗，請檢查 requirements.txt
    pause
    exit /b 1
)

echo [1/3] 初始化資料庫...
py scripts/init_db.py

echo [2/3] 啟動 Web 伺服器 (port %WEB_PORT%)...
start "ArkBot-Web" cmd /c "cd /d %~dp0 && set PYTHONPATH=src && py -m uvicorn src.web_server:app --host 0.0.0.0 --port %WEB_PORT%"

timeout /t 2 /nobreak >nul

echo [3/3] 啟動 Telegram Bot...
start "ArkBot-Bot" cmd /c "cd /d %~dp0 && py src/bot_main.py"

REM 排程引擎（可選）
if "%1"=="--with-scheduler" (
    echo [+] 啟動排程引擎...
    start "ArkBot-Scheduler" cmd /c "cd /d %~dp0 && set PYTHONPATH=src && py src/scheduler.py"
    echo    Scheduler: 已啟動
)

echo.
echo ✅ 服務已啟動！
echo    Web: http://localhost:%WEB_PORT%
echo    Bot: Telegram polling
echo    Scheduler: %1
echo.
pause
'''

# schedules.json 模板
SCHEDULES_JSON = '''{
  "schedules": [
    {
      "id": "daily-revenue",
      "skill_id": "dashboard",
      "input": "產生昨日的營收分析儀表板",
      "cron": "0 9 * * *",
      "enabled": true,
      "description": "每日 09:00 產生營收儀表板"
    },
    {
      "id": "daily-revenue-notify",
      "skill_id": "notify",
      "input": "data/dashboard/revenue/",
      "cron": "5 9 * * *",
      "enabled": false,
      "description": "每日 09:05 發送營收通報",
      "params": {"route": "daily_revenue"}
    }
  ]
}'''


# .env.example 模板
ENV_EXAMPLE = """# ArkBot 環境變數
GOOGLE_API_KEY=your-gemini-api-key-here
TELEGRAM_TOKEN=your-telegram-bot-token-here
DATABASE_PATH=data/brain.db
WEB_PORT=2141
SKILL_API_KEY=your-skill-api-key-here

# 如果需要代理才能連到 Telegram API，取消下面的註解並填入你的代理地址
# HTTPS_PROXY=http://127.0.0.1:7890
"""

# requirements.txt 模板
REQUIREMENTS_TXT = """python-telegram-bot>=20.0
google-genai>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
markdownify>=0.11.0
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
websockets>=12.0
croniter>=1.4.0
"""

# scripts/init_db.py 模板
INIT_DB_PY = '''#!/usr/bin/env python3
"""資料庫初始化腳本"""
import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv

# 以專案根目錄（scripts/ 的上一層）為基準
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

db_path = os.getenv("DATABASE_PATH", "data/brain.db")
if not os.path.isabs(db_path):
    db_path = str(PROJECT_ROOT / db_path)
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS raw_crawls (
    url TEXT UNIQUE NOT NULL,
    content_md TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    is_star BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print(f"✅ 資料庫已初始化：{db_path}")
'''


# docs/bot_test_guide.md 模板（8 大測試案例）
BOT_TEST_GUIDE = r'''# ArkBot 對話測試指南

## 案例 1：Web 對話介面
- **操作**：瀏覽器開啟 `http://localhost:2141`
- **預期**：顯示 Web 對話頁面，右上角狀態顯示「🟢 已連線」

## 案例 2：初始化測試
- **操作**：在 Telegram 發送 `/start`
- **預期**：顯示歡迎訊息，無 BadRequest 錯誤

## 案例 3：閒聊模式
- **操作**：發送「你好，今天天氣如何？」
- **預期**：友善的對話回覆，不是條列式摘要格式
- **路由**：Intent Router → CASUAL 快速路徑 → brain.chat() 直接回覆

## 案例 4：研究意圖測試
- **操作**：發送 `https://example.com`
- **預期**：依序顯示「🧠 正在思考...」→「⚙️ 執行 Skill：crawler...」→ 結構化摘要
- **路由**：Intent Router → RESEARCH → Skill Resolver → crawler Skill → Executor

## 案例 5：快取驗證
- **操作**：再次發送同一個 URL
- **預期**：回應速度明顯加快（從快取讀取）

## 案例 6：儀表板（對話觸發）

### 6a：營收分析儀表板
- **資料來源**：`preprocessed_bklog.DailyUserInfoSnapshot`
- **範例 JSON**：`data/dashboard/revenue/sample.json`
- **操作**：在對話中發送：
  ```
  幫我用 data/dashboard/revenue/sample.json 產生營收分析儀表板
  ```
  或帶入日期（預設昨日）：
  ```
  產生 2026-03-18 的營收分析儀表板
  ```
- **預期**：
  1. 路由：Intent Router → DASHBOARD → Skill Resolver → dashboard Skill → Executor（async 模式）
  2. 產出包含 KPI 卡片（活躍玩家、押注、贏分、GGR%、儲值、ARPU）
  3. 7 日趨勢圖（daily_bet / daily_win / active_users）
  4. 國家分佈圓餅圖 + VIP 等級分佈表
  5. 儀表板存入 `data/dashboard/dashboard_YYYYMMDD_HHMMSS.html`

### 6b：老虎機分析儀表板
- **資料來源**：`bklog.SessionBetWinLog`
- **範例 JSON**：`data/dashboard/slots/sample.json`
- **操作**：
  ```
  幫我用 data/dashboard/slots/sample.json 產生老虎機分析儀表板
  ```
- **預期**：
  1. 意圖分類為 `DASHBOARD`
  2. 產出包含 KPI 卡片（場次數、押注、贏分、RTP、平均每轉押注、活躍玩家）
  3. 7 日趨勢圖 + Top 10 遊戲排行表（含 RTP）
  4. 國家分佈 + VIP 等級分佈

### 6c：魚機分析儀表板
- **資料來源**：`bklog.SessionTigerSharkBetWinLog`
- **範例 JSON**：`data/dashboard/fish/sample.json`
- **操作**：
  ```
  幫我用 data/dashboard/fish/sample.json 產生魚機分析儀表板
  ```
- **預期**：
  1. 意圖分類為 `DASHBOARD`
  2. 產出包含 KPI 卡片（場次數、押注、贏分、RTP、活躍玩家、場均押注）
  3. 7 日趨勢圖 + Top 遊戲排行表（含 RTP）
  4. 國家分佈 + VIP 等級分佈

### 6d：瀏覽器直接查看
- **操作**：瀏覽器開啟 `http://localhost:2141/dashboard`
- **預期**：顯示最新的儀表板 HTML（若尚未產生則顯示提示頁面）

## 案例 7：Skill API（外部呼叫）

### 7a：列出所有 Skill
```bash
curl -H "X-API-Key: <your-api-key>" http://localhost:2141/api/skills
```
- **預期**：回傳 JSON 含 `skills` 陣列（dashboard / crawler / chat），`count: 3`

### 7b：直接執行 Chat Skill
```bash
curl -X POST http://localhost:2141/api/skill/chat \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"你好\"}"
```
- **預期**：`{"success": true, "skill_id": "chat", "result": "...", "execution_time_ms": ...}`

### 7c：直接執行 Dashboard Skill
```bash
curl -X POST http://localhost:2141/api/skill/dashboard \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d "{\"input\": \"產生營收儀表板\"}"
```
- **預期**：`success: true`，result 含 html_path 和 summary

### 7d：無效 Skill ID
- **預期**：HTTP 404，`detail: "Skill 'nonexist' 不存在"`

### 7e：無 API Key
- **預期**：HTTP 401，`detail: "無效的 API Key"`

### 7f：Swagger UI
- **操作**：瀏覽器開啟 `http://localhost:2141/docs`
- **預期**：顯示 FastAPI 自動產生的 API 文件

## 案例 8：排程系統（Scheduler）

### 8a：Dry-run 模式
```bash
py src/scheduler.py --dry-run
```
- **預期**：列出預設排程，顯示下次執行時間，不實際執行

### 8b：排程引擎啟動
```bash
py src/scheduler.py
```
- **預期**：log 顯示「排程引擎啟動」，每 60 秒檢查一次

### 8c：一鍵啟動含排程
```bash
start.bat --with-scheduler
```
- **預期**：Web + Telegram + Scheduler 三個視窗同時啟動
'''


# ═══ Telegram 路由設定模板 ═══

TELEGRAM_CONFIG_JSON = '''{
  "telegram": {
    "bot_token": "${TELEGRAM_TOKEN}",
    "polling_enabled": false,
    "parse_mode": "Markdown",

    "admin": {
      "chat_id": "",
      "name": "Admin",
      "description": "管理員私訊通報"
    },

    "group": {
      "chat_id": "",
      "name": "",
      "description": "主群組（Forum 模式，含 Topics）",
      "topics": {}
    },

    "additional_groups": {},

    "notify_routes": {
      "default": {
        "targets": [
          { "type": "admin" }
        ],
        "description": "預設通報路由"
      }
    }
  }
}'''


# ═══ ArkAgent OS 設定模板 ═══

# ArkAgent start.bat（一鍵啟動：安裝套件 → 初始化 DB → py main.py）
ARKAGENT_START_BAT = '''@echo off
chcp 65001 >nul
echo ============================
echo   ArkAgent OS Launcher
echo ============================

echo [1/3] 檢查並安裝套件...
py -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo [FAIL] 套件安裝失敗，請檢查 requirements.txt
    pause
    exit /b 1
)

echo [2/3] 初始化資料庫...
py scripts/init_db.py

echo [3/3] 啟動服務（Web + Telegram + Scheduler）...
py main.py
'''

# ArkAgent .env.example
ARKAGENT_ENV_EXAMPLE = """# ArkAgent OS 環境變數
GOOGLE_API_KEY=your-gemini-api-key-here
TELEGRAM_TOKEN=your-telegram-bot-token-here
DATABASE_PATH=data/brain.db
WEB_PORT=2141
SKILL_API_KEY=your-skill-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# 如果需要代理才能連到 Telegram API，取消下面的註解並填入你的代理地址
# HTTPS_PROXY=http://127.0.0.1:7890
"""

# ArkAgent requirements.txt
ARKAGENT_REQUIREMENTS_TXT = """python-telegram-bot>=20.0
google-genai>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
markdownify>=0.11.0
python-dotenv>=1.0.0
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
websockets>=12.0
croniter>=1.4.0
pyyaml>=6.0
jsonschema>=4.20.0
"""
