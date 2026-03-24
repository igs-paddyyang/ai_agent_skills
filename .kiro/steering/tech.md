---
inclusion: always
version: "1.0.0"
last_synced: "2026-03-24"
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

## 常用指令

```bash
# Kiro Skill 初始化（自動偵測路徑：.kiro/skills/ > .agent/skills/）
python .kiro/skills/skill-creator/scripts/init_skill.py <skill-name>

# 手動指定路徑
python .kiro/skills/skill-creator/scripts/init_skill.py <skill-name> --path .kiro/skills
python .kiro/skills/skill-creator/scripts/init_skill.py <skill-name> --path .agent/skills

# Kiro Skill 驗證
python .kiro/skills/skill-creator/scripts/quick_validate.py .kiro/skills/<skill-name>

# Kiro Skill 打包
python -m scripts.package_skill .kiro/skills/<skill-name>

# Kiro Skill 同步（預設全量同步）
python .kiro/skills/skill-sync/scripts/sync_skills.py
python .kiro/skills/skill-sync/scripts/sync_skills.py --skills skill-creator env-smoke-test

# ArkBot 啟動（Web + Telegram）
start.bat

# ArkBot 資料庫初始化
py scripts/init_db.py
```

## 備註
- 尚未設定測試框架（ArkBot Skill Factory 的 Test Runner 規劃中）
- 尚未設定 linter / formatter
- `requirements.txt` 未鎖定版本
