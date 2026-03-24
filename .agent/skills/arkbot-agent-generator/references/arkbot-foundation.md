# Foundation Layer 實作要點

本文件涵蓋 ArkBot Foundation Layer（基礎層）的實作細節。內容繼承自 `arkbot-generator` 的規格，針對 arkbot-agent-generator 的需求精煉。

---

## 1. 核心架構

三層架構，核心邏輯抽離讓兩個入口共用：

```
                    ┌─ bot_main.py (Telegram)
arkbot_core.py ────┤
                    └─ web_server.py (FastAPI + WebSocket)
```

`arkbot_core.py` 的 `process_message(user_input)` 封裝完整流程：意圖分類 → 爬取/快取 → 摘要/閒聊。以 async generator 回傳事件：
- `{"type": "status", "content": "🧠 正在思考..."}` — 狀態更新
- `{"type": "reply", "content": "最終回覆"}` — 最終結果
- `{"type": "dashboard", "content": "摘要文字", "html_path": "路徑"}` — 儀表板

## 2. 資料庫初始化（scripts/init_db.py）

建立 `brain.db`，包含：
- `raw_crawls`（url UNIQUE）— 存儲爬取原文
- `memories` — 存儲對話精華

所有路徑以 `PROJECT_ROOT` 為基準解析。

## 3. 爬蟲引擎（src/crawler_skill.py）

`requests` + `BeautifulSoup` + `markdownify`，快取優先邏輯：
- 先查 brain.db 是否已有該 URL
- 偽裝 User-Agent，處理 403/超時
- 成功後存入 raw_crawls

## 4. 意圖路由（src/intent_router.py）

`ArkBrain` 類別，四個方法、四個獨立 prompt，絕不混用：
- `classify_intent()` — 意圖分類，輸出 JSON
- `summarize_content()` — 研究型摘要（僅用於 RESEARCH）
- `chat()` — 閒聊型對話（僅用於 CASUAL）
- `extract_date()` — 日期提取

意圖分類 3 種：DASHBOARD > RESEARCH > CASUAL

意圖分類回傳結果與分支邏輯：
- `DASHBOARD`：通用儀表板（含 Canvas 儀表板產生）
- `RESEARCH`：研究型（含 URL 則爬取 + 摘要，無 URL 則 AI 回答）
- `CASUAL`：閒聊型（直接走 `chat()`）

意圖分類輸出格式：
```json
{
  "intent": "DASHBOARD | RESEARCH | CASUAL",
  "url": "string | null"
}
```

`extract_date(text)` 支援格式：
- `3/14`、`3-14` → 今年 3 月 14 日
- `3月14日`、`3月14號` → 今年 3 月 14 日
- `2026/3/14`、`2026-03-14` → 指定年月日
- `20260314` → 8 位數日期

## 5. Telegram 入口（src/bot_main.py）

消費 `process_message()` 的事件流：
- `_send_with_retry()` 指數退避重試 ConnectionError
- ReadTimeout 不重試
- `bootstrap_retries=5`
- 支援 `HTTPS_PROXY`

## 6. Web 入口（src/web_server.py + web/index.html）

FastAPI + WebSocket 即時對話：
- `/ws/chat` 端點接收使用者訊息
- `GET /canvas?file=xxx` — Canvas 儀表板 HTML 預覽

WebSocket 訊息協議：
```json
// 使用者 → 伺服器
{"type": "message", "content": "使用者輸入"}
// 伺服器 → 使用者
{"type": "status", "content": "狀態訊息"}
{"type": "reply", "content": "最終回覆"}
{"type": "dashboard_reply", "content": "摘要文字", "dashboard_url": "/dashboard?date=20260314"}
```

前端收到 `dashboard_reply` 時，渲染摘要文字並顯示「📊 開啟儀表板」按鈕（`target="_blank"` 開新分頁）。

前端自動 3 秒重連，伺服器端 catch `WebSocketDisconnect` 優雅處理。

## 7. MarkdownV2 跳脫（src/format_utils.py）

`escape_markdown_v2(text)` 處理動態內容。保留字元：`_ * [ ] ( ) ~ \` > # + - = | { } . !`

靜態字串必須手動預先跳脫。

## 8. 已知陷阱預防

| # | 陷阱 | 預防措施 |
|---|------|---------|
| 1 | MarkdownV2 跳脫 | 靜態字串預先跳脫，動態內容走 `escape_markdown_v2()` |
| 2 | Prompt 分離 | `summarize_content()` 和 `chat()` 使用獨立 prompt，casual 絕不呼叫 summarize |
| 3 | 路徑解析 | 所有模組用 `PROJECT_ROOT` 定位 `.env` 和 `brain.db` |
| 4 | Telegram 連線不穩定 | `_send_with_retry()` 指數退避；ReadTimeout 不重試 |
| 5 | WebSocket 斷線 | 前端自動 3 秒重連，伺服器端 catch disconnect |

## 9. 環境配置

`.env.example` 必須包含：
```
GOOGLE_API_KEY=your_api_key
TELEGRAM_TOKEN=your_telegram_token
WEB_PORT=2141
SKILL_API_KEY=your_skill_api_key
HTTPS_PROXY=                    # 選用
```

`requirements.txt` 必須包含：
```
fastapi
uvicorn
python-telegram-bot
google-genai
requests
beautifulsoup4
markdownify
croniter
```

## 10. 儀表板產生器（src/dashboard_skill.py）

`dashboard_skill.py` 是 src/ 核心模組，負責「JSON → Gemini API → HTML 儀表板」流程：

- `generate_dashboard_from_input(user_input)` — 協調器：解析輸入 → 決定 JSON 來源 → 處理日期 → 產出 HTML
- `generate_dashboard(json_path, title=None)` — 核心：讀取 JSON → 組合 prompt → 呼叫 Gemini → 提取 HTML → 存檔
- `detect_dashboard_type(user_input)` — 關鍵字匹配：revenue / slots / fish / general
- `get_sample_json(dashboard_type)` — 對應 `data/dashboard/sample_{type}.json`
- `parse_date(user_input)` — 日期提取（支援 `3/14`、`3月14日`、`2026-03-14`），預設昨日

回傳格式：`{"html_path": str, "summary": str}` 或 `{"error": str}`

Gemini client 延遲初始化，PROMPT_TEMPLATE 簡化自 `gemini-canvas-dashboard` 技能。產出的 HTML 存至 `data/dashboard/dashboard_{timestamp}.html`。

## 11. Skill Runtime 正式化

所有內建功能（爬蟲、儀表板、閒聊）已正式化為 Skill Package，放入 `skills/` 目錄：

```
skills/
├── crawler/     # 爬蟲研究（subprocess 模式）
│   ├── skill.json
│   └── skill.py
├── chat/        # 閒聊對話（subprocess 模式）
│   ├── skill.json
│   └── skill.py
└── dashboard/   # 儀表板（async 模式，需自行實作 dashboard_skill.py）
    ├── skill.json
    └── skill.py
```

路由流程：
- 對話觸發：Intent Router → Hybrid Router → Skill Resolver → Executor
- API 直接呼叫：`POST /api/skill/{skill_id}` → Executor
- 排程觸發：Scheduler cron → Executor

`arkbot_core.py` 的 `_foundation_fallback` 僅保留 CASUAL 閒聊作為最後防線。

## 12. Skill API 端點

`web_server.py` 提供 HTTP API：
- `GET /api/skills` — 列出所有已註冊 Skill
- `POST /api/skill/{skill_id}` — 直接執行指定 Skill

需要 `X-API-Key` header 驗證，對比 `.env` 中的 `SKILL_API_KEY`。

## 13. 排程系統

`src/scheduler.py` 使用 asyncio + croniter：
- 每 60 秒檢查到期排程
- 排程設定在 `data/schedules.json`
- 支援 `--dry-run` 模式
- 執行結果寫入 `data/scheduler.log`
- `start.bat --with-scheduler` 一鍵啟動含排程
