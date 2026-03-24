# Awesome Claude Skills — 軟體開發 & 遊戲開發相關 Skills 摘要

**來源**: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
**授權**: Apache License 2.0
**整理日期**: 2026-03-24

---

## 一句話摘要

從 awesome-claude-skills 精選與軟體開發、遊戲開發直接相關的 Claude Skills，涵蓋程式碼工具、架構設計、測試、視覺化、媒體創作等領域。

---

## 核心概念

awesome-claude-skills 是由 ComposioHQ 維護的 Claude Skills 策展清單，收錄跨平台（Claude.ai / Claude Code / API）可用的技能。每個 Skill 為獨立資料夾，包含 `SKILL.md`（YAML frontmatter + Markdown 指令）及選用的 scripts / templates / resources。本摘要聚焦於軟體工程與遊戲開發可直接應用的 Skills。

---

## 軟體開發相關 Skills 總覽

### Development & Code Tools

| Skill 名稱 | 說明 | 備註 |
|------------|------|------|
| artifacts-builder | 使用 React / Tailwind / shadcn/ui 建立多元件 HTML artifacts | 前端開發 |
| aws-skills | AWS CDK 最佳實踐、成本優化、Serverless 架構模式 | 雲端架構 |
| Changelog Generator | 從 git commits 自動產生使用者導向的 changelog | 版本管理 |
| Claude Code Terminal Title | 為 Claude Code 終端視窗加上動態標題描述 | 開發體驗 |
| D3.js Visualization | 產出 D3 圖表與互動式資料視覺化 | by @chrisvoncsefalvay |
| finishing-a-development-branch | 引導完成開發分支的工作流程 | Git 工作流 |
| iOS Simulator | 與 iOS Simulator 互動進行測試與除錯 | by @conorluddy |
| jules | 委派程式任務給 Google Jules AI agent（非同步修 bug、寫文件、測試） | by @sanjay3290 |
| LangSmith Fetch | 從 LangSmith Studio 抓取執行 trace 進行 LangChain/LangGraph 除錯 | AI 可觀測性 |
| MCP Builder | 引導建立 MCP Server（Python / TypeScript），整合外部 API 與 LLM | MCP 開發 |
| move-code-quality-skill | 分析 Move 語言套件的程式碼品質（Move 2024 Edition） | 區塊鏈 |
| Playwright Browser Automation | 使用 Playwright 自動化測試與驗證 Web 應用 | by @lackeyjb |
| prompt-engineering | 教授 prompt engineering 技巧，含 Anthropic 最佳實踐 | AI 開發 |
| pypict-claude-skill | 使用 PICT 設計組合測試案例，產生最佳化測試套件 | 測試設計 |
| software-architecture | 實作 Clean Architecture、SOLID 原則等軟體設計模式 | 架構設計 |
| subagent-driven-development | 分派獨立 subagent 執行任務，搭配 code review 檢查點 | 開發方法論 |
| test-driven-development | TDD 工作流：先寫測試再寫實作 | 開發方法論 |
| using-git-worktrees | 建立隔離的 git worktree，含智慧目錄選擇與安全驗證 | Git 進階 |
| Webapp Testing | 使用 Playwright 測試本地 Web 應用，含截圖功能 | 前端測試 |

### Code & DevOps（Composio 自動化）

| Skill 名稱 | 說明 |
|------------|------|
| GitHub Automation | 自動化 GitHub：issues、PRs、repos、branches、actions、code search |
| GitLab Automation | 自動化 GitLab：issues、MRs、projects、pipelines、branches |
| Bitbucket Automation | 自動化 Bitbucket：repos、PRs、branches、issues、workspaces |
| CircleCI Automation | 自動化 CircleCI：pipelines、workflows、jobs |
| Sentry Automation | 自動化 Sentry：issues、events、projects、releases、alerts |
| Datadog Automation | 自動化 Datadog：monitors、dashboards、metrics、incidents |
| PagerDuty Automation | 自動化 PagerDuty：incidents、services、schedules |
| Vercel Automation | 自動化 Vercel：deployments、projects、domains、env vars |
| Render Automation | 自動化 Render：services、deploys、project management |
| Supabase Automation | 自動化 Supabase：SQL queries、table schemas、edge functions、storage |

---

## 遊戲開發 & 創意媒體相關 Skills

| Skill 名稱 | 分類 | 說明 |
|------------|------|------|
| D3.js Visualization | 視覺化 | 產出互動式圖表，可用於遊戲數據分析儀表板 |
| imagen | 圖像生成 | 使用 Gemini API 生成 UI mockups、icons、illustrations |
| Canvas Design | 視覺設計 | 建立 PNG/PDF 視覺作品（海報、設計稿） |
| Image Enhancer | 圖像處理 | 提升圖片解析度與清晰度 |
| Slack GIF Creator | 動畫 | 建立動畫 GIF，含尺寸驗證與可組合動畫基元 |
| Theme Factory | 主題設計 | 套用專業字型與配色主題，含 10 組預設主題 |
| Video Downloader | 影片 | 下載 YouTube 等平台影片 |
| FFUF Web Fuzzing | 安全測試 | 整合 ffuf 模糊測試工具，分析漏洞 |

---

## 資料分析相關（輔助開發）

| Skill 名稱 | 說明 |
|------------|------|
| CSV Data Summarizer | 自動分析 CSV 並產生視覺化洞察 |
| deep-research | 使用 Gemini Deep Research Agent 執行多步驟研究 |
| postgres | 對 PostgreSQL 執行安全的唯讀 SQL 查詢 |
| root-cause-tracing | 追蹤錯誤根因分析 |

---

## Skill 結構規範

```
skill-name/
├── SKILL.md          # 必要：技能指令與 YAML 元資料
├── scripts/          # 選用：輔助腳本
├── templates/        # 選用：文件範本
└── resources/        # 選用：參考資料
```

SKILL.md 使用 YAML frontmatter 定義 `name` 和 `description`，與本專案的 Kiro Skill 結構高度相似。

---

## 與本專案的關係

| 面向 | 對應 |
|------|------|
| Skill 結構 | 兩者都採用 `SKILL.md` + 附帶資源的模式，可互相參考 |
| 架構設計 | `software-architecture` 可參考其 Clean Architecture / SOLID 指引 |
| 測試方法 | `test-driven-development`、`pypict-claude-skill` 可借鏡測試策略 |
| MCP 開發 | `MCP Builder` 的 MCP Server 建立指引值得參考 |
| 視覺化 | `D3.js Visualization` 可補充 `gemini-canvas-dashboard` 的圖表能力 |
| 遊戲開發 | `imagen`、`Canvas Design` 可輔助 `game-design-document-writer` 的視覺素材 |

---

## 行動建議

1. 研究 `software-architecture` Skill 的 Clean Architecture 指引，評估是否整合到 `arkbot-agent-generator` 的產出模板中
2. 參考 `test-driven-development` 的工作流設計，作為本專案規劃中的 Test Runner 框架參考
3. 研究 `MCP Builder` 的 MCP Server 建立模式，可作為未來 ArkAgent OS Tool Gateway 的參考
4. 評估 `D3.js Visualization` 是否能補充 `gemini-canvas-dashboard` 的圖表類型
