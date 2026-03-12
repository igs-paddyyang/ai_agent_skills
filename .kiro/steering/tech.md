---
inclusion: always
# 📌 注入模式：永遠自動注入
# 📋 用途：技術棧、套件版本與常用指令速查，避免 AI 猜測環境
# ✏️ 維護：新增套件或指令時更新
---

# 技術棧

## 語言與執行環境
- Python 3.12+（Windows 使用 `py` 載入器）
- 無前端建置系統（gemini_canvas 的靜態 HTML 由 FastAPI 提供服務）

## 主要套件
| 套件 | 用途 | 使用模組 |
|---|---|---|
| `google-genai` | Gemini API（`models/gemini-2.5-flash-lite`）LLM 推理引擎 | 全部 |
| `python-dotenv` | 環境變數載入 | 全部 |
| `python-telegram-bot` | Telegram Bot 閘道 | clawdbot |
| `fastapi` + `uvicorn` | Web 伺服器 | gemini_canvas |

## 環境變數（`.env`，位於專案根目錄）
- `GOOGLE_API_KEY` — Gemini API 金鑰（必要）
- `SKILL_PATH` — 技能定義路徑，預設 `.agent/skills`
- `TELEGRAM_TOKEN` — Telegram Bot Token（clawdbot 用）

## 常用指令

```bash
# 安裝核心套件
py -m pip install google-genai python-dotenv

# 驗證 Gemini API 連通
py agent_skills/tests/test_api.py

# 掃描可用技能
py agent_skills/src/loader.py

# 生成 GDD（鏈式：level-designer → character-creator → 組裝）
py agent_skills/src/gdd_generator.py "火山要塞"

# GDD 品質校準（AI 審計）
py agent_skills/tests/qa_validator.py "火山要塞"

# 啟動 ClawdBot
py clawdbot/src/bot_main.py

# 啟動 Gemini Canvas 伺服器
py gemini_canvas/src/server.py
```

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
