# 🤖 AI Agent Skills Workshop

> **SKILL.md（劇本）** + **Gemini API（演員）** + **Python 腳本（導演）** = 自動化產出

AI Agent 開發教學工作坊，透過實作三大模組，展示如何利用技能定義（Skills）搭配 Gemini API 進行自動化內容生成。

## 核心概念

```
.agent/skills/level-designer/SKILL.md   ← 劇本（定義 AI 角色與規範）
         ↓
agent_skills/src/gdd_generator.py       ← 導演（載入劇本 → 組裝 Prompt）
         ↓
Gemini 2.5 Flash Lite                        ← 演員（按規範生成內容）
         ↓
reports/GDD_火山要塞.md                  ← 產出
```

## 三大教學模組

| 模組 | 路徑 | 說明 |
|---|---|---|
| Agent Skills | `agent_skills/` | 鏈式 GDD 自動生成器（level-designer → character-creator → 組裝） |
| ClawdBot | `clawdbot/` | Telegram Bot，含 Gemini 意圖路由與網頁爬蟲技能 |
| Gemini Canvas | `gemini_canvas/` | FastAPI 資料儀表板，JSON API + HTML 視覺化渲染 |

## 技能庫

`.agent/skills/` 下有 13 個技能定義，涵蓋遊戲設計、文件撰寫、行銷文案等領域：

| 分類 | 技能 |
|---|---|
| 🎮 遊戲設計 | character-creator、level-designer |
| 📝 文件撰寫 | document-summarizer、meeting-minutes-writer、presentation-writer、sop-writer |
| 📧 溝通 | email-writer、social-media-writer |
| 📊 商業 | market-analyzer、marketing-copywriter、task-planner |
| 🤖 Agent | customer-support-agent、skill-creator |

## Kiro Skills（IDE 輔助技能）

`.kiro/skills/` 下有 3 個 Kiro 技能，在對話中用 `#` 引用：

| 技能 | 用途 |
|---|---|
| skill-creator | 引導建立新的 Kiro skill |
| slide-generator | 引導開發 Markdown → PPTX CLI 工具 |
| ai-agent-generator | 引導搭建 Bot + Web + 可插拔技能的 Agent 專案 |

## 快速開始

### 前置需求

- Python 3.12+（Windows 使用 `py` 載入器）
- Gemini API Key

### 安裝

```bash
py -m pip install google-genai python-dotenv
```

### 設定環境變數

在專案根目錄建立 `.env`：

```env
GOOGLE_API_KEY=你的_Gemini_API_金鑰
SKILL_PATH=.agent/skills
TELEGRAM_TOKEN=你的_Telegram_Bot_Token
```

### 驗證 API 連通

```bash
py agent_skills/tests/test_api.py
```

## 使用方式

### Agent Skills — GDD 生成

```bash
# 掃描可用技能
py agent_skills/src/loader.py

# 生成 GDD（鏈式：level-designer → character-creator → 組裝）
py agent_skills/src/gdd_generator.py "火山要塞"

# GDD 品質校準（AI 審計）
py agent_skills/tests/qa_validator.py "火山要塞"
```

### ClawdBot — Telegram Bot

```bash
# 需要 python-telegram-bot、requests、beautifulsoup4、markdownify
py -m pip install python-telegram-bot requests beautifulsoup4 markdownify

# 啟動 Bot
py clawdbot/src/bot_main.py
```

### Gemini Canvas — Web 儀表板

```bash
# 需要 fastapi、uvicorn
py -m pip install fastapi uvicorn

# 啟動伺服器（預設 http://127.0.0.1:8000）
py gemini_canvas/src/server.py
```

## 專案結構

```
ai_agent_skills/
├── .agent/                    # AI Agent 規範層
│   ├── skills/                # 13 個技能定義（SKILL.md）
│   ├── rules/                 # AI 編碼規範
│   ├── context/               # 專案記憶與架構文件
│   └── workflows/             # 標準 SOP（待建立）
├── .kiro/                     # Kiro IDE 設定
│   ├── skills/                # 3 個 Kiro 輔助技能
│   └── steering/              # AI 行為導引規範
├── agent_skills/              # 模組 1：GDD 自動生成器
│   ├── src/                   # gdd_generator.py、loader.py
│   ├── tests/                 # API 測試、品質校準
│   ├── reports/               # GDD 產出
│   └── docs/                  # 規格書
├── clawdbot/                  # 模組 2：Telegram Bot
│   ├── src/                   # bot_main、intent_router、crawler_skill
│   ├── data/                  # SQLite 資料庫
│   └── docs/                  # 文件
├── gemini_canvas/             # 模組 3：視覺化儀表板
│   ├── src/                   # FastAPI server
│   ├── web/                   # 靜態 HTML
│   ├── data/                  # JSON 資料源
│   └── docs/                  # 文件
└── docs/                      # 教學投影片與工作坊文件
```

## 技術棧

| 套件 | 用途 |
|---|---|
| `google-genai` | Gemini 2.5 Flash Lite LLM 推理 |
| `python-dotenv` | 環境變數載入 |
| `python-telegram-bot` | Telegram Bot 閘道 |
| `fastapi` + `uvicorn` | Web 伺服器 |
| `requests` + `beautifulsoup4` + `markdownify` | 網頁爬蟲 |

## 授權

MIT License

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
