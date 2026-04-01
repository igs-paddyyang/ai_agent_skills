# 🏭 Agent Skills Factory

AI Agent 架構與 Agent Skills 的開發、測試、打包專案。

透過 [Kiro IDE](https://kiro.dev) 的 Skills 體系，快速產出可重用的 AI 技能包與完整的 AI Agent 專案。

## 專案定位

這是一個**技能包產出工廠**，不是單一應用程式：

1. 用 `skill-spec-writer` 產出技能規格 → 餵給 `skill-creator`
2. 用 `skill-creator` 建立、測試、迭代改進 Kiro Skills
3. 用 `software-spec-writer` 產出專案級規格文件驅動開發

## Kiro Skills（21 個）

### 元技能
| 技能 | 說明 |
|------|------|
| `skill-creator` | 建立 / 測試 / 打包技能的元技能 |
| `skill-seeker` | 文件來源自動轉換為 Kiro Skill 草稿 |
| `skill-tapestry` | 技能關聯索引與知識網路 |

### 規格與文件
| 技能 | 說明 |
|------|------|
| `skill-spec-writer` | 技能級規格文件（餵給 skill-creator） |
| `software-spec-writer` | 專案級規格文件 + 任務執行計畫 |
| `document-summarizer` | 長文件 → 結構化摘要 + 行動建議 |
| `websearch-summarizer` | 網頁搜尋 → 結構化摘要 |
| `changelog-generator` | Git commits → 結構化變更紀錄 |
| `game-design-document-writer` | 遊戲企劃文件（GDD + One Pager） |
| `game-spec-writer` | 遊戲機台規格文件（捕魚機/老虎機/棋牌） |

### 開發指引
| 技能 | 說明 |
|------|------|
| `tdd-workflow` | TDD Red-Green-Refactor 工作流 |
| `software-architecture-guide` | Clean Architecture / SOLID / 設計模式指引 |
| `mcp-builder-guide` | MCP Server 建立指引（Python SDK） |
| `prompt-engineering-guide` | Prompt 設計方法論與 description 撰寫公式 |

### 產生器與視覺化
| 技能 | 說明 |
|------|------|
| `gemini-canvas-dashboard` | JSON → Gemini API → HTML 儀表板 |
| `dashboard-skill-generator` | JSON → DSL → Renderer → HTML 儀表板 |
| `d3-visualization-guide` | D3.js 互動圖表與資料視覺化 |

### 環境與 CI
| 技能 | 說明 |
|------|------|
| `env-setup-installer` | 環境與服務安裝引導 |
| `env-smoke-test` | 環境煙霧測試 |
| `skill-sync` | 技能同步備份（.kiro → .agent） |
| `ci-automation` | CI 自動化（lint + validate + sync） |

## 快速開始

### 環境需求

- Python 3.9+（建議 3.12）
- [Kiro IDE](https://kiro.dev)

### 安裝

```bash
# 複製環境變數範本
cp .env.example .env
# 編輯 .env 填入 API Key

# 安裝套件
pip install -r requirements.txt
```

### 常用指令

```bash
# 技能驗證
py .kiro/skills/skill-creator/scripts/quick_validate.py .kiro/skills/<skill-name>

# 技能同步（.kiro/skills → .agent/skills）
py .kiro/skills/skill-sync/scripts/sync_skills.py

# 本地 CI（lint + validate + sync）
py .kiro/skills/ci-automation/scripts/ci_local.py
```

## 專案結構

```
├── .kiro/
│   ├── steering/          # AI 協作文件（claude / product / tech / structure / memory）
│   └── skills/            # Kiro 技能（21 個，核心產出物）
├── .agent/
│   └── skills/            # 正式環境（由 skill-sync 同步備份）
├── docs/                  # 設計文件與規格
├── output/                # 產出物（儀表板、關聯索引等）
├── .env.example           # 環境變數範本
├── requirements.txt       # Python 套件
└── LICENSE                # MIT
```

## 技能開發流程

```
skill-spec-writer ──產 Spec──→ skill-creator ──產出技能──→ quick_validate.py
                                    │
                    prompt-engineering-guide ←── 改善 description
                                    │
                    changelog-generator ←── 更新變更紀錄
                                    │
                    skill-sync ──→ .agent/skills/（正式環境）
```

## 技術棧

| 類別 | 工具 |
|------|------|
| 語言 | Python 3.9+ |
| IDE | Kiro IDE |
| AI API | Google Gemini (`models/gemini-2.5-flash-lite`) |
| Bot | python-telegram-bot |
| Web | FastAPI + uvicorn |
| 爬蟲 | requests + beautifulsoup4 |

## 授權

[MIT License](LICENSE) © 2026 paddyyang
