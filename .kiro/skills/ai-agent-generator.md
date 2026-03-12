---
inclusion: manual
---

# ai-agent-generator（AI Agent 專案生成器）

引導 Kiro 快速搭建完整的 AI Agent 專案，包含 Telegram Bot 閘道、FastAPI Web 服務、Gemini 意圖路由，以及可插拔技能系統。

## 觸發情境

- 使用者說「建立新 Agent」、「生成 AI Agent 專案」、「打造一個 Bot + Web Agent」
- 使用者想快速搭建含 Telegram Bot 與 Web API 的 Agent 骨架
- 使用者想建立具備可插拔技能架構的 AI 應用

## 技術棧

- Python 3.12+，Windows 使用 `py` 載入器
- `google-genai`：Gemini 2.5 Flash Lite LLM 推理
- `python-dotenv`：環境變數
- `python-telegram-bot`：Telegram Bot 閘道
- `fastapi` + `uvicorn`：Web 服務
- `requests` + `beautifulsoup4` + `markdownify`：爬蟲技能
- `python-pptx`：投影片技能

## 工作流程

### 步驟 1：需求確認

向使用者確認以下資訊：

1. **Agent 名稱**：snake_case 格式（例如 `my_agent`），作為專案目錄名稱
2. **啟用架構**：
   - `bot` — 僅 Telegram Bot
   - `web` — 僅 FastAPI Web 服務
   - `both`（預設）— Bot + Web 同時啟用
3. **預設技能**（可複選，預設全選）：
   - `crawler_skill` — 網頁爬取 → Markdown → AI 摘要
   - `canvas_skill` — 結構化資料 → JSON API → HTML 視覺化
   - `slide_skill` — Markdown 大綱 → PPTX 投影片生成
4. **額外需求**：是否有自訂技能需要一併建立

### 步驟 2：建立目錄結構

根據使用者選擇，在專案根目錄下建立：

```
{agent_name}/
├── src/
│   ├── __init__.py
│   ├── intent_router.py      # Gemini 意圖路由器
│   ├── skill_loader.py       # 技能動態載入器
│   ├── bot_main.py           # Telegram Bot 閘道（若啟用 bot）
│   ├── web_server.py         # FastAPI Web 服務（若啟用 web）
│   └── skills/               # 可插拔技能目錄
│       ├── __init__.py
│       ├── base_skill.py     # 技能基底類別
│       ├── crawler_skill.py  # 網頁爬蟲（若選擇）
│       ├── canvas_skill.py   # 資料視覺化（若選擇）
│       └── slide_skill.py    # 投影片生成（若選擇）
├── data/                     # 資料庫 / 靜態資料
├── web/                      # HTML 靜態頁面（若啟用 web）
├── docs/
├── main.py                   # CLI 入口
└── requirements.txt
```

若使用者僅選擇 `bot` 或 `web`，省略未選擇架構的對應檔案。

### 步驟 3：實作核心框架

#### 3a. base_skill.py — 技能基底類別

所有技能繼承此類別，確保統一介面：

```python
from abc import ABC, abstractmethod

class BaseSkill(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """執行技能，回傳 {"success": bool, "result": str/dict}"""
        pass
```

#### 3b. skill_loader.py — 技能動態載入器

掃描 `skills/` 目錄，自動註冊所有繼承 `BaseSkill` 的類別：

```python
def load_skills() -> dict[str, BaseSkill]:
    """回傳 {"skill_name": skill_instance, ...}"""
```

- 使用 `importlib` 動態載入 `skills/` 下的 `.py` 檔案
- 過濾出繼承 `BaseSkill` 的類別並實例化
- 以 `skill.name` 為 key 註冊

#### 3c. intent_router.py — Gemini 意圖路由器

參考 clawdbot 的 `ClawdBrain` 模式：

- 使用 `google-genai` + `models/gemini-2.5-flash-lite`
- `classify_intent(user_input)` → 回傳 `{"intent": str, "skill": str, "params": dict}`
- 系統 Prompt 動態注入已載入的技能清單，讓 Gemini 知道可用技能
- API Key 從 `.env` 的 `GOOGLE_API_KEY` 讀取

```python
class IntentRouter:
    def __init__(self, skills: dict[str, BaseSkill]):
        """接收已載入的技能字典，建構路由系統 Prompt"""

    def classify_intent(self, user_input: str) -> dict:
        """分析意圖，回傳匹配的技能名稱與參數"""

    def route_and_execute(self, user_input: str) -> dict:
        """分類意圖 → 呼叫對應技能 → 回傳結果"""
```

### 步驟 4：實作 Bot 閘道（若啟用 bot）

參考 clawdbot 的 `ClawdBot` 模式建立 `bot_main.py`：

- 使用 `python-telegram-bot` 的 `ApplicationBuilder`
- `/start` 指令：歡迎訊息，列出可用技能
- 訊息處理：`intent_router.route_and_execute()` → 格式化回傳
- Token 從 `.env` 的 `TELEGRAM_TOKEN` 讀取
- 包含 MarkdownV2 跳脫處理工具函式

```python
class AgentBot:
    def __init__(self):
        self.skills = load_skills()
        self.router = IntentRouter(self.skills)

    async def handle_message(self, update, context):
        result = self.router.route_and_execute(update.message.text)
        # 格式化並回傳結果
```

### 步驟 5：實作 Web 服務（若啟用 web）

參考 gemini_canvas 的 `server.py` 模式建立 `web_server.py`：

- `GET /api/skills` — 列出所有已載入技能（名稱 + 描述）
- `POST /api/invoke` — 呼叫指定技能，body: `{"skill": str, "input": dict}`
- `GET /dashboard` — 提供靜態 HTML 頁面（從 `web/` 目錄）
- 使用 `FastAPI` + `uvicorn`

```python
app = FastAPI(title="{agent_name} API")

@app.get("/api/skills")
async def list_skills():
    return [{"name": s.name, "description": s.description} for s in skills.values()]

@app.post("/api/invoke")
async def invoke_skill(request: InvokeRequest):
    result = skills[request.skill].execute(request.input)
    return result
```

### 步驟 6：植入預設技能

根據使用者選擇，實作對應技能：

#### crawler_skill.py（網頁爬蟲）
- 繼承 `BaseSkill`，`name = "crawler"`
- `execute({"url": str})` → 爬取網頁 → 轉 Markdown → Gemini 摘要
- 參考 clawdbot 的 `ClawdCrawler` 模式
- 含 SQLite 快取機制

#### canvas_skill.py（資料視覺化）
- 繼承 `BaseSkill`，`name = "canvas"`
- `execute({"data": dict, "mock": bool})` → 回傳結構化 JSON 或生成 HTML
- 參考 gemini_canvas 的資料模型與 mock 資料產生器

#### slide_skill.py（投影片生成）
- 繼承 `BaseSkill`，`name = "slide"`
- `execute({"topic": str})` 或 `execute({"outline_file": str})`
- 使用 `python-pptx` 生成 PPTX
- AI 模式：Gemini 生成大綱 → 轉 PPTX

### 步驟 7：建立 CLI 入口與設定檔

#### main.py — 統一 CLI 入口

```bash
# 啟動 Telegram Bot
py main.py bot

# 啟動 Web 服務
py main.py web

# 同時啟動 Bot + Web
py main.py both

# 列出可用技能
py main.py skills
```

使用 `typer` 或 `argparse` 建立 CLI。

#### requirements.txt

根據選擇的架構與技能生成對應的依賴清單。

### 步驟 8：驗證與測試

1. 確認目錄結構完整
2. 確認 `py main.py skills` 能列出所有已載入技能
3. 若啟用 bot：確認 `py main.py bot` 能啟動（需要有效 TELEGRAM_TOKEN）
4. 若啟用 web：確認 `py main.py web` 能啟動，`/api/skills` 回傳正確
5. 測試至少一個技能的 `execute()` 能正常運作
6. 確認所有 API Key 從 `.env` 讀取，無硬編碼

## 品質標準

| 項目 | 要求 |
|---|---|
| 技能介面 | 所有技能繼承 `BaseSkill`，實作 `execute()` |
| 動態載入 | `skill_loader` 自動掃描 `skills/` 目錄 |
| 意圖路由 | Gemini 根據技能清單動態分類意圖 |
| 環境變數 | API Key / Token 一律從 `.env` 讀取 |
| 錯誤處理 | 技能執行失敗時回傳友善錯誤訊息，不中斷主程式 |
| 編碼 | UTF-8，對外產出使用繁體中文 |
| 架構彈性 | 可單獨啟用 bot 或 web，也可同時啟用 |
| 技能擴充 | 新增技能只需在 `skills/` 下新增 `.py` 檔案，無需修改其他程式碼 |

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
