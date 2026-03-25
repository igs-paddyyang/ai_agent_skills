# 知識指南類技能合併評估報告

**日期**: 2026-03-25
**作者**: paddyyang
**對應 Task**: skills-improvement-spec.md Task 6.4

---

## 評估對象

| 技能 | 版本 | 領域 | 有 scripts | 有 references |
|------|------|------|-----------|--------------|
| prompt-engineering-guide | 0.1.1 | Prompt 設計 | ❌ | ❌ |
| software-architecture-guide | 0.1.1 | 軟體架構 | ❌ | ❌ |
| mcp-builder-guide | 0.1.1 | MCP 開發 | ❌ | ❌ |
| tdd-workflow | 0.1.1 | 測試開發 | ❌ | ❌ |
| d3-visualization-guide | 0.1.1 | 資料視覺化 | ❌ | ❌ |

## 關鍵字重疊度分析

### 觸發關鍵字矩陣

| | prompt | architecture | mcp | tdd | d3 |
|---|---|---|---|---|---|
| prompt | — | ❌ | ❌ | ❌ | ❌ |
| architecture | ❌ | — | ❌ | ❌ | ❌ |
| mcp | ❌ | ❌ | — | ❌ | ❌ |
| tdd | ❌ | ❌ | ❌ | — | ❌ |
| d3 | ❌ | ❌ | ❌ | ❌ | — |

結論：5 個技能的觸發關鍵字完全不重疊，各自服務明確不同的領域。

### 功能定位分析

| 技能 | 本質 | 產出物 | 使用頻率預估 |
|------|------|--------|------------|
| prompt-engineering-guide | Kiro Skill 開發方法論 | 改善 description、指令設計 | 高（每次建立/改進技能都用） |
| software-architecture-guide | 軟體設計決策指引 | 架構建議、ADR | 中（新專案或重構時） |
| mcp-builder-guide | MCP Server 開發教學 | MCP Server 程式碼 | 低（僅建立 MCP Server 時） |
| tdd-workflow | 測試開發流程指引 | 測試程式碼 | 中（寫測試時） |
| d3-visualization-guide | D3.js 圖表開發 | D3 圖表程式碼 | 低（僅需要 D3 圖表時） |

## 合併方案評估

### 方案 A：合併為 `dev-guides`（單一技能 + references/ 分章節）

優點：
- 減少技能數量（21 → 17）
- 統一維護入口

缺點：
- description 必須涵蓋 5 個領域的觸發關鍵字，容易超過 1024 字元限制
- 觸發準確度下降（「幫我寫 D3 圖表」不應該載入 TDD 指引）
- 違反 Kiro Skill 的「單一職責」原則
- 合併後的 SKILL.md 會超過 500 行限制

### 方案 B：維持獨立

優點：
- 觸發精準，各自只在需要時載入
- 符合漸進式揭露原則
- 維護獨立，改一個不影響其他

缺點：
- 技能數量較多（但 21 個在可管理範圍內）

### 方案 C：部分合併（prompt + architecture 合併，其餘獨立）

不建議。prompt-engineering-guide 專注 Kiro Skill description 撰寫，software-architecture-guide 專注系統設計，兩者服務的使用情境完全不同。

## 結論

**建議：維持獨立（方案 B）**

理由：
1. 5 個技能觸發關鍵字零重疊，合併會降低觸發準確度
2. 合併後的 description 很可能超過 1024 字元限制
3. 各技能的 SKILL.md 內容量適中，不需要壓縮
4. 21 個技能在 Kiro 平台的管理範圍內，不構成負擔
5. prompt-engineering-guide 使用頻率高（每次建立技能都會用），不應與低頻技能混在一起

## 後續建議

- 維持 5 個技能獨立，不合併
- 考慮為 mcp-builder-guide 和 d3-visualization-guide 加入 scripts/（產出骨架程式碼），提升從「指引」到「工具」的實用性
- tdd-workflow 在 Task 6.6 會補強測試執行能力（scripts/run_tests.py）
