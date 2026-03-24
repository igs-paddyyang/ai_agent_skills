# Agent ArkBot / ArkAgent OS 產生器

> 生成 AI Agent 專案，支援兩種模式：ArkBot（四層架構）和 ArkAgent OS（五模組平台架構，含 Spec DSL、Memory System、Tool Gateway、多 Agent 支援）。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 1.7.1 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-18 |
| 最後更新 | 2026-03-24 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

支援兩種模式產出 AI Agent 專案：

- **ArkBot 模式**（預設）：完整可執行架構（entry/ → src/ → controller/ + memory/ + planner/），產出 ~52 個檔案
- **ArkAgent OS 模式**（進階）：平台級架構（Agent Kernel / Intent Engine / Skill Runtime / Memory System / Tool Gateway）+ Domain Controller + Skill Planner + API Gateway + compat/ 相容層，產出 ~94 個檔案，支援 Spec DSL、多 Agent、Architecture Reviewer

採用兩階段工作流程：Scaffold（骨架搭建）確認結構後，再 Implement（逐層實作）填入細節。

## 使用方式

觸發此技能的方式：

```
「建立一個 ArkBot 專案」
「幫我生成 agent-arkbot」
「建立 ArkAgent OS 專案」
「建立具備 Memory System 的 Agent 平台」
「我要做一個多 Agent 平台」
「建立智庫助理」
```

### 統一 CLI（Generator Platform）

```bash
# 列出可用 profiles
python generate.py --list

# ArkBot 模式（~52 檔）
python generate.py arkbot
python generate.py arkbot my-bot --output-dir ./projects

# ArkAgent OS 模式（~94 檔）
python generate.py arkagent
python generate.py arkagent my-agent

# 進階選項
python generate.py arkagent my-agent --no-compat    # 跳過 compat/ 相容層
python generate.py arkagent my-agent --dry-run       # 只印檔案清單
python generate.py arkagent my-agent --modules kernel,memory,planner  # 只產出指定模組
```

## 兩種模式差異分析

### 產出規模

| | arkbot（預設） | arkagent（進階） |
|---|---|---|
| 產出檔案數 | ~52 | ~94 |
| 頂層目錄 | src/ entry/ memory/ controller/ planner/ agents/ config/ skills/ web/ data/ docs/ tests/ scripts/ | kernel/ intent/ runtime/ memory/ tools/ controller/ planner/ gateway/ config/ agents/ entry/ compat/ skills/ specs/ web/ data/ docs/ tests/ scripts/ |
| 使用模板模組 | 10 個（entry / core / decision / runtime / skills / tests / config / memory / controller / planner） | 14 個（+specs / kernel / tools / gateway） |

### 架構差異

ArkBot 採 entry/ → src/ 結構，核心模組平鋪在 src/，入口獨立於 entry/：

```
entry/
├── telegram_entry.py   # Telegram 入口
├── web_entry.py        # Web 入口（FastAPI + WebSocket）
└── cli_entry.py        # CLI 互動模式
src/
├── arkbot_core.py      # 核心 + 路由 + fallback
├── intent_router.py    # 意圖分類
├── skill_registry.py   # 註冊表
├── ...                 # 共 11 個核心模組
memory/                 # ShortTermMemory + LongTermMemory
controller/             # DomainController + System + Python + MCP
planner/                # SkillPlanner + ExecutionPlan
```

ArkAgent OS 按職責拆成獨立模組目錄，相容層改名為 compat/：

```
kernel/     → Agent 生命週期 + 配置 + 日誌 + Spec 載入
intent/     → 意圖分類 + 路由（從 src/ 抽出）
runtime/    → 註冊表 + 解析器 + 執行器 + 排程（從 src/ 抽出）
memory/     → 短期記憶 + 長期記憶
tools/      → 統一工具閘道
agents/     → 多 Agent 定義
entry/      → 入口層（Telegram + Web + CLI）
compat/     → 相容層（保留舊模組，方便遷移，目錄名明確標示過渡性質）
```

### 核心能力差異

| 能力 | ArkBot | ArkAgent OS |
|---|---|---|
| Skill 定義格式 | skill.yaml | skill.yaml（Spec DSL） |
| 配置驗證 | 無 | JSON Schema 驗證（3 個 schema） |
| 記憶系統 | ShortTermMemory + LongTermMemory | ShortTermMemory + LongTermMemory |
| 工具管理 | 散落在各模組 | ToolGateway 統一 register/call |
| Agent 數量 | 單一 Bot | 多 Agent（agents/ 目錄，各自 agent.yaml） |
| 入口 | Telegram + Web + CLI | Telegram + Web + CLI |
| Domain Controller | DomainController + System + Python + MCP | DomainController + System + Python + MCP |
| Skill Planner | SkillPlanner + ExecutionPlan | SkillPlanner + ExecutionPlan |
| 架構審查 | 無 | Architecture Reviewer（5 維度評分） |
| 測試模板 | 4 個 | 14 個（+kernel / memory / tools / specs / controller / planner / gateway） |
| 相容層 | 無（src/ 即核心） | compat/（過渡用，可 --no-compat 跳過） |
| requirements.txt | 含 pyyaml + jsonschema | 含 pyyaml + jsonschema |

### 程式碼複用

兩個產生器共用同一套 `templates/` 模板模組，透過 `__COMPAT_DIR__` 佔位符實現路徑參數化。ArkBot 的 `src/` 和 ArkAgent 的 `compat/` 使用相同模板，只是 `__COMPAT_DIR__` 替換為不同值（`src` vs `compat`）。

arkbot 現在也包含 entry/、memory/、controller/、planner/ 等模組，與 arkagent 共用相同的 gen_* 函式。差異在於 arkagent 額外產出 OS 原生模組（kernel/、intent/、runtime/、gateway/、tools/、specs/）和 compat/ 相容層。

### 一句話總結

arkbot 產出一個完整可執行的 Agent（entry/ → src/ → controller/ + memory/ + planner/）；arkagent 在此基礎上加入 OS 原生模組骨架和 compat/ 相容層，為未來遷移到原生架構做準備。

## 產出結構

### ArkBot 產出結構（~52 檔）

```
{project-name}/
├── .env.example
├── requirements.txt                    # 含 pyyaml + jsonschema
├── start.bat                           # entry/ 路徑啟動，PYTHONPATH=src
├── entry/                              # 入口層
│   ├── telegram_entry.py
│   ├── web_entry.py
│   └── cli_entry.py
├── src/                                # 核心模組（11 個）
│   ├── arkbot_core.py
│   ├── intent_router.py
│   ├── hybrid_router.py
│   ├── skill_registry.py
│   ├── skill_resolver.py
│   ├── skill_prompt.py
│   ├── executor.py
│   ├── scheduler.py
│   ├── crawler_skill.py
│   ├── dashboard_skill.py
│   └── format_utils.py
├── memory/
│   ├── __init__.py
│   ├── short_term.py
│   └── long_term.py
├── controller/
│   ├── __init__.py
│   ├── domain_controller.py
│   ├── system_controller.py
│   ├── python_controller.py
│   └── mcp_controller.py
├── planner/
│   ├── __init__.py
│   ├── planner.py
│   └── execution_plan.py
├── agents/
│   └── default/
│       └── agent.yaml
├── config/
│   ├── mcp.json
│   └── telegram.json
├── skills/                              # skill.yaml 版
│   ├── dashboard/  (skill.yaml + skill.py)
│   ├── crawler/    (skill.yaml + skill.py)
│   ├── chat/       (skill.yaml + skill.py)
│   └── notify/     (skill.yaml + skill.py)
├── data/
│   ├── dashboard/{type}/sample.json
│   └── schedules.json
├── web/
│   └── index.html
├── scripts/
│   └── init_db.py
├── docs/
│   └── bot_test_guide.md
└── tests/
    └── (4 個基礎測試)
```

### ArkAgent OS 產出結構（~94 檔）

```
{project-name}/
├── .env.example
├── requirements.txt
├── start.bat                           # PYTHONPATH=compat
├── compat/                             # 相容層（從 src/ 改名，明確標示過渡性質）
│   ├── arkbot_core.py
│   ├── intent_router.py
│   ├── ... (11 個相容層模組)
├── entry/                              # import compat/
│   ├── telegram_entry.py
│   ├── web_entry.py
│   └── cli_entry.py
├── kernel/                             # OS 原生（預留）
├── intent/                             # OS 原生（預留）
├── runtime/                            # OS 原生（預留）
├── gateway/                            # API Gateway（預留）
├── tools/                              # Tool Gateway（預留）
├── memory/                             # 共用
├── controller/                         # 共用
├── planner/                            # 共用
├── agents/
├── config/
├── specs/
├── skills/
├── data/
├── web/
├── scripts/
├── docs/
└── tests/
    └── (14 個完整測試)
```

## 檔案結構

```
.kiro/skills/arkbot-agent-generator/
├── SKILL.md                        # 主要技能指令（雙模式：ArkBot + ArkAgent OS）
├── README.md                       # 本文件
├── references/
│   ├── arkbot-foundation.md        # Foundation Layer 實作要點
│   ├── arkbot-decision-engine.md   # Decision Engine + Skill Runtime 實作要點
│   ├── arkbot-skill-runtime.md     # Skill Package 開發指南
│   └── arkagent-os.md              # ArkAgent OS 五模組架構說明
├── scripts/
│   ├── generate.py                 # 統一 CLI 入口（Generator Platform）
│   ├── generator/                  # Generator 核心模組
│   │   ├── __init__.py
│   │   ├── core.py                 # Generator 類別（create_file / run）
│   │   ├── manifest.py             # Manifest 定義（arkbot / arkagent profiles）
│   │   └── registry.py             # MODULE_REGISTRY（19 個模組生成函式）
│   ├── generate_arkbot.py          # Deprecated wrapper → generate.py arkbot
│   ├── generate_arkagent.py        # Deprecated wrapper → generate.py arkagent
│   └── templates/                   # 模板模組（14 個檔案）
│       ├── __init__.py              # 統一匯出所有模板常數
│       ├── entry.py                 # 入口層：BOT_MAIN_PY, WEB_SERVER_PY, CLI_ENTRY_PY
│       ├── core.py                  # 核心層：CORE_PY, INTENT_ROUTER_PY, DASHBOARD_SKILL_PY 等
│       ├── decision.py              # 決策引擎：REGISTRY, RESOLVER, PROMPT, HYBRID_ROUTER
│       ├── runtime.py               # 執行層：EXECUTOR_PY, SCHEDULER_PY
│       ├── skills.py                # Skill Package（JSON + YAML 版）+ sample data
│       ├── tests.py                 # 測試模板：14 個 test_*.py
│       ├── config.py               # 設定：START_BAT, ENV_EXAMPLE（ArkBot + ArkAgent）
│       ├── specs.py                 # Spec DSL：JSON Schema + 範例 YAML + 驗證腳本 + Reviewer
│       ├── kernel.py               # Agent Kernel：agent_base + config + logger + spec_loader
│       ├── memory.py               # Memory System：short_term + long_term
│       ├── tools.py                # Tool Gateway：gateway + gemini + telegram + web
│       ├── controller.py           # Domain Controller：domain + system + python + mcp
│       ├── planner.py              # Skill Planner：planner + execution_plan
│       └── gateway.py              # API Gateway：app + auth + rate_limiter + websocket
└── assets/
    └── index.html                  # Web 對話頁完整版
```

## 變更紀錄

### v1.7.1（2026-03-24）
- Dashboard Engine 修正：強化 `dsl_prompt.txt` 防止 Gemini 捏造 source 路徑
- 智慧 `build_fallback_dsl`：自動偵測資料形狀產生 kpi_group / line_chart / bar_chart（取代舊版只產 table）
- DSL 驗證全部失敗時自動 fallback（不再回傳 error），確保儀表板永遠能產出
- 新增 `_detect_array_shape()` + `_find_fields()` 輔助函式（含 category_hints 防誤判）

### v1.7.0（2026-03-24）
- 新增 DASHBOARD_CANVAS 意圖支援（Gemini Canvas 自由排版模式）
- `INTENT_ROUTER_PY` 新增 DASHBOARD_CANVAS 到 DEFAULT_INTENTS + canvas 關鍵字快速路徑
- `CORE_PY` Planner skip 條件擴展為 `intent not in ("DASHBOARD", "DASHBOARD_CANVAS")`
- 舊 `DASHBOARD_SKILL_PY` 重命名為 `GEMINI_CANVAS_SKILL_PY`（Gemini Canvas 模式）
- 新增 `DASHBOARD_SKILL_PY`（三層架構：JSON → DSL → Renderer → HTML，使用內嵌 dashboard_engine）
- 新增 `gen_dashboard_engine` — 從 assets/ 複製 dashboard_engine 模組（engine.py + assets/）
- 新增 `SKILL_PKG_CANVAS_YAML` + `SKILL_PKG_CANVAS_PY`（gemini-canvas skill package）
- `gen_src` / `gen_compat` 產出 gemini_canvas_skill.py + dashboard_skill.py（雙儀表板模式）
- `gen_skills_yaml` 新增 gemini-canvas skill package
- `AGENT_EXAMPLE_YAML` 新增 DASHBOARD_CANVAS 意圖 + gemini-canvas skill
- `ARKAGENT_START_BAT` 簡化為 `py main.py` 一鍵啟動（3 步驟）
- arkbot / arkagent manifest 新增 `dashboard_engine` 模組

### v1.6.1（2026-03-24）
- 修正 `MAIN_PY` 模板 `logging.basicConfig()` 缺少 `stream=sys.stdout`

### v1.6.0（2026-03-24）
- 新增 `main.py` 統一入口模板（Web + Telegram + Scheduler 共用 asyncio event loop）
- 新增 Logging 架構：噪音來源壓制（httpx / telegram.ext / google_genai / uvicorn.access）
- `py main.py` 預設三個服務全開，Ctrl+C graceful shutdown

### v1.5.0（2026-03-24）
- gen_common 新增 `web/dashboard_hub.html` 產出（報告中心入口頁）
- 新增 `DASHBOARD_HUB_HTML` 模板常數（templates/entry.py）
- arkbot / arkagent 兩種 profile 均預設產出 dashboard_hub.html

### v1.4.0（2026-03-24）
- Generator Profile 重構（`docs/generator-profile-refactor-spec.md`，10 Task 全部完成）：
  - arkbot profile 升級為完整可執行架構：新增 entry/、memory/、controller/、planner/、agents/、config/、skills_yaml 模組
  - arkbot 移除 skills_json（改用 skills_yaml）、gen_src() 移除 bot_main.py 和 web_server.py（由 entry/ 取代）
  - arkbot 產出從 ~38 檔增加到 ~52 檔，與 DataWiseBot-Agent 實際架構對齊
  - arkagent 相容層目錄從 `src/` 改名為 `compat/`，明確標示過渡性質
  - 模板參數化：使用 `__COMPAT_DIR__` 佔位符，entry/runtime/gateway/skills/config 模板自動適配 src/ 或 compat/
  - 新增 `_compat_dir(g)` + `_replace_compat()` 輔助函式（registry.py）
  - arkbot 共用 `ARKAGENT_REQUIREMENTS_TXT`（差異僅 pyyaml + jsonschema，對 arkbot 無害）
  - arkbot config 改用 `ARKAGENT_ENV_EXAMPLE` / `ARKAGENT_REQUIREMENTS_TXT` / `ARKAGENT_START_BAT`
- core.py + generate.py 移除 emoji 字元（修正 Windows cp950 編碼錯誤）
- 更新兩種模式差異分析（產出規模、架構差異、核心能力對比）

### v1.3.0（2026-03-24）
- 附錄 D 回寫（第二輪差異分析 → 模板改進）：
  - P1-1: sample JSON 改為類型子目錄結構（`data/dashboard/{type}/sample.json`）
  - P3-1: `FORMAT_UTILS_PY` 新增反斜線 `\` 跳脫（Windows 路徑 MarkdownV2 修正）
  - P2-1: 新增 `TELEGRAM_CONFIG_JSON` 常數（TG 路由設定骨架）
  - P2-2: 新增 `SKILL_PKG_NOTIFY_YAML` + `SKILL_PKG_NOTIFY_PY` 常數（notify skill 骨架）
  - P3: `SCHEDULES_JSON` 新增 notify 排程範例（含 params 欄位）
  - P3: `TELEGRAM_ENTRY_PY` dashboard 路徑改為相對路徑（從 `data/dashboard/` 開始）
- `gen_config_mcp()` 新增產出 `config/telegram.json`
- `gen_skills_yaml()` 新增產出 `skills/notify/`（skill.yaml + skill.py）
- `__init__.py` 新增匯出：TELEGRAM_CONFIG_JSON、SKILL_PKG_NOTIFY_YAML、SKILL_PKG_NOTIFY_PY
- `BOT_TEST_GUIDE` 範例 JSON 路徑更新為子目錄格式
- ArkAgent OS 產出檔案從 ~91 增加到 ~95 個（+telegram.json +notify skill）

### v1.2.0（2026-03-23）
- DataWiseBot-Agent 測試回寫：12 個 Issue + 8 個 Fix 修正回寫至 generator 模板
- 新增 `TELEGRAM_ENTRY_PY` 常數（ArkAgent OS Telegram 入口，使用 process_message() 統一流程）
- 新增 `WEB_ENTRY_PY` 常數（ArkAgent OS Web 入口，含 Dashboard Hub API + 類型分目錄）
- `gen_entry()` 改用 `TELEGRAM_ENTRY_PY` / `WEB_ENTRY_PY`（取代舊的 BOT_MAIN_PY / WEB_SERVER_PY）
- `ARKAGENT_START_BAT` 修正：entry/ 路徑 + PYTHONPATH=src + 移除 emoji（cp950 相容）
- `CORE_PY` 修正：sys.path 加入 PROJECT_ROOT + Memory API 對齊 + DASHBOARD 跳過 Planner
- `INTENT_ROUTER_PY` 修正：intents list→dict 轉換 + DASHBOARD 關鍵字快速路徑
- `SKILL_REGISTRY_PY` 重寫至 decision.py：支援 skill.yaml + intent list 正規化 + filter_by_intent
- `EXECUTOR_PY` 修正：subprocess UTF-8 編碼（cp950 相容）
- `SCHEDULER_PY` 修正：移除 emoji + 新增 `|||` params 支援
- `DASHBOARD_SKILL_PY` 修正：類型分目錄產出 + DATA 變數綁定 + _detect_type_from_data
- `CRAWLER_SKILL_PY` 修正：錯誤訊息 emoji 改為 [ERROR]
- `MCP_CONTROLLER_PY` 修正：骨架標示明確（logger.warning + [MCP 骨架] 前綴）
- `CLI_ENTRY_PY` 修正：移除 print() emoji
- `__init__.py` 新增匯出：TELEGRAM_ENTRY_PY、WEB_ENTRY_PY
- `generator-issues-report.md` 更新至 v2.1，所有 Issue/Fix 標註回寫狀態
- 新增附錄 C：DataWiseBot-Agent 未使用的 ArkAgent OS 功能清單

### v1.1.0（2026-03-23）
- Generator Platform 統一產生器：合併 generate_arkbot.py + generate_arkagent.py 為單一 `generate.py` CLI
- 新增 `generator/` 核心模組：core.py（Generator 類別）+ manifest.py（Profile 定義）+ registry.py（19 個模組生成函式）
- 支援 `--dry-run`（只印檔案清單）、`--no-compat`（跳過 src/ 相容層）、`--modules`（指定模組子集）
- generate_arkbot.py / generate_arkagent.py 改為 deprecated thin wrapper
- Manifest 驅動：新增 profile 只需修改 manifest.py，無需新增 .py 檔

### v1.0.0（2026-03-23）
- 平台級架構升級：新增 Domain Controller（三種執行模式：MCP / Python / System）
- 新增 Skill Planner（LLM 驅動多步驟規劃 + ExecutionPlan DAG）
- 新增 API Gateway 獨立化（認證 + 限流 + WebSocket 封裝）
- Executor 新增 Action 偵測 + Plan 執行能力
- arkbot_core.py 整合 DomainController + ShortTermMemory + SkillPlanner
- Intent Parser 升級為 Spec 驅動動態意圖（從 agent.yaml 讀取）
- 新增 3 個模板模組：controller.py / planner.py / gateway.py
- 新增 6 個測試模板：test_domain_controller / test_system / test_python / test_mcp / test_planner / test_gateway
- arkagent-os.md 新增 §12-14（Domain Controller / Planner / Gateway）
- templates/ 從 11 個檔案擴展為 14 個
- 產出檔案從 ~68 個增加到 ~80 個
- generate_arkagent.py 新增產出：controller/ + planner/ + gateway/ + config/

### v0.9.1（2026-03-23）
- 新增「兩種模式差異分析」章節（產出規模、架構差異、核心能力、程式碼複用）

### v0.9.0（2026-03-20）
- 新增 ArkAgent OS 模式：五模組平台架構（Agent Kernel / Intent Engine / Skill Runtime / Memory System / Tool Gateway）
- 新增 `generate_arkagent.py`（ArkAgent OS 產生器，產出 ~68 個檔案）
- 新增 4 個模板模組：specs.py / kernel.py / memory.py / tools.py
- 新增 Spec DSL 系統：skill.yaml / agent.yaml / runtime.yaml + JSON Schema 驗證
- 新增 Agent Kernel：AgentBase 類別 + lifecycle hooks + spec_loader
- 新增 Memory System：ShortTermMemory（deque）+ LongTermMemory（SQLite）
- 新增 Tool Gateway：BaseTool 介面 + ToolGateway（register/call）+ 3 個工具
- 新增 CLI 入口（entry/cli_entry.py）
- 新增 Architecture Reviewer（Prompt 模板 + review_architecture.py）
- 新增 4 個測試模板：test_kernel / test_memory / test_tools / test_specs
- 新增 YAML 版 Skill Package（skill.yaml 取代 skill.json）
- 新增 `references/arkagent-os.md`（ArkAgent OS 架構說明）
- requirements.txt 新增 pyyaml / jsonschema
- templates/ 從 7 個檔案擴展為 11 個
- generate_arkbot.py 凍結不動，保持向後相容

### v0.8.0（2026-03-20）
- 模板模組化重構：generate_arkbot.py 從 1840 行拆解為 ~120 行主程式 + templates/ 子模組（7 個檔案）
- 新增 `templates/` 目錄：entry.py / core.py / decision.py / runtime.py / skills.py / tests.py / config.py
- 新增 DASHBOARD_SKILL_PY 模板（src/dashboard_skill.py 產出）
- 新增 skills/dashboard/ 完整 Skill Package（skill.json + skill.py）
- 新增 3 個 sample JSON 模板（sample_revenue / sample_slots / sample_fish）
- 移除 dashboard_generator 空殼（被真正的 skills/dashboard/ 取代）
- 更新 BOT_TEST_GUIDE 模板（對齊 nana_bot 8 大案例）
- arkbot-foundation.md 新增 §10 儀表板產生器說明
- 清理 nana_bot：開發文件移至根目錄 docs/，清除 __pycache__
- 產出檔案從 33 個增加到 ~38 個

### v0.7.1（2026-03-20）
- 新增 `references/arkbot-skill-runtime.md`（Skill Package 開發指南：格式規格、執行模式、路由流程、API 使用）

### v0.7.0（2026-03-20）
- Skill Runtime 正式化：arkbot_core.py 移除 DASHBOARD/RESEARCH 硬編碼，全部走 Skill Runtime
- 新增 Executor async 模式（in-process 動態載入，支援 async run_async）
- 新增 response_type 處理邏輯（dashboard → 解析 html_path/summary）
- 新增 Skill API 端點模板（GET /api/skills、POST /api/skill/{skill_id}、API Key 驗證）
- 新增 Scheduler 排程引擎模板（asyncio + croniter、dry-run、schedules.json）
- 新增內建 Skill Package 模板（crawler/chat 的 skill.json + skill.py）
- start.bat 新增 --with-scheduler 選項
- requirements.txt 新增 croniter
- .env.example 新增 SKILL_API_KEY
- arkbot-foundation.md 新增 §10-12（Skill Runtime / Skill API / Scheduler）
- 產出檔案從 26 個增加到 33 個

### v0.6.0（2026-03-18）
- generate_arkbot.py 升級為完整四層架構產出（Foundation + Decision Engine + Skill Runtime + Integration）
- 新增 5 個 src 模板：skill_registry.py、skill_resolver.py、skill_prompt.py、hybrid_router.py、executor.py
- 新增 3 個範例 skill.json：web_scraper、knowledge_qa、dashboard_generator
- 新增 3 個測試模板：test_skill_registry.py、test_skill_resolver.py、test_executor.py
- arkbot_core.py 模板升級為 Integration 版本（整合 Hybrid Router + Executor + Foundation fallback）
- 新增 data/dashboard/.gitkeep 目錄
- 產出檔案從 16 個增加到 26 個

### v0.5.0（2026-03-18）
- start.bat 新增自動安裝套件步驟（pip install -r requirements.txt）
- start.bat 新增資料庫初始化步驟（init_db.py）
- start.bat 新增 .env WEB_PORT 讀取與錯誤檢查
- generate_arkbot.py START_BAT 模板同步更新

### v0.4.0（2026-03-18）
- 預設 WEB_PORT 從 8000 改為 2141
- generate_arkbot.py 全面清除 REVENUE/GAME_ANALYSIS 模板（BOT_MAIN_PY、CORE_PY、WEB_SERVER_PY、INTENT_ROUTER_PY）
- 移除 REVENUE_SKILL_PY 模板常數
- 移除 requirements.txt 模板中的 pyodbc、pyyaml
- 更新測試指南模板（移除營收/遊戲分析案例）
- 移除 config/db.yaml 後續步驟提示

### v0.3.0（2026-03-18）
- 移除 REVENUE 和 GAME_ANALYSIS 意圖，精簡為 3 種：DASHBOARD > RESEARCH > CASUAL
- 移除 revenue_skill.py 及相關 SQL Server 依賴（pyodbc、pandas、pyyaml）
- 移除 /dashboard、/api/revenue、/game-analysis 端點
- 更新範例 skill.json 為 web_scraper、knowledge_qa、dashboard_generator
- 更新 references 文件同步移除 REVENUE/GAME_ANALYSIS 相關內容

### v0.2.0（2026-03-18）
- 整合 `arkbot-generator` 所有功能（Foundation 基礎層）
- 新增 `scripts/generate_arkbot.py`（Foundation 層產生腳本）
- 合併觸發關鍵字（ArkBot、智庫助理、網頁獵取 Bot、爬蟲 Bot、Telegram 智庫、建立 ArkBot）
- 移除「與 arkbot-generator 的關係」章節（已整合為單一技能）
- `arkbot-generator` 退役至 `.agent/skills/` 備份

### v0.1.0（2026-03-18）
- 初始版本建立
- 四層架構：Foundation / Decision Engine / Skill Runtime / Integration
- 兩階段工作流程：Scaffold → Implement
- 繼承 arkbot-generator 的 Foundation 實作要點
- 新增 Decision Engine + Skill Runtime references
