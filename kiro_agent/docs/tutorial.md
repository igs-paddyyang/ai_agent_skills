# kiro-agent 教學使用手冊

## 概述

kiro-agent 是一個多 Agent 艦隊管理系統，將 Telegram 轉變為 AI 編碼 Agent 的指揮中心。每個 Telegram Forum Topic 對應一個獨立的 Agent Session，在 tmux 中執行 AI CLI 後端（Kiro CLI、Claude Code、Gemini CLI 等）。

系統提供費用控管、掛起偵測、Context 輪替、排程任務、Web Dashboard 等自主運維能力。

---

## 1. 安裝

### 前置需求

- Python 3.12+
- tmux（Agent Session 隔離）
- 至少一個 AI CLI 後端（kiro-cli、claude、gemini 等）

### 安裝步驟

```bash
# 進入專案目錄
cd kiro-agent

# 安裝依賴
pip install -r kiro_agent/requirements.txt

# 以開發模式安裝套件
pip install -e .

# 驗證安裝
kiro-agent --version
```

### 檢查後端是否可用

```bash
# 檢查 kiro-cli 後端
kiro-agent backend doctor kiro-cli

# 檢查 claude-code 後端
kiro-agent backend doctor claude-code
```

`backend doctor` 會檢查 CLI 工具是否安裝在 PATH 中，並嘗試取得版本資訊。

---

## 2. 配置

### 2.1 建立執行時目錄

首次啟動時會自動建立 `~/.kiro-agent/` 目錄結構：

```
~/.kiro-agent/
├── fleet.yaml          # 艦隊配置（需手動建立）
├── .env                # 敏感資訊（Bot Token、API Key）
├── events.db           # 事件日誌（自動建立）
├── scheduler.db        # 排程資料（自動建立）
└── instances/
    └── <name>/
        ├── statusline.json       # CLI 狀態
        ├── rotation_snapshot.md  # Context 輪替快照
        └── chat_history.jsonl    # 對話記錄
```

### 2.2 建立 .env 檔案

在 `~/.kiro-agent/.env` 中設定敏感資訊：

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
```

- `TELEGRAM_BOT_TOKEN` — Telegram Bot 的 Token（從 @BotFather 取得）
- `GOOGLE_API_KEY` — Google Gemini API Key（General Dispatcher 自然語言路由用）
- `GROQ_API_KEY` — Groq API Key（語音轉錄用，選填）

### 2.3 建立 fleet.yaml

在 `~/.kiro-agent/fleet.yaml` 中定義艦隊配置：

```yaml
# 專案目錄映射
project_roots:
  my-app: /home/user/projects/my-app
  my-lib: /home/user/projects/my-lib

# Telegram 頻道設定
channel:
  bot_token_env: TELEGRAM_BOT_TOKEN   # .env 中的變數名
  group_id: -1001234567890            # Telegram Group ID
  general_topic_id: 1                 # General Topic ID

# 預設值（Instance 未指定時使用）
defaults:
  backend: kiro-cli
  model: auto

# Agent Instance 定義
instances:
  - name: app-dev
    project: my-app
    backend: kiro-cli
    model: claude-sonnet-4
    description: "主應用開發 Agent"
    auto_start: true
    model_failover:
      - claude-sonnet-4
      - claude-haiku-4.5
    mcp_tools:
      - list_instances
      - delegate_task

  - name: lib-dev
    project: my-lib
    description: "函式庫開發 Agent"
    # 未指定 backend/model，使用 defaults 的值

# Team 定義（選填）
teams:
  - name: frontend
    members: [app-dev, lib-dev]
    description: "前端開發團隊"

# 費用控管
cost_guard:
  daily_limit_usd: 15.0
  warn_at_percentage: 80
  timezone: Asia/Taipei

# 掛起偵測
hang_detector:
  enabled: true
  timeout_minutes: 30

# 存取控制
access:
  mode: locked                        # locked | open
  allowed_users:
    - 123456789                       # 你的 Telegram User ID

# Web Dashboard 埠號
health_port: 8470
```

### 配置欄位說明

| 區段 | 說明 |
|------|------|
| `project_roots` | 專案名稱 → 絕對路徑的映射 |
| `channel` | Telegram Bot 連線設定 |
| `defaults` | Instance 未指定 backend/model 時的預設值 |
| `instances` | Agent Instance 清單 |
| `teams` | Instance 的邏輯分組 |
| `cost_guard` | 每日費用上限與警告閾值 |
| `hang_detector` | 掛起偵測超時設定 |
| `access` | Telegram 使用者白名單 |
| `health_port` | Dashboard HTTP 埠號 |

### 支援的後端

| 後端名稱 | CLI 命令 | 說明 |
|----------|---------|------|
| `kiro-cli` | `kiro-cli` | Kiro CLI（主要後端，支援 steering/skills） |
| `claude-code` | `claude` | Claude Code CLI |
| `gemini-cli` | `gemini` | Gemini CLI |
| `codex` | `codex` | OpenAI Codex CLI |
| `opencode` | `opencode` | OpenCode CLI |

### Kiro CLI 支援的模型

`auto`、`claude-sonnet-4.5`、`claude-sonnet-4`、`claude-haiku-4.5`

---

## 3. CLI 操作

### 3.1 艦隊管理

```bash
# 啟動艦隊（載入配置 → 啟動 auto_start Instance → 啟動 Telegram Bot）
kiro-agent fleet start

# 停止艦隊（停止所有 Instance → 停止 Telegram Bot）
kiro-agent fleet stop

# 查看艦隊狀態
kiro-agent fleet status
```

`fleet status` 輸出範例：

```
Name            Status   Backend      Model            Context%
--------------  -------  -----------  ---------------  --------
app-dev         running  kiro-cli     claude-sonnet-4  45%
lib-dev         stopped  kiro-cli     auto             0%
```

### 3.2 Instance 管理

```bash
# 互動式建立新 Instance
kiro-agent instance create
# 依序輸入：名稱、project、backend、model

# 刪除 Instance
kiro-agent instance delete <name>
```

### 3.3 後端診斷

```bash
# 檢查後端安裝狀態
kiro-agent backend doctor kiro-cli
kiro-agent backend doctor claude-code
```

輸出範例：

```
Backend: kiro-cli
CLI Tool: kiro-cli
Installed: YES (/usr/local/bin/kiro-cli)
Version: kiro-cli 1.2.3
```

---

## 4. Telegram 操作

### 4.1 基本訊息流程

1. 在 Telegram Group 中，每個 Instance 對應一個 Forum Topic
2. 在 Topic 中發送訊息 → 自動路由到對應的 Agent
3. Agent 的回應會發送回同一個 Topic
4. 超過 4096 字元的回應會自動分割為多則訊息

### 4.2 General Topic

在 General Topic 中發送訊息時，系統使用 Gemini 分析訊息意圖，自動路由到最適合的 Agent。

如果無法識別目標，會列出所有可用的 Instance 請你指定。

### 4.3 存取控制

- `access.mode: locked` — 僅 `allowed_users` 中的 Telegram User ID 可操作
- `access.mode: open` — 所有使用者皆可操作
- 未授權的訊息會被靜默忽略，並記錄 `access_denied` 事件

### 4.4 Inline Button

當 Agent 請求工具使用權限時，Telegram 會顯示 Allow / Deny 按鈕。

當偵測到 Agent 掛起時，會顯示三個按鈕：
- 重啟 — 停止並重新啟動 Instance
- 繼續等待 — 忽略本次掛起警告
- 強制停止 — 立即終止 Instance

### 4.5 語音訊息

發送 Telegram 語音訊息時，系統會透過 Groq Whisper API 自動轉錄為文字，再作為一般訊息處理。需要在 `.env` 中設定 `GROQ_API_KEY`。

---

## 5. 自主運維功能

### 5.1 費用控管（Cost Guard）

- 追蹤每個 Instance 的 API 使用費用
- 達到 `warn_at_percentage`（預設 80%）時發送 Telegram 警告
- 達到 `daily_limit_usd` 時自動暫停 Instance
- 每日依 `timezone` 自動重置

### 5.2 掛起偵測（Hang Detector）

- 每 60 秒檢查 running Instance 的最後活動時間
- 超過 `timeout_minutes`（預設 30 分鐘）發送 Telegram 通知
- 通知包含 inline button（重啟 / 繼續等待 / 強制停止）

### 5.3 Context 輪替（Context Guardian）

- 讀取 `~/.kiro-agent/instances/<name>/statusline.json` 取得 context 使用率
- 超過 80% 時產生 RotationSnapshot（工作摘要 + 關鍵決策）
- 重啟 Session 並注入快照，讓 Agent 延續工作
- `statusline.json` 不存在時自動跳過

### 5.4 排程系統（Scheduler）

使用 cron 表達式定義定時任務，持久化於 `scheduler.db`。

```python
# 程式化使用範例
from kiro_agent.scheduler import Scheduler

scheduler = Scheduler("~/.kiro-agent/scheduler.db")

# 建立排程：每天早上 9 點執行
await scheduler.create_schedule("0 9 * * *", "開始今日工作", "app-dev")

# 列出所有排程
entries = await scheduler.list_schedules()

# 停用/啟用排程
await scheduler.toggle_schedule(schedule_id)

# 刪除排程
await scheduler.delete_schedule(schedule_id)
```

### 5.5 Crash 自動重啟

當 Instance 的 tmux Session 意外終止時：
- 第 1 次重試：等待 5 秒
- 第 2 次重試：等待 15 秒
- 第 3 次重試：等待 45 秒
- 3 次失敗後標記為 crashed，發送 Telegram 通知

### 5.6 模型故障轉移（Model Failover）

當主模型不可用時，依照 `model_failover` 陣列順序嘗試備用模型：

```yaml
instances:
  - name: app-dev
    model: claude-sonnet-4
    model_failover:
      - claude-sonnet-4
      - claude-haiku-4.5
```

成功切換時發送 Telegram 通知，全部失敗時暫停 Instance。

---

## 6. Agent 間協作（MCP Bridge）

Agent 之間透過 MCP Tool 進行 P2P 協作。每個 Agent 可使用以下 MCP Tool：

| Tool | 說明 |
|------|------|
| `list_instances` | 列出所有 Instance 的名稱、狀態、描述、後端 |
| `send_to_instance` | 傳送訊息到目標 Instance |
| `request_information` | 向目標 Instance 請求資訊 |
| `delegate_task` | 委派任務（自動喚醒停止的 Instance） |
| `report_result` | 回傳任務結果給委派者 |
| `create_team` | 建立 Team |
| `broadcast` | 廣播訊息到 Team 所有成員 |

### 協作範例

Agent A 委派任務給 Agent B：

```
Agent A → delegate_task(target="lib-dev", task="更新 API 文件")
  ↓ (lib-dev 若未啟動，自動喚醒)
Agent B 收到: [DELEGATED TASK] 更新 API 文件
  ↓ (完成後)
Agent B → report_result(requester="app-dev", result="API 文件已更新")
Agent A 收到: [TASK RESULT] API 文件已更新
```

### Fleet Context 注入

使用 kiro-cli 後端時，系統會自動在 `.kiro/steering/fleet-context.md` 寫入艦隊上下文，讓 Agent 知道自己的身份、可用的 peer、協作規則。

---

## 7. Web Dashboard

啟動艦隊後，Dashboard 會在 `health_port`（預設 8470）提供 HTTP API：

| 端點 | 說明 |
|------|------|
| `GET /api/instances` | 所有 Instance 即時狀態（JSON） |
| `GET /api/events?limit=50` | 最近事件日誌（JSON） |
| `GET /sse` | Server-Sent Events 即時推送 |

### SSE 即時監控

```javascript
const source = new EventSource("http://localhost:8470/sse");
source.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("狀態更新:", data);
};
```

---

## 8. HTML 對話匯出

將 Agent 的對話記錄匯出為自包含 HTML 檔案：

```python
from kiro_agent.html_exporter import export_chat_html

messages = [
    {"timestamp": "2025-01-15T10:30:00Z", "sender": "user", "content": "修改登入頁面"},
    {"timestamp": "2025-01-15T10:31:00Z", "sender": "agent", "content": "已完成修改"},
]

html = export_chat_html("app-dev", messages)

with open("chat_export.html", "w", encoding="utf-8") as f:
    f.write(html)
```

匯出的 HTML 內嵌 CSS + JS，可離線檢視，程式碼區塊支援一鍵複製。

---

## 9. 事件日誌

所有重要事件記錄在 `~/.kiro-agent/events.db`（SQLite）：

| 事件類型 | 說明 |
|---------|------|
| `instance_started` | Instance 啟動 |
| `instance_stopped` | Instance 停止 |
| `instance_crashed` | Instance 崩潰 |
| `message_sent` | 訊息已發送 |
| `message_received` | 訊息已接收 |
| `cost_warning` | 費用警告 |
| `cost_limit_reached` | 費用達上限 |
| `hang_detected` | 偵測到掛起 |
| `context_rotated` | Context 已輪替 |
| `schedule_triggered` | 排程已觸發 |
| `access_denied` | 存取被拒絕 |

超過 30 天的事件會自動清理。

```python
from kiro_agent.event_logger import EventLogger

logger = EventLogger("~/.kiro-agent/events.db")

# 查詢最近事件
events = logger.query(limit=20)

# 依類型查詢
crashes = logger.query(event_type="instance_crashed")

# 依 Instance 查詢
events = logger.query(instance_name="app-dev", limit=10)

# 手動清理
deleted = logger.cleanup(days=30)
```

---

## 10. 測試

```bash
# 執行所有單元測試
py -m pytest tests/unit/ -v

# 執行特定模組測試
py -m pytest tests/unit/test_config.py -v
py -m pytest tests/unit/test_fleet_manager.py -v
```

---

## 11. 模組架構速查

```
kiro_agent/
├── __init__.py           # 版本、RUNTIME_DIR、ensure_runtime_dirs()
├── __main__.py           # CLI 入口（fleet/instance/backend 子命令）
├── config.py             # fleet.yaml 載入、驗證、序列化
├── models.py             # 資料模型（dataclass）與自訂例外
├── db.py                 # SQLite schema 初始化
├── event_logger.py       # 事件日誌 CRUD
├── fleet_manager.py      # 艦隊生命週期管理核心
├── channel_router.py     # Telegram 訊息路由 + 存取控制
├── backend_adapter.py    # AI CLI 後端抽象層（5 個 Adapter）
├── general_dispatcher.py # General Topic 自然語言路由（Gemini）
├── mcp_bridge.py         # Agent 間 MCP 協作（7 個 Tool）
├── cost_guard.py         # 費用控管
├── hang_detector.py      # 掛起偵測
├── context_guardian.py   # Context 輪替
├── scheduler.py          # cron 排程系統
├── model_failover.py     # 模型故障轉移
├── voice_transcriber.py  # 語音轉錄（Groq Whisper）
├── html_exporter.py      # HTML 對話匯出
└── dashboard.py          # Web Dashboard（FastAPI + SSE）
```

---

## 12. 快速開始 Checklist

1. 安裝 Python 3.12+ 與 tmux
2. `pip install -e .` 安裝 kiro-agent
3. `kiro-agent backend doctor kiro-cli` 確認後端可用
4. 建立 `~/.kiro-agent/.env`（填入 Bot Token）
5. 建立 `~/.kiro-agent/fleet.yaml`（定義 Instance）
6. `kiro-agent fleet start` 啟動艦隊
7. 在 Telegram Group 的 Forum Topic 中與 Agent 對話
8. `kiro-agent fleet status` 查看狀態
9. `kiro-agent fleet stop` 停止艦隊
