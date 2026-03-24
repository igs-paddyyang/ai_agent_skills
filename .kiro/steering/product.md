---
inclusion: always
version: "1.0.0"
last_synced: "2026-03-24"
---

# 產品概述

Google Antigravity — Agent Skills Factory。一個用於建立 AI Agent 架構與 Agent Skills 的開發、測試、打包專案。

## 專案定位

這是一個**技能包產出工廠**，不是單一應用程式：

1. 用 `skill-spec-writer` 產出技能級規格，餵給 `skill-creator`
2. 用 `skill-creator` 建立、測試、迭代改進 Kiro Skills
3. 用 `software-spec-writer` 產出專案級規格文件驅動開發
4. 用 `arkbot-agent-generator` 一鍵生成完整的 AI Agent（ArkBot）專案
5. 在 ArkBot 上部署外部產出的 Skill Package

## 核心產出物

### Kiro Skills（11 個）
- `skill-creator` — 建立 / 測試 / 打包技能的元技能
- `skill-spec-writer` — 技能級規格文件（餵給 skill-creator）
- `software-spec-writer` — 專案級規格文件 + 任務執行計畫
- `arkbot-agent-generator` — ArkBot Agent 專案產生器（Foundation 基礎層 ～ 完整四層架構）
- `gemini-canvas-dashboard` — 任意 JSON → Gemini API → HTML 儀表板
- `document-summarizer` — 長文件 → 結構化摘要 + 行動建議
- `websearch-summarizer` — 網頁搜尋 → 結構化摘要
- `env-setup-installer` — 環境與服務安裝引導
- `env-smoke-test` — 環境煙霧測試
- `skill-sync` — 技能同步備份（.kiro → .agent）
- `game-design-document-writer` — 遊戲企劃文件（GDD + One Pager）

### ArkBot（產出的 Agent 範例）
- Telegram Bot + Web 對話介面（三層架構）
- 意圖分類 → Skill Registry → Executor 路由
- Skill Runtime：載入外部產出的 Skill Package 並執行

### 設計文件
- `docs/agent-arkbot-spec.md` — ArkBot 完整規格文件（四層架構：Foundation / Decision Engine / Skill Runtime / Integration）
- `docs/arkbot-agent-generator-spec.md` — arkbot-agent-generator Skill Spec（餵給 skill-creator）
- `docs/agent優化-spec.md` — Agent 雙層決策架構（Intent Router + Skill Resolver）
- `docs/arkbot優化-spec.md` — ArkBot Skill Factory 自動化架構（Spec → Skill → Test → Registry → Use）

## 目標使用者
開發者，透過 Kiro IDE 使用 Skills 體系快速產出 AI Agent 與擴展技能。
