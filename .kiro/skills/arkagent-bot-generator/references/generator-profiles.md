# Generator Profiles — 三種產出模式規格

> 本文件定義 arkagent-bot-generator 的三種產出模式（lite / standard / agent），作為 manifest.py 實作的參考依據。

---

## 一、模式總覽

| | Lite（簡易版） | Standard（完整版） | Agent（進階版） |
|---|---|---|---|
| 參考專案 | tiger-bot | ninja-bot | datawise-agent |
| 定位 | 快速部署的輕量 Bot | 功能完整的 ArkBot | ArkAgent OS 平台級架構 |
| 頂層目錄 | 8 個 | 14 個 | 20 個 |
| 核心路徑 | src/（PYTHONPATH=src） | src/（PYTHONPATH=src） | compat/（PYTHONPATH=compat） |
| Skills | 4 個 | 11 個 | 11+ 個 |
| 產出檔案 | ~40 檔 | ~75 檔 | ~117 檔 |
| CLI 指令 | `py generate.py lite` | `py generate.py standard` | `py generate.py agent` |

---

## 二、Lite 模式（簡易版）

### 適用場景
- 快速原型驗證
- 特定業務場景的專用 Bot（如營收監控、客服助理）
- 不需要 MCP Controller / Memory / Planner 的輕量部署

### 產出結構
```
{project}/
├── entry/
│   ├── telegram_entry.py
│   ├── web_entry.py
│   └── cli_entry.py
├── src/
│   ├── arkbot_core.py
│   ├── intent_router.py
│   ├── skill_registry.py
│   ├── executor.py（v2 Runtime Dispatcher）
│   ├── scheduler.py（SQLite 持久化）
│   ├── notify_skill.py（發送核心 v2）
│   ├── crawler_skill.py
│   ├── format_utils.py
│   └── runtime/
│       ├── __init__.py
│       ├── base.py
│       ├── python_adapter.py
│       ├── mcp_adapter.py
│       ├── ai_adapter.py
│       └── composite_adapter.py
├── skills/
│   ├── chat/（config/ + scripts/ + SKILL.md + README.md）
│   ├── crawler/（同上）
│   ├── dashboard/（同上）
│   └── notify/（同上 + assets/tg_formatter.py + templates）
├── config/
│   ├── mcp.json（sqlite-server only）
│   └── telegram.json
├── data/
│   ├── brain.db
│   ├── dashboard/sample/（revenue.json + slots.json + fish.json）
│   └── schedules.json
├── web/
│   ├── index.html
│   └── dashboard_hub.html
├── scripts/
│   └── init_db.py
├── docs/
│   └── bot_test_guide.md
├── .env.example
├── requirements.txt
├── main.py
└── start.bat
```

### Skills（4 個）
| Skill | Runtime | Intent | 說明 |
|-------|---------|--------|------|
| chat | python | CASUAL | 閒聊（Gemini） |
| crawler | python | RESEARCH | 網頁爬取 + 結構化摘要 |
| dashboard | python | DASHBOARD | 三層 DSL 儀表板 |
| notify | python | NOTIFY | TG 通報（發送核心 + 樣板） |

### 不包含
- controller/（MCP Controller）— 但 runtime/mcp_adapter.py 保留，可手動加
- memory/（ShortTerm + LongTerm）
- planner/（SkillPlanner）
- agents/（agent.yaml）
- tests/
- dashboard_engine/（DSL 引擎）— dashboard skill 用簡化版
- gemini-canvas skill
- MCP skills（sql-query / bigquery-query / mssql-query）
- AI skills（kpi-analyzer）
- Composite skills（daily-report / anomaly-report）

### Manifest 定義
```python
"lite": {
    "name": "lite",
    "description": "Lite Bot（簡易版，4 Skills）",
    "default_project_name": "my-bot",
    "modules": [
        "src_lite",
        "runtime_adapters",
        "entry",
        "config_mcp_lite",
        "skills_lite",
    ],
    "features": {
        "compat": False,
        "dashboard_engine": False,
        "controller": False,
        "memory": False,
        "planner": False,
    },
    "config": {
        "env_template": "ARKAGENT_ENV_EXAMPLE",
        "requirements_template": "LITE_REQUIREMENTS_TXT",
        "start_bat_template": "ARKAGENT_START_BAT",
    },
}
```

### 新增的 gen_* 函式
- `gen_src_lite` — 精簡版 src/（無 hybrid_router / skill_resolver / skill_prompt / dashboard_skill / gemini_canvas_skill）
- `gen_skills_lite` — 4 個基礎 skill（chat / crawler / dashboard / notify）
- `gen_config_mcp_lite` — 只有 sqlite-server（無 bigquery / mssql）

---

## 三、Standard 模式（完整版）

### 適用場景
- 功能完整的 AI Agent
- 需要 MCP 整合（SQL / BigQuery / MSSQL）
- 需要 Memory + Planner 的智慧路由
- 需要 Composite Workflow

### 產出結構
```
{project}/
├── entry/
├── src/
│   ├── （Lite 的全部）
│   ├── hybrid_router.py
│   ├── skill_resolver.py
│   ├── skill_prompt.py
│   ├── dashboard_skill.py
│   ├── gemini_canvas_skill.py
│   ├── dashboard_engine/（DSL 三層引擎）
│   └── runtime/
├── controller/（Domain + System + Python + MCP）
├── memory/（ShortTerm + LongTerm）
├── planner/（SkillPlanner + ExecutionPlan）
├── agents/default/agent.yaml
├── skills/（11 個）
├── config/
├── data/
├── web/
├── scripts/
├── tests/（4 個基礎測試）
├── docs/
├── .env.example
├── requirements.txt
├── main.py
└── start.bat
```

### Skills（11 個）
| Skill | Runtime | 說明 |
|-------|---------|------|
| chat | python | 閒聊 |
| crawler | python | 網頁爬取 + 結構化摘要 |
| dashboard | python | 三層 DSL 儀表板 |
| gemini-canvas | python | Gemini Canvas 自由排版 |
| notify | python | TG 通報 |
| sql-query | mcp | SQLite 查詢 |
| bigquery-query | mcp | BigQuery 查詢（預設 disabled） |
| mssql-query | mcp | MSSQL 查詢（預設 disabled） |
| kpi-analyzer | ai | KPI 異常分析 |
| daily-report | composite | 每日報告 workflow |
| anomaly-report | composite | 異常偵測 workflow |

### Manifest 定義
即現有的 `arkbot` profile（不變）。

---

## 四、Agent 模式（進階版）

### 適用場景
- 平台級 AI Agent
- 多 Agent 支援
- Spec DSL 驅動
- Architecture Reviewer
- 未來遷移到 OS 原生架構

### 產出結構
```
{project}/
├── entry/
├── compat/（相容層，PYTHONPATH=compat）
├── src/（dashboard_engine/ + runtime/）
├── kernel/（Agent Kernel）
├── intent/（Intent Engine）
├── runtime/（OS 原生 Skill Runtime）
├── memory/
├── tools/（Tool Gateway）
├── controller/
├── planner/
├── gateway/（API Gateway）
├── agents/
├── specs/（Spec DSL + JSON Schema）
├── skills/（11+ 個）
├── config/
├── data/
├── web/
├── scripts/（init_db + validate_specs + review_architecture）
├── tests/（14 個完整測試）
├── docs/
├── .env.example
├── requirements.txt
├── main.py
└── start.bat
```

### Manifest 定義
即現有的 `arkagent` profile（不變）。

---

## 五、模組對照表

| 模組 | gen_* 函式 | Lite | Standard | Agent |
|------|-----------|:----:|:--------:|:-----:|
| src_lite | gen_src_lite | ✅ | — | — |
| src | gen_src | — | ✅ | — |
| dashboard_engine | gen_dashboard_engine | — | ✅ | ✅ |
| runtime_adapters | gen_runtime_adapters | ✅ | ✅ | ✅ |
| entry | gen_entry | ✅ | ✅ | ✅ |
| memory | gen_memory | — | ✅ | ✅ |
| controller | gen_controller | — | ✅ | ✅ |
| planner | gen_planner | — | ✅ | ✅ |
| agents | gen_agents | — | ✅ | ✅ |
| config_mcp_lite | gen_config_mcp_lite | ✅ | — | — |
| config_mcp | gen_config_mcp | — | ✅ | ✅ |
| skills_lite | gen_skills_lite | ✅ | — | — |
| skills_yaml | gen_skills_yaml | — | ✅ | ✅ |
| workflow_skills | gen_workflow_skills | — | ✅ | ✅ |
| tests_basic | gen_tests_basic | — | ✅ | — |
| tests_full | gen_tests_full | — | — | ✅ |
| specs | gen_specs | — | — | ✅ |
| kernel | gen_kernel | — | — | ✅ |
| intent | gen_intent | — | — | ✅ |
| runtime (OS) | gen_runtime | — | — | ✅ |
| tools | gen_tools | — | — | ✅ |
| api_gateway | gen_api_gateway | — | — | ✅ |
| compat | gen_compat | — | — | ✅ |
| scripts_extra | gen_scripts_extra | — | — | ✅ |
| common | gen_common | ✅ | ✅ | ✅ |

---

## 六、實作步驟

### Phase 1：新增 lite profile
1. `manifest.py` 新增 `lite` profile 定義
2. `registry.py` 新增 `gen_src_lite` / `gen_skills_lite` / `gen_config_mcp_lite`
3. `templates/` 新增 `LITE_REQUIREMENTS_TXT`（精簡版，無 jsonschema）
4. MODULE_REGISTRY 新增 3 個條目
5. Dry-run 驗證檔案數 ~40

### Phase 2：重命名現有 profiles
1. `arkbot` → `standard`（保留 `arkbot` 作為 alias）
2. `arkagent` → `agent`（保留 `arkagent` 作為 alias）
3. `generate.py` 的 `--list` 顯示 3 個 profiles

### Phase 3：驗證
1. `py generate.py lite test-lite --dry-run`
2. `py generate.py standard test-std --dry-run`
3. `py generate.py agent test-agent --dry-run`
4. 實際產出 lite 並測試啟動
