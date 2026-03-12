# 🧠 專案記憶與進度管理 (Memory & Progress)

## 📌 關鍵技術棧 (Key Tech Stack)
- **環境管理**: Windows OS, Python 3.12+ (使用 `py` 載入器)
- **AI 模型**: Gemini 2.0 Flash
- **開發規範**: Skill-First, PEP 8, UTF-8 Encoding
- **版本控制**: Git → GitHub (`igs-paddyyang/ai_agent_skills`, branch: `main`)
- **目錄架構**:
  - `.agent/rules/`: 系統護欄 (gemini.md, ai_coding_standards.md, ai_coding_workflow.md)
  - `.agent/context/`: 記憶與上下文 (memory.md, ai_agent.md, agent_skills.md)
  - `.agent/skills/`: 技能定義 (13 個技能)
  - `.agent/workflows/`: 標準 SOP (待建立)
  - `.kiro/steering/`: Kiro Steering 文件 (6 檔)

---

## 📂 專案模組總覽 (Project Modules)

| 模組 | 路徑 | 狀態 | 說明 |
|:---|:---|:---|:---|
| Agent Skills (GDD 生成器) | `agent_skills/` | ✅ 完成 | 鏈式 GDD 自動生成，含 QA 校準 |
| ClawdBot (Telegram Bot) | `clawdbot/` | ⏳ 進行中 | 智慧意圖路由 + 爬蟲技能 |
| Gemini Canvas (視覺化) | `gemini_canvas/` | ⏳ 進行中 | 資料儀表板 + HTML 渲染 |

---

## 🚀 完成進度 (Completion Progress)

### ✅ 已完成項目
- [x] `.agent/` 目錄架構建立 (rules / skills / workflows / context)
- [x] 3 份 rules + 3 份 context 文件
- [x] 13 個 `.agent/skills/` 技能定義 (SKILL.md)
- [x] Agent Skills 模組：loader.py、gdd_generator.py、qa_validator.py、test_api.py
- [x] 產出 3 份 GDD 報告 + QA 分析報告
- [x] ClawdBot 核心模組 (bot_main, intent_router, crawler_skill, format_utils)
- [x] Gemini Canvas 模組 (server.py, index.html, data.json)
- [x] 教學投影片 `ai_agent_practic_slides.md`
- [x] `.gitignore` + 首次 Git 推送至 GitHub
- [x] `.kiro/steering/` 6 檔對齊本 repo 實際內容 (2026-03-12)

### ⏳ 進行中項目
- [ ] ClawdBot: TG 介面優化與 MarkdownV2 容錯
- [ ] ClawdBot: 意圖路由完整測試
- [ ] Gemini Canvas: 儀表板互動功能強化
- [ ] `.agent/workflows/` 標準 SOP 建立

### 📅 未來計畫 (Roadmap)
- [ ] 整合 BigQuery 資料源
- [ ] 自動化日度報告流程
- [ ] Docker Multi-stage 部署優化
- [ ] 新增更多 GDD 技能鏈 (quest-designer, item-designer)

---

## 🏛️ 重大架構決策紀錄

| 日期 | 決策 | 原因 |
|---|---|---|
| 2026-03-11 | GDD 採鏈式架構 (level-designer → character-creator → 組裝) | 上下文傳遞讓 Boss 對齊環境，邏輯一致性更高 |
| 2026-03-11 | SKILL.md 全文注入 Prompt 作為系統指令 | 完整理解角色規範，比摘要注入品質更好 |
| 2026-03-12 | Steering 從 Nana Agent 體系重寫為本 repo 專屬 | 原內容描述另一個專案，造成 AI 認知錯位 |

---

## 🔗 重要連結
- **GitHub**: https://github.com/igs-paddyyang/ai_agent_skills

---
*最後更新時間: 2026-03-12*
