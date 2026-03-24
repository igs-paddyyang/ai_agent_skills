# Agent Skills 標準與範例參考

> 本文件整理自兩個外部來源，供 skill-spec-writer 在產出 Skill Spec 時參考。
> 產出的 Spec 應對齊這些標準，確保 skill-creator 能產出符合規範的技能。

**資料來源**：
- [anthropics/skills](https://github.com/anthropics/skills) — Anthropic 官方 Agent Skills（Apache 2.0）
- [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) — 社群版 1,265+ 技能集合（MIT）

**最後更新**：2026-03-18

---

## 1. Agent Skills 規範（agentskills.io）

以下內容改寫自 [Agent Skills Specification](https://agentskills.io/specification)。

### 1.1 目錄結構

```
skill-name/
├── SKILL.md          # 必要：中繼資料 + 指令
├── scripts/          # 選用：可執行程式碼
├── references/       # 選用：按需載入文件
├── assets/           # 選用：範本、圖片等
└── ...               # 其他檔案
```

### 1.2 SKILL.md 格式

YAML frontmatter + Markdown 內容。

| 欄位 | 必要 | 限制 |
|------|------|------|
| `name` | 是 | ≤ 64 字元，小寫字母 + 數字 + 連字號，不可以連字號開頭或結尾，不可連續連字號，須與目錄名一致 |
| `description` | 是 | ≤ 1024 字元，描述技能功能與使用時機，包含觸發關鍵字 |
| `license` | 否 | 授權名稱或授權檔案參考 |
| `compatibility` | 否 | ≤ 500 字元，環境需求（平台、套件、網路） |
| `metadata` | 否 | 字串鍵值對，自訂屬性 |
| `allowed-tools` | 否 | 空格分隔的預核准工具清單（實驗性） |

### 1.3 漸進式揭露（Progressive Disclosure）

| 層級 | 載入時機 | 建議大小 |
|------|---------|---------|
| 中繼資料（name + description） | 啟動時全部載入 | ~100 tokens |
| SKILL.md 本體 | 技能觸發時載入 | < 5000 tokens（建議 < 500 行） |
| 附帶資源（scripts/references/assets） | 按需載入 | 無限制，但單檔保持聚焦 |

### 1.4 description 撰寫要點

- 同時描述「做什麼」和「什麼時候用」
- 包含具體的觸發關鍵字，幫助 agent 識別相關任務
- 稍微「積極」一些，對抗觸發不足的傾向

---

## 2. 官方技能範例（anthropics/skills）

Anthropic 官方 repo 包含 17 個技能，涵蓋 4 大類：

| 類別 | 技能 |
|------|------|
| Creative & Design | algorithmic-art, brand-guidelines, canvas-design, frontend-design, slack-gif-creator, theme-factory, web-artifacts-builder |
| Development & Technical | claude-api, mcp-builder, webapp-testing |
| Enterprise & Communication | doc-coauthoring, internal-comms |
| Document Skills | docx, pdf, pptx, xlsx |
| Meta | skill-creator |

### 範例 A：brand-guidelines（參考/指引型）

以下為改寫摘要，展示「參考型技能」的結構模式。

```yaml
name: brand-guidelines
description: >
  Applies Anthropic's official brand colors and typography to any sort of
  artifact that may benefit from having Anthropic's look-and-feel. Use it
  when brand colors or style guidelines, visual formatting, or company
  design standards apply.
```

結構特點：
- 概述 → 品牌指南（顏色、字型）→ 功能說明 → 技術細節
- 無 scripts/，純指令型
- description 同時包含功能（applies brand colors）和觸發情境（when brand colors or style guidelines apply）

### 範例 B：webapp-testing（工作流程型）

以下為改寫摘要，展示「工具型技能」的結構模式。

```yaml
name: webapp-testing
description: >
  Toolkit for interacting with and testing local web applications using
  Playwright. Supports verifying frontend functionality, debugging UI
  behavior, capturing browser screenshots, and viewing browser logs.
```

結構特點：
- 決策樹（Decision Tree）引導選擇方法
- Helper Scripts 作為黑盒使用（先 `--help`，不讀原始碼）
- 範例驅動：具體的命令和程式碼片段
- references/ + examples/ 按需載入

### 範例 C：mcp-builder（多階段工作流程型）

以下為改寫摘要，展示「複雜工作流程技能」的結構模式。

```yaml
name: mcp-builder
description: >
  Guide for creating high-quality MCP servers that enable LLMs to interact
  with external services through well-designed tools. Use when building MCP
  servers to integrate external APIs or services.
```

結構特點：
- 4 個 Phase：Research → Implementation → Review → Evaluation
- 每個 Phase 有明確的子步驟和交付物
- 大量使用 reference/ 按需載入（best practices、語言指南、評估指南）
- SKILL.md 本體作為路線圖，細節在 reference/ 中

---

## 3. 社群技能範例（antigravity-awesome-skills）

社群版 v8.1.0 包含 1,265+ 技能，分為 9 大類：

| 類別 | 焦點 | 代表技能 |
|------|------|---------|
| Architecture | 系統設計、ADR、可擴展模式 | architecture, c4-context, senior-architect |
| Business | 成長、定價、SEO、GTM | copywriting, pricing-strategy, seo-audit |
| Data & AI | LLM 應用、RAG、Agent、分析 | rag-engineer, prompt-engineer, langgraph |
| Development | 語言精通、框架模式、程式碼品質 | typescript-expert, python-patterns, react-patterns |
| General | 規劃、文件、產品營運 | brainstorming, doc-coauthoring, writing-plans |
| Infrastructure | DevOps、雲端、CI/CD | docker-expert, aws-serverless, vercel-deployment |
| Security | AppSec、滲透測試、合規 | api-security-best-practices, vulnerability-scanner |
| Testing | TDD、測試設計、QA 流程 | test-driven-development, testing-patterns |
| Workflow | 自動化、編排、Agent | workflow-automation, inngest, trigger-dev |

### 社群技能的額外 frontmatter 欄位

社群版在標準欄位之外加入了：

```yaml
risk: unknown        # 風險等級標記
source: community    # 來源標記
date_added: "2026-02-27"  # 加入日期
```

### 範例 D：architecture（選擇性閱讀型）

以下為改寫摘要，展示「模組化參考技能」的結構模式。

```yaml
name: architecture
description: >
  Architectural decision-making framework. Requirements analysis,
  trade-off evaluation, ADR documentation. Use when making architecture
  decisions or analyzing system design.
```

結構特點：
- 「選擇性閱讀規則」— 內容地圖表格，agent 只讀需要的檔案
- 關聯技能（Related Skills）交叉引用
- 核心原則精簡（Start simple, add complexity only when proven necessary）
- 驗證清單（Validation Checklist）

### 範例 E：brainstorming（嚴格流程型）

以下為改寫摘要，展示「硬性閘門流程技能」的結構模式。

```yaml
name: brainstorming
description: >
  Use before creative or constructive work. Transforms vague ideas into
  validated designs through disciplined reasoning and collaboration.
```

結構特點：
- 7 個步驟，有硬性閘門（Understanding Lock — 必須確認才能繼續）
- 明確的退出條件（Exit Criteria）
- 決策日誌（Decision Log）貫穿全程
- 禁止在流程中實作程式碼

---

## 4. 技能結構模式總結

從官方和社群範例中歸納出 4 種常見的技能結構模式：

| 模式 | 適用場景 | 代表技能 | 特徵 |
|------|---------|---------|------|
| 參考/指引型 | 標準、規範、品牌指南 | brand-guidelines, architecture | 查閱式，無固定流程 |
| 工具型 | 提供多個操作/功能 | webapp-testing | 決策樹 + 範例驅動 |
| 工作流程型 | 多階段循序流程 | mcp-builder, brainstorming | Phase/Step + 交付物 |
| 選擇性閱讀型 | 大量參考資料 | architecture | 內容地圖 + 按需載入 |

模式可混合搭配。skill-spec-writer 在產出 Spec 時，應根據技能的性質建議最適合的結構模式。

---

## 5. description 撰寫範例

好的 description 同時包含功能描述和觸發情境：

| 技能 | description 寫法 | 分析 |
|------|-----------------|------|
| brand-guidelines | "Applies brand colors and typography... Use when brand colors or style guidelines apply." | 功能 + 觸發情境 |
| webapp-testing | "Toolkit for testing local web applications using Playwright. Supports verifying frontend functionality..." | 功能 + 具體能力列舉 |
| mcp-builder | "Guide for creating MCP servers... Use when building MCP servers to integrate external APIs." | 功能 + 觸發情境 |
| brainstorming | "Use before creative or constructive work. Transforms vague ideas into validated designs." | 觸發時機 + 功能 |
| architecture | "Architectural decision-making framework. Requirements analysis, trade-off evaluation, ADR documentation." | 功能列舉 + 觸發情境 |

撰寫公式：`[做什麼] + [什麼時候用 / 觸發關鍵字]`

---

## 6. 與本專案的對應關係

| 外部標準 | 本專案對應 |
|---------|-----------|
| agentskills.io 規範 | `.kiro/steering/claude.md` 的 SKILL.md 撰寫規範 |
| anthropics/skills template | `.kiro/skills/skill-creator/templates/default.md` |
| 漸進式揭露 3 層 | skill-creator SKILL.md 的「漸進式揭露」章節 |
| description ≤ 1024 字元 | claude.md 禁止事項表格 |
| name kebab-case ≤ 64 字元 | claude.md SKILL.md 撰寫規範 |

本專案的技能規範已與 Agent Skills 標準對齊。skill-spec-writer 產出的 Spec 遵循這些標準，確保 skill-creator 產出的技能可跨平台使用。
