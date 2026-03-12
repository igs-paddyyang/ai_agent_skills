---
inclusion: manual
# 📌 注入模式：手動引用
# 📋 用途：專案進度存檔點，記錄當前開發狀態與重大決策
# 🎯 使用時機：開啟新對話視窗時，用 #File 手動餵入
# ✏️ 維護：每次開發告一段落後更新
---

> 每次開新對話視窗時，將此檔案餵給 AI，讓它立即進入狀況。

---

## 🗂️ 專案基本資訊

- 專案名稱：AI Agent Skills Workshop（AI 代理技能工作坊）
- 主要語言：Python 3.12+
- AI 模型：`gemini-2.0-flash`
- GitHub：https://github.com/igs-paddyyang/ai_agent_skills（branch: main）
- 最後更新：2026-03-12

---

## 📊 當前開發狀態

### ✅ 已完成
- `.agent/` 目錄架構建立（rules / skills / workflows / context）
- 3 份 rules 文件 + 3 份 context 文件
- 13 個 `.agent/skills/` 技能定義（SKILL.md）
- Agent Skills 模組：loader.py、gdd_generator.py、qa_validator.py、test_api.py、list_models.py、test_marketing.py
- 產出 GDD 報告 + QA 分析報告（動態命名：GDD_{主題}_{日期}.md）
- ClawdBot 核心模組（bot_main、intent_router、crawler_skill、format_utils）
- Gemini Canvas 模組（server.py、index.html、data.json）
- 教學投影片 `ai_agent_skills_workshop_slides.md`（含實作練習 3 頁、Skill 秘訣 2 頁）
- 實戰投影片 `ai_agent_practic_slides.md`
- `.gitignore` + Git 推送至 GitHub
- `.kiro/steering/` 6 檔對齊本 repo 實際內容
- `.kiro/skills/` 3 個 Kiro skill（skill-creator、slide-generator、ai-agent-generator）
- 全部 `.md` 檔案加入著作權標註
- 根目錄 `README.md` 建立
- `.env.example` 環境變數範例
- `tools/mermaid/build_diagrams.py` + `gdd_flow.mmd` → `docs/images/gdd_flow.png`
- qa_validator.py 修正（自動搜尋 GDD、動態報告命名、移除 Antigravity 殘留）
- list_models.py 遷移至 `google-genai` 新 API
- marketing-pro 實作用技能已移除（僅作為投影片教學範例，由學員自行建立）
- `.agent/` 目錄架構建立（rules / skills / workflows / context）
- 3 份 rules 文件（gemini.md、ai_coding_standards.md、ai_coding_workflow.md）
- 3 份 context 文件（memory.md、ai_agent.md、agent_skills.md）
- 13 個 `.agent/skills/` 技能定義（SKILL.md）
- Agent Skills 模組完成：loader.py、gdd_generator.py、qa_validator.py、test_api.py
- 產出 3 份 GDD 報告（深海大冒險、火山要塞、科幻太空實驗室）+ QA 分析報告
- ClawdBot 核心模組（bot_main、intent_router、crawler_skill、format_utils）
- Gemini Canvas 模組（server.py、index.html、data.json）
- 教學投影片 `ai_agent_practic_slides.md`
- `.gitignore` 建立 + Git 推送至 GitHub
- `.kiro/steering/` 6 檔對齊本 repo 實際內容（2026-03-12）
- `.kiro/skills/skill-creator.md` — Kiro 技能建立器
- `.kiro/skills/slide-generator.md` — 投影片生成器 skill
- `.kiro/skills/ai-agent-generator.md` — AI Agent 專案生成器 skill
- 全部 `.md` 檔案加入著作權標註（28 檔）
- 根目錄 `README.md` 建立

### ⏳ 進行中
- ClawdBot: Telegram Bot 介面優化與 MarkdownV2 容錯
- Gemini Canvas: 儀表板互動功能強化
- `.agent/workflows/` 標準 SOP 建立

### 📅 未來計畫
- 整合 BigQuery 資料源
- 自動化日度報告流程
- Docker Multi-stage 部署優化
- 新增更多 GDD 技能鏈（quest-designer、item-designer）

---

## 🛠️ Kiro Skills 清單

| 技能 | 路徑 | 用途 |
|---|---|---|
| skill-creator | `.kiro/skills/skill-creator.md` | 引導建立新的 Kiro skill |
| slide-generator | `.kiro/skills/slide-generator.md` | 引導開發 Markdown → PPTX CLI 工具 |
| ai-agent-generator | `.kiro/skills/ai-agent-generator.md` | 引導搭建 Bot + Web + 可插拔技能的 Agent 專案 |

---

## 🏛️ 重大架構決策紀錄

| 日期 | 決策 | 原因 |
|---|---|---|
| 2026-03-11 | GDD 生成採鏈式架構（level-designer → character-creator → 組裝） | 上下文傳遞讓 Boss 設計能對齊環境危險要素，邏輯一致性更高 |
| 2026-03-11 | SKILL.md 全文注入 Prompt 作為系統指令 | 讓 Gemini 完整理解角色規範，比摘要注入品質更好 |
| 2026-03-12 | Steering 檔案從 Nana Agent 體系重寫為本 repo 專屬 | 原內容描述的是另一個專案，造成 AI 認知錯位 |
| 2026-03-12 | Kiro skills 採單一 `.md` 檔案格式（非 `.agent/skills/` 的目錄結構） | Kiro 原生格式，用 `#` 引用即可注入，輕量且直覺 |
| 2026-03-12 | ai-agent-generator 採 BaseSkill + skill_loader 動態載入架構 | 可插拔設計，新增技能只需加 `.py` 檔案，無需改路由邏輯 |

---

## 💬 上次對話摘要

- 2026-03-12（第三輪）：移除實作用 marketing-pro 技能目錄（由學員自行建立）、更新 memory.md 與 context/memory.md、git 提交推送。
- 2026-03-12（第二輪）：投影片大幅優化（實作練習 3 頁、Skill 秘訣 2 頁、Mermaid 圖表、字型調整）、qa_validator.py 修正、list_models.py 遷移、.env.example 建立、test_marketing.py 建立、tools/mermaid/ 工具。
- 2026-03-12（第一輪）：建立 ai-agent-generator skill、根目錄 README.md、更新 memory.md。

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
