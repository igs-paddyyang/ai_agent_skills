---
name: skill-tapestry
description: "建立技能間的關聯索引與知識網路，管理技能依賴、互補、替代與延伸關係。自動掃描 .kiro/skills/ 產生關聯圖，根據使用情境推薦相關技能。當使用者提到技能關聯、技能索引、skill tapestry、技能網路、技能推薦、技能地圖、技能依賴、技能管理、列出所有技能、技能總覽、skill map、技能關係圖時，請務必使用此技能。"
---

# 技能知識網路（Skill Tapestry）

技能越多，越難記住哪個技能做什麼、跟誰有關。
Skill Tapestry 幫你建立技能間的關聯索引，讓你快速找到需要的技能。

## 使用時機

- 技能數量超過 15 個，需要總覽
- 想知道某個技能跟哪些技能有關
- 需要根據使用情境推薦技能組合
- 新增技能後需要更新關聯索引
- 需要了解技能間的依賴關係

## 關聯類型定義

| 類型 | 符號 | 說明 | 範例 |
|------|------|------|------|
| 依賴 | `→` | A 的產出是 B 的輸入 | skill-spec-writer → skill-creator |
| 互補 | `↔` | A 和 B 搭配使用效果更好 | gemini-canvas-dashboard ↔ d3-visualization-guide |
| 延伸 | `⇒` | B 是 A 的進階版或擴展 | skill-creator ⇒ skill-seeker |
| 替代 | `⇄` | A 和 B 可互相替代 | （目前無） |

## 掃描與產生流程

### 步驟 1：掃描技能目錄

讀取 `.kiro/skills/` 下所有技能的 SKILL.md，提取：
- name
- description
- 附帶資源列表（references/）

### 步驟 2：分析關聯

根據以下線索判斷關聯：
- description 中提到的其他技能名稱
- 功能重疊或互補的描述
- 共同的觸發關鍵字
- 工作流中的上下游關係

### 步驟 3：產生關聯索引

輸出格式為 Markdown 表格 + 關聯圖。

## 關聯索引格式

### 技能總覽表

```markdown
| # | 技能名稱 | 分類 | 簡述 |
|---|---------|------|------|
| 1 | skill-creator | 元技能 | 建立/測試/打包技能 |
| 2 | skill-spec-writer | 規格 | 技能級規格文件 |
| 3 | software-spec-writer | 規格 | 專案級規格文件 |
| ... | ... | ... | ... |
```

### 關聯矩陣

```markdown
| 技能 | 依賴 | 互補 | 延伸 |
|------|------|------|------|
| skill-creator | skill-spec-writer | prompt-engineering-guide | skill-seeker |
| tdd-workflow | — | software-architecture-guide | — |
| gemini-canvas-dashboard | — | d3-visualization-guide | — |
```

### 文字關聯圖

```
skill-spec-writer ──→ skill-creator ←── skill-seeker
                          │
                          ⇒ prompt-engineering-guide
                          
software-spec-writer ──→ 專案開發
                          │
                          ↔ tdd-workflow
                          ↔ software-architecture-guide

arkbot-agent-generator ──→ ArkBot 專案
                          │
                          ↔ mcp-builder-guide（Tool Gateway）
                          ↔ software-architecture-guide（架構指引）

gemini-canvas-dashboard ↔ d3-visualization-guide

changelog-generator ↔ skill-creator（版本管理）

env-setup-installer → env-smoke-test
```

## 技能分類體系

| 分類 | 技能 | 說明 |
|------|------|------|
| 元技能 | skill-creator、skill-seeker、skill-tapestry | 管理技能本身 |
| 規格 | skill-spec-writer、software-spec-writer | 產出規格文件 |
| 開發指引 | tdd-workflow、software-architecture-guide、mcp-builder-guide、prompt-engineering-guide | 開發方法論 |
| 產生器 | arkbot-agent-generator、gemini-canvas-dashboard、d3-visualization-guide | 產出程式碼或視覺化 |
| 文件 | document-summarizer、websearch-summarizer、changelog-generator、game-design-document-writer | 文件處理 |
| 環境 | env-setup-installer、env-smoke-test | 環境管理 |
| 同步 | skill-sync | 技能備份 |

## 情境推薦

根據使用者的工作情境，推薦技能組合：

| 情境 | 推薦技能組合 |
|------|------------|
| 建立新技能 | skill-spec-writer → skill-creator → prompt-engineering-guide |
| 從文件建立技能 | skill-seeker → skill-creator |
| 開發新功能 | tdd-workflow + software-architecture-guide |
| 建立 ArkBot | arkbot-agent-generator + mcp-builder-guide |
| 產出儀表板 | gemini-canvas-dashboard（快速）或 d3-visualization-guide（精細） |
| 發布版本 | changelog-generator |
| 環境設定 | env-setup-installer → env-smoke-test |
| 研究外部資源 | websearch-summarizer 或 document-summarizer |

## 更新關聯索引的時機

- 新增技能後
- 修改技能的 description 後
- 技能間的關係改變後
- 定期檢視（建議每 5 個新技能後）

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/tapestry-format.md | 關聯索引格式規範與進階用法 | 需要自訂索引格式時 |
