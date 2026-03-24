# 技能關聯索引（Skill Tapestry Index）

**產生日期**: 2026-03-24
**技能總數**: 21 個
**掃描來源**: `.kiro/skills/`

---

## 技能總覽表

| # | 技能名稱 | 分類 | 簡述 |
|---|---------|------|------|
| 1 | skill-creator | 元技能 | 建立/測試/打包技能 |
| 2 | skill-seeker | 元技能 | 文件來源自動轉換為 Skill 草稿 |
| 3 | skill-tapestry | 元技能 | 技能關聯索引與知識網路 |
| 4 | skill-spec-writer | 規格 | 技能級規格文件 |
| 5 | software-spec-writer | 規格 | 專案級規格文件 + 執行計畫 |
| 6 | tdd-workflow | 開發指引 | TDD Red-Green-Refactor 工作流 |
| 7 | software-architecture-guide | 開發指引 | Clean Architecture / SOLID / 設計模式 |
| 8 | mcp-builder-guide | 開發指引 | MCP Server 建立指引（Python SDK） |
| 9 | prompt-engineering-guide | 開發指引 | Prompt 設計方法論與 description 撰寫 |
| 10 | arkbot-agent-generator | 產生器 | ArkBot / ArkAgent OS 專案產生器 |
| 11 | gemini-canvas-dashboard | 產生器 | JSON → Gemini API → HTML 儀表板 |
| 12 | dashboard-skill-generator | 產生器 | JSON → DSL → Renderer → HTML 儀表板 |
| 13 | d3-visualization-guide | 產生器 | D3.js 互動圖表與資料視覺化 |
| 14 | document-summarizer | 文件 | 長文件 → 結構化摘要 |
| 15 | websearch-summarizer | 文件 | 網頁搜尋 → 結構化摘要 |
| 16 | changelog-generator | 文件 | Git commits → 結構化變更紀錄 |
| 17 | game-design-document-writer | 文件 | 遊戲企劃文件（GDD + One Pager） |
| 18 | fish-spec-writer | 文件 | 捕魚機遊戲機台規格文件 |
| 19 | env-setup-installer | 環境 | 環境與服務安裝引導 |
| 20 | env-smoke-test | 環境 | 環境煙霧測試 |
| 21 | skill-sync | 同步 | 技能同步備份（.kiro → .agent） |

---

## 關聯矩陣

| 技能 | 依賴（→） | 互補（↔） | 延伸（⇒） |
|------|----------|----------|----------|
| skill-creator | skill-spec-writer | prompt-engineering-guide, changelog-generator | skill-seeker |
| skill-seeker | — | document-summarizer, websearch-summarizer | skill-creator |
| skill-tapestry | — | skill-sync | — |
| skill-spec-writer | — | software-spec-writer | skill-creator |
| software-spec-writer | — | skill-spec-writer | — |
| tdd-workflow | — | software-architecture-guide | — |
| software-architecture-guide | — | tdd-workflow, arkbot-agent-generator | — |
| mcp-builder-guide | — | arkbot-agent-generator | — |
| prompt-engineering-guide | — | skill-creator | — |
| arkbot-agent-generator | — | software-architecture-guide, mcp-builder-guide | — |
| gemini-canvas-dashboard | — | d3-visualization-guide, dashboard-skill-generator | — |
| dashboard-skill-generator | — | gemini-canvas-dashboard | — |
| d3-visualization-guide | — | gemini-canvas-dashboard | — |
| document-summarizer | — | websearch-summarizer | — |
| websearch-summarizer | — | document-summarizer | — |
| changelog-generator | — | skill-creator | — |
| game-design-document-writer | — | fish-spec-writer | — |
| fish-spec-writer | — | game-design-document-writer | — |
| env-setup-installer | — | — | env-smoke-test |
| env-smoke-test | env-setup-installer | — | — |
| skill-sync | — | skill-tapestry | — |

---

## 文字關聯圖

```
┌─────────────────── 元技能層 ───────────────────┐
│                                                 │
│  skill-spec-writer ──→ skill-creator ←── skill-seeker
│                            │                    │
│                            ⇒ prompt-engineering-guide
│                            ↔ changelog-generator│
│                                                 │
│  skill-tapestry ↔ skill-sync                   │
└─────────────────────────────────────────────────┘

┌─────────────────── 開發指引層 ─────────────────┐
│                                                 │
│  tdd-workflow ↔ software-architecture-guide     │
│                       ↔                         │
│               arkbot-agent-generator            │
│                       ↔                         │
│               mcp-builder-guide                 │
└─────────────────────────────────────────────────┘

┌─────────────────── 產生器層 ───────────────────┐
│                                                 │
│  gemini-canvas-dashboard ↔ d3-visualization-guide
│          ↔                                      │
│  dashboard-skill-generator                      │
│                                                 │
│  arkbot-agent-generator（見開發指引層）          │
└─────────────────────────────────────────────────┘

┌─────────────────── 文件層 ─────────────────────┐
│                                                 │
│  document-summarizer ↔ websearch-summarizer     │
│  game-design-document-writer ↔ fish-spec-writer │
│  changelog-generator                            │
└─────────────────────────────────────────────────┘

┌─────────────────── 環境層 ─────────────────────┐
│                                                 │
│  env-setup-installer ⇒ env-smoke-test           │
└─────────────────────────────────────────────────┘
```

---

## 分類體系（7 大分類）

| 分類 | 技能數 | 技能 |
|------|--------|------|
| 元技能 | 3 | skill-creator、skill-seeker、skill-tapestry |
| 規格 | 2 | skill-spec-writer、software-spec-writer |
| 開發指引 | 4 | tdd-workflow、software-architecture-guide、mcp-builder-guide、prompt-engineering-guide |
| 產生器 | 4 | arkbot-agent-generator、gemini-canvas-dashboard、dashboard-skill-generator、d3-visualization-guide |
| 文件 | 5 | document-summarizer、websearch-summarizer、changelog-generator、game-design-document-writer、fish-spec-writer |
| 環境 | 2 | env-setup-installer、env-smoke-test |
| 同步 | 1 | skill-sync |

---

## 情境推薦表

| 情境 | 推薦技能組合 |
|------|------------|
| 建立新技能 | skill-spec-writer → skill-creator → prompt-engineering-guide |
| 從文件建立技能 | skill-seeker → skill-creator |
| 從網頁建立技能 | websearch-summarizer → skill-seeker → skill-creator |
| 開發新功能 | software-spec-writer → tdd-workflow + software-architecture-guide |
| 建立 ArkBot | arkbot-agent-generator + mcp-builder-guide + software-architecture-guide |
| 產出儀表板（快速） | gemini-canvas-dashboard 或 dashboard-skill-generator |
| 產出儀表板（精細） | d3-visualization-guide |
| 發布版本 | changelog-generator |
| 環境設定 | env-setup-installer → env-smoke-test |
| 研究外部資源 | websearch-summarizer 或 document-summarizer |
| 遊戲企劃 | game-design-document-writer + fish-spec-writer |
| 技能總覽 | skill-tapestry |
| 技能備份 | skill-sync |
| 改善 prompt 品質 | prompt-engineering-guide |
