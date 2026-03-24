---
inclusion: manual
version: "1.0.0"
last_synced: "2026-03-24"
---

# 專案記憶

> 開新對話時，用 `#File` 手動餵入此檔案，讓 AI 立即進入狀況。

---

## 專案基本資訊

- 專案名稱：Google Antigravity — Agent Skills Factory
- 定位：Agent Framework 與 Agent Skills 開發、測試、打包專案
- Python 3.12，透過 `py` 啟動器執行
- 使用者：paddyyang
- 最後更新：2026-03-24

---

## 當前開發狀態

### Kiro Skills（11 個，全部含 README.md）
- `skill-creator` v2.1.0 — 技能建立 / 測試 / 迭代改進（含 eval 框架、盲測比較、描述優化）
- `skill-spec-writer` v0.2.0 — 技能級規格文件（餵給 skill-creator，5 階段工作流程）
- `software-spec-writer` v1.1.0 — 軟體工程規格文件（8 章節：Part I 規格設計 5 + Part II 執行計畫 3）
- `arkbot-agent-generator` v1.2.0 — Generator Platform：統一 CLI（generate.py）+ Manifest 驅動 + Module Registry。支援 arkbot（~37 檔）/ arkagent（~91 檔）兩種 profile，--no-compat / --dry-run / --modules 選項。v1.2.0 回寫 DataWiseBot-Agent 12 Issues + 8 Fixes 至模板（entry.py 分離入口、config.py cp950 相容、registry.py 新入口常數）
- `gemini-canvas-dashboard` v1.0.0 — 通用儀表板（任意 JSON → Gemini API → HTML）
- `document-summarizer` v0.1.0 — 文件摘要（一句話摘要 + 核心重點 + 行動建議）
- `websearch-summarizer` v0.1.0 — 網頁搜尋摘要（URL / 關鍵字 → 結構化摘要）
- `env-setup-installer` v0.1.0 — 環境與服務安裝引導（Python / 套件 / .env / Gemini / Telegram）
- `env-smoke-test` v0.1.0 — 環境煙霧測試（Python / packages / Gemini API / Telegram，4 階段）
- `skill-sync` v0.3.0 — 技能同步工具（預設全量同步、支援 --skills / --reverse / --dry-run）
- `game-design-document-writer` v0.1.0 — 遊戲企劃文件（完整 GDD 10 章節 + One Pager，8 類型指南）

### ArkBot 範例專案（nana_bot/）
- Telegram Bot + Web 對話（port 2141），四層架構
- 意圖分類 3 種：DASHBOARD > RESEARCH > CASUAL
- 雙層決策引擎：Intent Router + Skill Resolver
- Skill Runtime 正式化：3 個內建 Skill Package（dashboard / crawler / chat）
- Executor 支援 async + subprocess 雙模式
- Skill API：`GET /api/skills`、`POST /api/skill/{skill_id}`（API Key 驗證）
- Scheduler：asyncio + croniter 排程引擎（`data/schedules.json`，3 個預設排程）

### DataWiseBot Agent（DataWiseBot-Agent/）
- ArkAgent OS 產出的範例專案（port 2142）
- 產品：金猴爺（Golden HoYeah）監控與數據分析
- generator-issues-report.md v2.1：12 個問題全部修正完成，已回寫至 generator 模板
- 額外修正：cp950 編碼崩潰、儀表板意圖誤判、儀表板資料綁定
- 報告中心：`/dashboard` 入口（日期/類型篩選、卡片 grid、備份移除功能）
- Dashboard API：`GET /api/dashboards`、`DELETE /api/dashboards/{filename}`（備份至 archive/）
- Skill API：`GET /api/skills`、`POST /api/skill/{skill_id}`（API Key 驗證，key: datawise-skill-api-key-2026）
- TG 通報群：DataWiseReports（chat_id: -1003706655958，Topics: 營收監控=4, 遊戲分析=3）
- 監控群組：告警監控（-1002838311570）、金流監控（-1001977542987）

### 設計文件（docs/）
- `generator-platform-spec.md` v1.1 — Generator Platform 統一產生器規格文件（6 Task 全部完成 ✅）
- `arkagent-platform-spec.md` v1.1 — 平台級架構升級規格文件（11 Task 全部完成 ✅）
- `arkagent-upgrade-spec.md` v1.1 — ArkAgent OS 升級規格文件（10 Task 全部完成 ✅）
- `arkbot-agent-spec.md` v3.1 — ArkBot 完整規格文件（四層架構）
- `arkbot-skill-runtime-spec.md` v1.1 — Skill Runtime 正式化（9 Task 完成）
- `arkbot-generator-refactor-spec.md` v1.1 — 模板模組化重構（7 Task 完成）
- `generator-issues-report.md` v2.1 — Generator 產出問題追蹤（12 Issues + 8 Fixes，全部已修正+回寫）
- Agent 雙層決策架構 + ArkBot Skill Factory 閉環設計（設計 + 規格）

### 待推進
- ArkBot Skill Runtime 人工驗證（`arkbot-skill-runtime-spec.md` 中 ← 待人工驗證 項目）
- nana_bot → ArkAgent OS 遷移（skill.json → skill.yaml、目錄結構重組）
- 測試框架建立
- linter / formatter 設定

---

## 重大決策紀錄

| 日期 | 決策 | 原因 |
|---|---|---|
| 2026-03-23 | arkbot-agent-generator 升級至 v1.1.0（Generator Platform） | 合併兩個 generator 為統一 CLI + Manifest 驅動 + Module Registry，消除 >70% 重複 |
| 2026-03-24 | DataWiseBot-Agent 修正回寫至 generator 模板（v1.2.0） | 確保未來產出的 ArkAgent OS 專案不再重複相同問題 |
| 2026-03-23 | Manifest 採用純 Python dict（非 YAML） | 避免 ArkBot 模式需額外安裝 pyyaml |
| 2026-03-20 | ArkAgent OS 採五模組架構 | Spec DSL + Agent Kernel + Memory + Tool Gateway + 多 Agent |
| 2026-03-18 | 專案重新定位為 Agent Skills Factory | 從單一應用轉為技能包產出工廠 |

---

## 環境備註

- ArkBot 設定：`nana_bot/.env`（GOOGLE_API_KEY、TELEGRAM_TOKEN、WEB_PORT=2141）
- Kiro Skills 研發系統：`.kiro/skills/`
- Kiro Skills 正式環境（備份）：`.agent/skills/`
- Skill README 範本：`.kiro/skills/skill-creator/templates/readme.md`
- 預設 Gemini 模型：`gemini-2.5-flash`

---

## 上次對話摘要

- 2026-03-24：將 DataWiseBot-Agent 12 Issues + 8 Fixes 回寫至 arkbot-agent-generator 模板（entry.py 分離 Telegram/Web 入口、config.py cp950 相容 start.bat、registry.py 新入口常數）。更新 generator-issues-report.md 至 v2.1（全部標註「已修正+回寫」）。新增附錄 C（DataWiseBot-Agent 未使用的 ArkAgent OS 功能清單）。arkbot-agent-generator 升級至 v1.2.0。
