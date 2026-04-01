---
inclusion: always
version: "1.2.0"
last_synced: "2026-03-25"
---

# 專案結構

```
├── .kiro/
│   ├── steering/                        # AI 協作文件
│   │   ├── claude.md                    # 開發規範（always）
│   │   ├── product.md                   # 產品概述（always）
│   │   ├── tech.md                      # 技術棧（always）
│   │   ├── structure.md                 # 專案結構（always）
│   │   ├── memory.md                    # 專案記憶（manual）
│   │   └── ai_workflow.md              # 協作 SOP（manual）
│   └── skills/                          # Kiro 技能（核心產出物）
│       ├── skill-creator/               # 技能建立器（含 eval 測試框架）
│       ├── software-spec-writer/        # 軟體工程規格文件撰寫師
│       ├── gemini-canvas-dashboard/     # 通用 Gemini Canvas 儀表板
│       ├── skill-spec-writer/           # 技能規格撰寫師
│       ├── websearch-summarizer/        # 網頁搜尋摘要師
│       ├── env-setup-installer/         # 環境與服務安裝
│       ├── env-smoke-test/              # 環境煙霧測試
│       ├── skill-sync/                  # 技能同步備份
│       ├── document-summarizer/         # 文件摘要師
│       ├── game-spec-writer/             # 遊戲機台規格撰寫師（捕魚機/老虎機/棋牌）
│       ├── game-design-document-writer/ # 遊戲企劃文件撰寫師
│       ├── skill-seeker/               # 文件轉技能探索器
│       ├── tdd-workflow/               # 測試驅動開發工作流
│       ├── software-architecture-guide/ # 軟體架構指引
│       ├── mcp-builder-guide/          # MCP Server 建立指引
│       ├── prompt-engineering-guide/   # Prompt 工程指引
│       ├── changelog-generator/        # 變更紀錄產生器
│       ├── d3-visualization-guide/     # D3.js 視覺化指引
│       ├── skill-tapestry/             # 技能知識網路
│       └── ci-automation/             # CI 自動化（lint + validate + sync）
│
├── .agent/
│   └── skills/                          # 正式環境（備份，由 skill-sync 同步）
│
├── docs/                                # 設計文件與規格
│   ├── agent-arkbot-spec.md             # ArkBot 完整規格文件 v3.1
│   ├── arkbot-agent-generator-spec.md   # arkbot-agent-generator Skill Spec
│   ├── arkbot-generator-refactor-spec.md # 模板模組化重構規格文件
│   ├── arkbot-skill-runtime-spec.md     # Skill Runtime 規格文件
│   ├── arkagent-upgrade-spec.md         # ArkAgent OS 升級規格文件 v1.1（10 Task ✅）
│   ├── arkagent-platform-spec.md        # 平台級架構升級規格文件 v1.1（11 Task ✅）
│   ├── generator-platform-spec.md       # Generator Platform 統一產生器規格文件 v1.1（6 Task ✅）
│   ├── generator-issues-report.md       # Generator 產出問題追蹤 v2.1（12 Issues + 8 Fixes）
│   ├── arkbot-to-arkagent-design.md     # ArkAgent OS 設計願景
│   ├── dashboard-impl.md               # 儀表板實作摘要
│   ├── skill-seeker-spec.md            # skill-seeker Skill Spec
│   ├── agent優化.md / agent優化-spec.md  # Agent 雙層決策架構
│   └── arkbot優化.md / arkbot優化-spec.md # ArkBot Skill Factory 設計
│
└── README.md                            # 專案說明
```

## 架構模式

### Kiro Skills 體系（核心）
- 每個技能為獨立目錄，包含 SKILL.md + README.md + 附帶資源
- 技能間透過 Kiro 平台觸發，不直接互相呼叫
- `skill-creator` 為元技能，負責建立和管理其他技能
- 版本管理採用 Semantic Versioning

### ArkBot / ArkAgent OS（產出的 Agent）
- ArkBot 模式：四層架構（Foundation / Decision Engine / Skill Runtime / Integration），~37 檔
- ArkAgent OS 模式：平台級架構（Agent Kernel / Intent Engine / Skill Runtime / Memory System / Tool Gateway / Domain Controller / Skill Planner / API Gateway），~91 檔
- 統一 CLI：`python generate.py <profile> <name>`，舊 generator 為 deprecated wrapper

### 技能開發流程
- `.kiro/skills/` — 研發系統（使用 Kiro IDE 開發技能，skill-creator 優先在此建立）
- `.agent/skills/` — 正式環境（無 Kiro IDE 時的技能部署位置 / 備份）
- 使用 `skill-sync` 從 `.kiro/skills/` 同步到 `.agent/skills/`

## 慣例
- 技能名稱使用 kebab-case
- 每個技能必須有 SKILL.md 和 README.md
- 修改技能時同步更新 README.md 版本號與變更紀錄
- 設計文件放 `docs/`，規格文件以 `-spec.md` 結尾
