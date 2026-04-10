---
inclusion: always
version: "1.1.0"
last_synced: "2026-04-10"
---

# 技術棧

## 語言
- Python 3.9+（實際使用 3.12，透過 `py` 啟動器執行）

## Kiro Skills 開發

| 工具 | 用途 |
|------|------|
| Kiro IDE | Skills 開發環境 |
| skill-creator | 技能建立 / 測試 / 打包 |
| skill-spec-writer | 技能級規格文件（餵給 skill-creator） |
| software-spec-writer | 專案級規格文件產生 |

## kiro-agent 套件

| 套件 | 用途 |
|------|------|
| python-telegram-bot | Telegram Bot（Forum Topic 路由） |
| PyYAML | fleet.yaml 配置解析 |
| FastAPI + uvicorn | Web Dashboard + SSE |
| httpx | Groq Whisper API 語音轉錄 |
| croniter | cron 排程表達式解析 |
| mcp (FastMCP) | Agent 間 MCP 協作 |
| google-genai | General Dispatcher 自然語言路由 |
| hypothesis | Property-based testing |
| pytest + pytest-asyncio | 測試框架 |

## ArkBot 相關套件

| 套件 | 用途 |
|------|------|
| FastAPI | HTTP API 框架（Web 對話介面） |
| uvicorn | ASGI 伺服器 |
| python-telegram-bot | Telegram Bot 入口 |
| google-genai | Gemini API（意圖分類、儀表板） |
| requests | HTTP 呼叫 |
| beautifulsoup4 | 爬蟲引擎 HTML 解析 |
| markdownify | HTML → Markdown 轉換 |

## 設定方式
- ArkBot 設定：`.env`（GOOGLE_API_KEY、TELEGRAM_TOKEN、WEB_PORT）
- kiro-agent 設定：`~/.kiro-agent/.env`（TELEGRAM_BOT_TOKEN、GOOGLE_API_KEY、GROQ_API_KEY）
- kiro-agent 配置：`~/.kiro-agent/fleet.yaml`

## 常用指令

```bash
# Kiro Skill 初始化（自動偵測路徑：.kiro/skills/ > .agent/skills/）
python .kiro/skills/skill-creator/scripts/init_skill.py <skill-name>

# Kiro Skill 驗證
python .kiro/skills/skill-creator/scripts/quick_validate.py .kiro/skills/<skill-name>

# Kiro Skill 同步（預設全量同步）
python .kiro/skills/skill-sync/scripts/sync_skills.py

# kiro-agent 測試
py -m pytest kiro_agent/tests/unit/ -q

# kiro-agent 艦隊管理
kiro-agent fleet start
kiro-agent fleet status
kiro-agent fleet stop
kiro-agent backend doctor kiro-cli
```

## 備註
- 尚未設定測試框架（ArkBot Skill Factory 的 Test Runner 規劃中）
- 尚未設定 linter / formatter
- `requirements.txt` 未鎖定版本
