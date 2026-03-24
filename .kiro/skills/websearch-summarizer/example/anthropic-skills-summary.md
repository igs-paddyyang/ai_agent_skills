# Anthropic Agent Skills (anthropics/skills) — 文件摘要

**來源**: [https://github.com/anthropics/skills](https://github.com/anthropics/skills)
**Stars**: ~73k
**授權**: Apache 2.0（範例技能）；Source-Available（文件技能 docx/pdf/pptx/xlsx）
**規格網站**: [agentskills.io](https://agentskills.io)
**整理日期**: 2026-03-19

---

## 一句話摘要

Anthropic 官方的 Agent Skills 公開倉庫，提供自包含的指令包讓 Claude 動態載入以執行專業任務，同時定義了跨平台的開放標準規格。

---

## 核心概念

Agent Skills 是由資料夾組成的指令、腳本與資源包，AI Agent 可以動態發現並載入以提升特定任務的準確性與效率。核心設計原則是「漸進式揭露」（Progressive Disclosure）：技能以三層結構載入 — 先讀 metadata（~100 tokens），需要時才載入 SKILL.md 本體（<5000 tokens），最後按需載入 scripts/references/assets，避免一次性塞滿 context window。

這個格式已由 Anthropic 發布為開放標準（agentskills.io），目標是跨平台通用，不僅限於 Claude。

---

## 技能分類總覽

| 分類 | 說明 | 代表技能 |
|------|------|---------|
| Document Skills（Source-Available） | 驅動 Claude 原生文件能力的生產級技能 | docx、pdf、pptx、xlsx |
| Creative & Design | 藝術、音樂、設計工作流程 | algorithmic-art 等 |
| Development & Technical | Web 應用測試、MCP Server 生成等技術任務 | MCP server generation、web app testing |
| Enterprise & Communication | 品牌、溝通、企業工作流程 | branding、communications |

---

## SKILL.md 規格

每個技能是一個資料夾，最少包含一個 `SKILL.md` 檔案（YAML frontmatter + Markdown 指令）：

```
skill-name/
├── SKILL.md          # 必要：metadata + 指令
├── scripts/          # 選用：可執行腳本
├── references/       # 選用：按需載入的文件
├── assets/           # 選用：範本、資源
└── ...
```

### Frontmatter 欄位

| 欄位 | 必要 | 限制 |
|------|------|------|
| name | ✅ | ≤64 字元，小寫 + 連字號，需與資料夾名稱一致 |
| description | ✅ | ≤1024 字元，描述功能與使用時機 |
| license | ❌ | 授權名稱或檔案參考 |
| compatibility | ❌ | ≤500 字元，環境需求 |
| metadata | ❌ | 任意 key-value 映射 |
| allowed-tools | ❌ | 空格分隔的預核准工具清單（實驗性） |

### 撰寫原則

- SKILL.md 本體建議 <500 行，詳細內容拆到 references/
- 漸進式揭露：metadata → SKILL.md 本體 → 附帶資源
- 檔案參考使用相對路徑，保持一層深度
- 可用 `skills-ref validate ./my-skill` 驗證格式

---

## 平台支援

| 平台 | 使用方式 |
|------|---------|
| Claude Code | `/plugin marketplace add anthropics/skills`，再安裝 document-skills 或 example-skills |
| Claude.ai | 付費方案內建，可上傳自訂技能 |
| Claude API | 透過 Skills API 端點上傳 |

---

## 漸進式揭露（Progressive Disclosure）

這是 Agent Skills 的核心設計原則，也是與直接塞 system prompt 的關鍵差異：

| 層級 | 載入內容 | Token 成本 |
|------|---------|-----------|
| Level 1 | name + description（frontmatter） | ~100 tokens |
| Level 2 | SKILL.md 完整本體 | <5000 tokens（建議） |
| Level 3 | scripts/ / references/ / assets/ | 按需載入 |

Agent 可以註冊數十個技能，但只為實際使用的技能付出 token 成本。

---

## Partner 生態

Anthropic 開始展示第三方技能，目前已有 [Notion Skills for Claude](https://github.com/anthropics/skills) 作為合作夥伴範例。agentskills.io 規格目標是成為跨供應商標準。

---

## 與本專案的關係

| 面向 | Anthropic Agent Skills | 我們的 Kiro Skills |
|------|----------------------|-------------------|
| 核心檔案 | SKILL.md（YAML frontmatter + Markdown） | SKILL.md（相同格式） |
| 目錄結構 | scripts/ + references/ + assets/ | scripts/ + references/ + assets/（完全一致） |
| name 限制 | ≤64 字元，kebab-case | ≤64 字元，kebab-case（一致） |
| description 限制 | ≤1024 字元 | ≤1024 字元（一致） |
| 漸進式揭露 | 三層載入 | 三層載入（一致） |
| SKILL.md 行數 | <500 行建議 | <500 行規範（一致） |
| 額外欄位 | license、compatibility、metadata、allowed-tools | 無（可考慮擴充） |
| 驗證工具 | `skills-ref validate` | `quick_validate.py` |
| 分發方式 | Claude Code Plugin Marketplace | skill-sync（.kiro → .agent） |
| README.md | 非必要 | 必要（含版本資訊 + 變更紀錄） |

我們的 Kiro Skills 體系與 Anthropic Agent Skills 標準高度相容。主要差異在於我們額外要求 README.md 做版本管理，以及使用 skill-creator 做建立/測試/打包流程。

---

## 行動建議

1. 考慮在 SKILL.md frontmatter 中加入 `license` 和 `compatibility` 欄位，與 Agent Skills 標準完全對齊，未來可直接發布到 Claude Code Marketplace
2. 研究 `allowed-tools` 實驗性欄位，評估是否適用於 ArkBot 的 Skill Runtime 權限控制
3. 參考 Document Skills（docx/pdf/pptx/xlsx）的實作模式，作為未來建立文件處理類技能的範本
4. 評估將現有 10 個 Kiro Skills 打包為 Agent Skills 標準格式發布的可行性，擴大技能的跨平台可用性
