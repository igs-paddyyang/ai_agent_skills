---
inclusion: always
version: "1.3.0"
last_synced: "2026-04-10"
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
│   ├── skills/                          # Kiro 技能（核心產出物，21 個）
│   └── specs/
│       └── kiro-agent/                  # kiro-agent 規格文件（Kiro IDE 用）
│
├── .agent/
│   └── skills/                          # 正式環境（備份，由 skill-sync 同步）
│
├── kiro_agent/                          # kiro-agent 多 Agent 艦隊管理系統
│   ├── *.py                             # 19 個 Python 模組
│   ├── tests/unit/                      # 19 個單元測試（330 tests）
│   ├── docs/tutorial.md                 # 教學使用手冊
│   ├── pyproject.toml                   # 套件配置
│   ├── requirements.txt                 # 依賴清單
│   └── README.md                        # 專案說明
│
├── llm-mcp-server/                      # LLM MCP Server（多 Provider 切換）
│   ├── server.py                        # MCP Server 入口
│   ├── providers/                       # LLM Provider 實作
│   └── README.md                        # 說明文件
│
├── docs/                                # 設計文件與規格
├── output/                              # 產出物暫存
├── pyproject.toml                       # 工作區配置（pytest testpaths）
├── requirements.txt                     # 工作區 Python 套件
└── README.md                            # 專案說明
```

## 架構模式

### Kiro Skills 體系（核心）
- 每個技能為獨立目錄，包含 SKILL.md + README.md + 附帶資源
- 技能間透過 Kiro 平台觸發，不直接互相呼叫
- `skill-creator` 為元技能，負責建立和管理其他技能
- 版本管理採用 Semantic Versioning

### kiro-agent（多 Agent 艦隊管理系統）
- 自包含子專案：原始碼 + 測試 + 文件 + pyproject.toml 全在 `kiro_agent/` 下
- 19 個 Python 模組，分為 6 層：外部介面 / 核心引擎 / 協作 / 自主運維 / 輔助功能 / 基礎設施
- 330 個單元測試，執行：`py -m pytest kiro_agent/tests/unit/ -q`
- 規格文件保留在 `.kiro/specs/kiro-agent/`（供 Kiro IDE 使用）

### ArkBot / ArkAgent OS（產出的 Agent）
- ArkBot 模式：四層架構（Foundation / Decision Engine / Skill Runtime / Integration），~37 檔
- ArkAgent OS 模式：平台級架構，~91 檔
- 統一 CLI：`python generate.py <profile> <name>`

### 技能開發流程
- `.kiro/skills/` — 研發系統（使用 Kiro IDE 開發技能，skill-creator 優先在此建立）
- `.agent/skills/` — 正式環境（無 Kiro IDE 時的技能部署位置 / 備份）
- 使用 `skill-sync` 從 `.kiro/skills/` 同步到 `.agent/skills/`

## 慣例
- 技能名稱使用 kebab-case
- 每個技能必須有 SKILL.md 和 README.md
- 修改技能時同步更新 README.md 版本號與變更紀錄
- 設計文件放 `docs/`，規格文件以 `-spec.md` 結尾
