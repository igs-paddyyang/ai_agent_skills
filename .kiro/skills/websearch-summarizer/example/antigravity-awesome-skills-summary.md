# Antigravity Awesome Skills — 文件摘要

**來源**: [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)
**版本**: V8.2.0
**技能總數**: 1,272+
**授權**: MIT License
**整理日期**: 2026-03-19

---

## 一句話摘要

一個跨平台的 AI Agent 技能庫，收錄 1,272+ 個 SKILL.md 格式的可重用技能，支援 Claude Code、Gemini CLI、Kiro IDE、Cursor、Copilot 等主流 AI 編碼助手。

---

## 核心概念

技能（Skill）是小型 Markdown 檔案，教導 AI Agent 如何完成特定任務。Agent 本身很聰明，但缺乏特定領域的工具和流程知識 — 技能填補了這個缺口。

---

## 9 大技能分類

| 分類 | 數量 | 聚焦領域 | 代表技能 |
|------|------|---------|---------|
| Architecture | 82 | 系統設計、ADR、C4、可擴展模式 | architecture, c4-context, senior-architect |
| Business | — | 成長、定價、CRO、SEO、GTM | copywriting, pricing-strategy, seo-audit |
| Data & AI | — | LLM 應用、RAG、Agent、分析 | rag-engineer, prompt-engineer, langgraph |
| Development | — | 語言精通、框架模式、程式碼品質 | typescript-expert, python-patterns, react-patterns |
| General | — | 規劃、文件、產品營運、寫作 | brainstorming, doc-coauthoring, writing-plans |
| Infrastructure | — | DevOps、雲端、Serverless、CI/CD | docker-expert, aws-serverless, vercel-deployment |
| Security | — | AppSec、滲透測試、漏洞分析、合規 | api-security-best-practices, vulnerability-scanner |
| Testing | — | TDD、測試設計、QA 工作流 | test-driven-development, testing-patterns |
| Workflow | — | 自動化、編排、Agent 工作流 | workflow-automation, inngest, trigger-dev |

---

## 平台相容性

| 工具 | 類型 | 技能路徑 |
|------|------|---------|
| Claude Code | CLI | `.claude/skills/` |
| Gemini CLI | CLI | `.gemini/skills/` |
| Codex CLI | CLI | `.codex/skills/` |
| Kiro IDE | IDE | `~/.kiro/skills/`（全域）/ `.kiro/skills/`（工作區） |
| Antigravity | IDE | `~/.gemini/antigravity/skills/`（全域）/ `.agent/skills/`（工作區） |
| Cursor | IDE | `.cursor/skills/` |
| OpenCode | CLI | `.agents/skills/` |
| AdaL CLI | CLI | `.adal/skills/` |

---

## 安裝方式

```bash
# 預設安裝（Antigravity 全域路徑）
npx antigravity-awesome-skills

# 指定工具
npx antigravity-awesome-skills --kiro        # Kiro CLI
npx antigravity-awesome-skills --claude      # Claude Code
npx antigravity-awesome-skills --cursor      # Cursor

# 自訂路徑（如 Kiro IDE 全域）
npx antigravity-awesome-skills --path ~/.kiro/skills
```

---

## Bundle 機制（角色套裝）

Bundle 不是獨立安裝，而是按角色分類的推薦技能清單。安裝一次即擁有全部技能，Bundle 只是幫你挑選起點。

常見組合：
- Web 開發 → Web Wizard bundle
- 資安 → Security Engineer bundle
- 通用 → Essentials bundle
- SaaS MVP → Essentials + Full-Stack Developer + QA & Testing
- 生產環境加固 → Security Developer + DevOps & Cloud + Observability

---

## Workflow 機制

Bundle 幫你選技能，Workflow 幫你按順序執行。提供人類可讀的 playbook 和機器可讀的 JSON。

內建 Workflow：
1. Ship a SaaS MVP
2. Security Audit for a Web App
3. Build an AI Agent System
4. QA and Browser Automation
5. Design a DDD Core Domain

---

## Top 10 入門技能

| 技能 | 用途 |
|------|------|
| @brainstorming | 實作前的規劃與構思 |
| @architecture | 系統與元件設計 |
| @test-driven-development | TDD 導向開發 |
| @doc-coauthoring | 結構化文件撰寫 |
| @lint-and-validate | 輕量品質檢查 |
| @create-pr | 打包成乾淨的 PR |
| @debugging-strategies | 系統化除錯 |
| @api-design-principles | API 設計一致性 |
| @frontend-design | UI 與互動品質 |
| @security-auditor | 安全導向審查 |

---

## 專案結構

| 路徑 | 用途 |
|------|------|
| `skills/` | 技能庫本體（SKILL.md 集合） |
| `docs/users/` | 使用者指南、Bundle、Workflow |
| `docs/contributors/` | 貢獻者指南、範本、品質標準 |
| `docs/maintainers/` | 發布流程、稽核、CI 維護 |
| `apps/web-app/` | 互動式技能瀏覽器（Vite） |
| `tools/` | 安裝器、驗證器、產生器 |
| `data/` | 產生的目錄、別名、Bundle、Workflow |

---

## 安全機制

- Runtime 加固保護 `/api/refresh-skills` mutation 流程
- Markdown 渲染避免 raw HTML passthrough
- SKILL.md 安全掃描檢查高風險指令模式（curl|bash、wget|sh 等）
- PR 自動化 skill-review GitHub Actions 檢查
- 路徑/符號連結檢查與解析器穩健性防護

---

## 官方來源（已整合）

| 來源 | 貢獻 |
|------|------|
| anthropics/skills | 文件操作（DOCX、PDF、PPTX、XLSX）、品牌指南 |
| vercel-labs/agent-skills | React 最佳實踐、Web 設計指南 |
| openai/skills | Agent 技能、Skill Creator、簡潔規劃 |
| supabase/agent-skills | Postgres 最佳實踐 |
| microsoft/skills | Azure、Bot Framework、多語言企業模式 |
| google-gemini/gemini-skills | Gemini API、SDK 互動 |
| apify/agent-skills | 網頁爬蟲、資料擷取、自動化 |
| remotion-dev/skills | React 影片製作（28 個模組化規則） |

---

## 與本專案的關係

本專案（Agent Skills Factory）的 `skill-creator` 整合版即源自此 repo 的社群版 skill-creator，結合 Anthropic 官方版的迭代改進管線。技能格式（SKILL.md + YAML frontmatter）完全相容。

---

## 行動建議

1. **可直接使用的技能**：brainstorming、architecture、doc-coauthoring 等通用技能可直接安裝到 `.kiro/skills/` 使用
2. **參考價值**：Security 和 Testing 分類的技能可作為未來建立 ArkBot 安全審計技能的參考
3. **Bundle 概念**：可借鏡 Bundle 機制，為本專案的技能體系設計角色套裝
4. **Workflow 概念**：可參考 Workflow 機制，設計技能串接的自動化流程（對應 arkbot優化-spec 的 Skill Factory 概念）
