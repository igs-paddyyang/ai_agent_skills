---
name: arkbot-agent-generator
author: paddyyang
description: "當使用者需要建立 ArkBot 或 ArkAgent OS 專案時，應使用此技能。支援兩種模式：ArkBot（四層架構）和 ArkAgent OS（五模組平台架構，含 Spec DSL、Memory System、Tool Gateway、多 Agent 支援）。當使用者提到 ArkBot、ArkAgent、智庫助理、網頁獵取 Bot、爬蟲 Bot、Telegram 智庫、建立 ArkBot、Agent ArkBot、ArkAgent OS、建立 Agent 專案、agent-arkbot、進階 ArkBot、多 Agent 平台時，請務必使用此技能。"
---

# Agent ArkBot / ArkAgent OS 產生器

生成 AI Agent 專案，支援兩種模式：

- **ArkBot 模式**：四層架構（Foundation / Decision Engine / Skill Runtime / Integration），產出單一 Bot 專案
- **ArkAgent OS 模式**：五模組平台架構（Agent Kernel / Intent Engine / Skill Runtime / Memory System / Tool Gateway），支援 Spec DSL、多 Agent、Architecture Reviewer

## 輸入

- 專案名稱（選用，預設 `arkbot` 或 `arkagent`）
- 模式選擇（選用）：ArkBot（預設）或 ArkAgent OS
- 自訂配置（選用）：Bot 名稱、預設語言、額外功能需求

## 四層架構概覽

```
┌─────────────────────────────────────────────────┐
│  Integration（整合層）                            │
│  arkbot_core.py 接入 Hybrid Router + Executor    │
├─────────────────────────────────────────────────┤
│  Skill Runtime（技能執行層）                      │
│  executor.py — Sandbox 隔離執行                  │
├─────────────────────────────────────────────────┤
│  Decision Engine（決策引擎層）                    │
│  skill_registry.py + skill_resolver.py           │
│  + skill_prompt.py + hybrid_router.py            │
├─────────────────────────────────────────────────┤
│  Foundation Layer（基礎層）                       │
│  arkbot_core.py + bot_main.py + web_server.py    │
│  + crawler_skill.py + intent_router.py           │
│  + format_utils.py                               │
└─────────────────────────────────────────────────┘
```

## 工作流程

採用兩階段工作流程，確保使用者在每個關鍵節點都能介入調整。

### 階段一：Scaffold（骨架搭建）

1. 生成完整目錄結構
2. 每個檔案產出骨架：模組 docstring + import + 函式/類別簽名 + TODO 註解
3. 產出 3 個範例 `skill.json`（web_scraper、knowledge_qa、canvas_generator）
4. 產出 `.env.example`、`requirements.txt`、`start.bat`
5. **暫停**，向使用者確認骨架結構

### 階段二：Implement（逐層實作）

按依賴順序逐層填入實作：

| 順序 | 層級 | 涵蓋模組 |
|------|------|---------|
| 1 | Foundation Layer | arkbot_core.py, bot_main.py, web_server.py, crawler_skill.py, intent_router.py, format_utils.py, init_db.py, index.html |
| 2 | Decision Engine | skill_registry.py, skill_resolver.py, skill_prompt.py, hybrid_router.py |
| 3 | Skill Runtime | executor.py（含 Sandbox 隔離） |
| 4 | Integration | 升級 arkbot_core.py 接入 Hybrid Router + Executor |

每層實作完成後暫停確認，再繼續下一層。

## 產出結構

```
{project-name}/
├── .env.example
├── requirements.txt
├── start.bat
├── data/
│   └── canvas/
├── docs/
│   └── bot_test_guide.md
├── scripts/
│   └── init_db.py
├── src/
│   ├── arkbot_core.py              # 核心邏輯（整合 Hybrid Router + Executor）
│   ├── bot_main.py                 # Telegram Bot 入口
│   ├── web_server.py               # FastAPI + WebSocket
│   ├── crawler_skill.py            # 爬蟲引擎
│   ├── intent_router.py            # 意圖分類（3 種 Intent）
│   ├── skill_registry.py           # Skill metadata 載入與過濾
│   ├── skill_resolver.py           # 三階段決策（Rule → LLM → Fallback）
│   ├── skill_prompt.py             # LLM Prompt 建構
│   ├── hybrid_router.py            # Intent + Resolver 整合
│   ├── executor.py                 # Skill 執行器（Sandbox 隔離）
│   └── format_utils.py             # MarkdownV2 跳脫
├── skills/                          # Skill Package 存放目錄
│   ├── web_scraper/
│   │   └── skill.json
│   ├── knowledge_qa/
│   │   └── skill.json
│   └── canvas_generator/
│       └── skill.json
├── web/
│   └── index.html
└── tests/
    ├── test_basic.py
    ├── test_skill_registry.py
    ├── test_skill_resolver.py
    └── test_executor.py
```

## 各層實作要點

### Foundation Layer（基礎層）

Foundation 的實作要點繼承自 `arkbot-generator`，詳見 `references/arkbot-foundation.md`。核心重點：

- `arkbot_core.py` 的 `process_message()` 是 async generator，yield 狀態更新和最終回覆
- 三層架構：arkbot_core 為核心，bot_main（Telegram）和 web_server（Web）為入口
- 意圖分類 3 種：DASHBOARD > RESEARCH > CASUAL
- 已知陷阱預防：MarkdownV2 跳脫、Prompt 分離、路徑解析、連線重試

### Decision Engine（決策引擎層）

詳見 `references/arkbot-decision-engine.md`。核心重點：

- `skill.json` Schema：skill_id、intent、description、examples、tags、priority、enabled
- `SkillRegistry`：掃描 skills/ 目錄，載入 metadata，`filter_by_intent()` + enabled 過濾
- `SkillResolver` 三階段決策：Rule Match（tags 比對）→ LLM Select（Gemini 精選）→ Fallback（priority 排序）
- `hybrid_router.py`：Intent Router（粗分類）+ Skill Resolver（精選），CASUAL 走快速路徑

### Skill Runtime（技能執行層）

詳見 `references/arkbot-decision-engine.md` §Skill Runtime。核心重點：

- `Executor`：動態載入 skill.py，在 subprocess 中執行 `run()` 方法
- Sandbox 隔離：捕獲 stdout/stderr，timeout 30 秒，錯誤不影響主程序
- 無對應 Skill 時回傳友善提示訊息

### Integration（整合層）

- 升級 `arkbot_core.py`：Hybrid Router → Registry → Executor 完整流程
- 有 Skill → Executor 執行 → 格式化結果回傳
- 無 Skill → 回傳「目前沒有對應的 Skill，請透過 skill-creator 建立」
- 向後相容：Foundation 功能不受影響

## skill.json 範例

每個 Skill Package 必須包含 `skill.json`：

```json
{
  "skill_id": "web_scraper",
  "intent": "RESEARCH",
  "description": "爬取指定網頁並產出結構化摘要，支援多種網站格式",
  "examples": ["幫我爬取這個網頁", "分析這個網站的內容", "摘要這篇文章"],
  "required_params": ["url"],
  "optional_params": ["format"],
  "tags": ["scrape", "爬取", "網頁", "摘要"],
  "priority": 80,
  "enabled": true
}
```

## 自我檢核

產出專案後確認：

**Foundation**：
- `.env.example` 包含所有金鑰（含 `WEB_PORT`）
- `init_db.py` 能建立資料庫
- 三個 prompt 嚴格分離（classify / summarize / chat）
- Web 對話頁能正常連線，WebSocket 狀態推送正常
- `start.bat` 能一鍵啟動

**Decision Engine**：
- 3 個範例 skill.json 包含所有必填欄位
- Registry 載入後 `filter_by_intent()` 回傳正確子集
- Resolver 三階段（Rule → LLM → Fallback）各有對應邏輯
- CASUAL 走快速路徑，不經 Resolver

**Skill Runtime**：
- Executor 可動態載入 skill.py
- Skill 拋出例外不影響主程序
- 超時強制終止

**Integration**：
- arkbot_core.py 已接入 Hybrid Router + Executor
- 無 Skill 時回傳友善提示
- Foundation 功能向後相容

---

## ArkAgent OS 模式

當使用者要求建立 ArkAgent OS 專案時，使用 `scripts/generate_arkagent.py` 產出五模組平台架構。

### 五模組架構概覽

```
┌─────────────────────────────────────────────────┐
│                 ArkAgent OS                     │
├─────────────────────────────────────────────────┤
│  Agent Kernel    │ Intent Engine │ Skill Runtime│
│  • lifecycle     │ • classifier  │ • registry   │
│  • config        │ • router      │ • executor   │
│  • spec_loader   │ • spec-driven │ • scheduler  │
├──────────────────┴──────────────┴──────────────┤
│  Memory System   │ Tool Gateway                 │
│  • short_term    │ • gemini / telegram / web    │
│  • long_term     │ • gateway (register/call)    │
├─────────────────────────────────────────────────┤
│  specs/          │ agents/       │ skills/       │
│  schema + yaml   │ agent.yaml    │ skill.yaml    │
└─────────────────────────────────────────────────┘
```

### 與 ArkBot 的差異

| 面向 | ArkBot | ArkAgent OS |
|------|--------|-------------|
| Skill 定義 | skill.json | skill.yaml（Spec DSL） |
| 配置驗證 | 無 | JSON Schema 驗證 |
| 記憶系統 | 無 | ShortTerm + LongTerm |
| 工具管理 | 散落各處 | Tool Gateway 統一管理 |
| Agent 數量 | 單一 | 多 Agent（agents/ 目錄） |
| 入口 | Telegram + Web | Telegram + Web + CLI |
| 架構審查 | 無 | Architecture Reviewer |

### 工作流程

1. 確認使用者要 ArkAgent OS 模式
2. 執行 `scripts/generate.py arkagent` 產出完整專案（~80 個檔案）
3. 引導使用者設定 `.env` 和驗證 Spec
4. 詳細架構說明請讀取 `references/arkagent-os.md`

### 自我檢核（ArkAgent OS）

- specs/ 包含 3 個 JSON Schema + runtime.yaml + 2 個範例
- kernel/ 包含 agent_base.py + config.py + logger.py + spec_loader.py
- memory/ 包含 short_term.py + long_term.py
- tools/ 包含 gateway.py + 3 個工具（gemini / telegram / web）
- controller/ 包含 domain_controller.py + system / python / mcp 三個子 Controller
- planner/ 包含 planner.py + execution_plan.py
- gateway/ 包含 app.py + auth.py + rate_limiter.py + websocket_handler.py
- config/ 包含 mcp.json
- agents/default/ 包含 agent.yaml
- skills/ 使用 skill.yaml（非 skill.json）
- scripts/validate_specs.py 可驗證所有 Spec
- scripts/review_architecture.py 可評分專案架構
- Executor 支援 Action 偵測 + Plan 執行
- arkbot_core.py 整合 DomainController + Memory + Planner
- Intent Parser 支援 Spec 驅動動態意圖（從 agent.yaml 讀取）
- 純文字回傳完全向後相容

## 參考資源

### 統一產生器（Generator Platform）
- 統一 CLI 入口：`scripts/generate.py`（Manifest 驅動，支援 --dry-run / --no-compat / --modules）
- 用法：`python generate.py arkbot [name]` 或 `python generate.py arkagent [name]`
- 列出可用 profiles：`python generate.py --list`

### ArkBot 模式
- Foundation 層實作要點：讀取 `references/arkbot-foundation.md`
- Decision Engine + Skill Runtime 實作要點：讀取 `references/arkbot-decision-engine.md`
- Web 對話頁完整版：`assets/index.html`
- 完整規格文件（設計依據）：`docs/agent-arkbot-spec.md`

### ArkAgent OS 模式
- ArkAgent OS 架構與模組說明：讀取 `references/arkagent-os.md`
- Skill Package 開發指南：讀取 `references/arkbot-skill-runtime.md`
- 升級規格文件：`docs/arkagent-upgrade-spec.md`

### 向後相容（Deprecated）
- `scripts/generate_arkbot.py`：已棄用，請改用 `generate.py arkbot`
- `scripts/generate_arkagent.py`：已棄用，請改用 `generate.py arkagent`
