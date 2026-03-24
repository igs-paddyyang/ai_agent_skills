# ArkAgent OS 架構與模組說明

本文件是 `generate_arkagent.py` 的對應參考資源，說明 ArkAgent OS 五模組架構的設計理念、模組職責與實作要點。

---

## 1. 架構總覽

ArkAgent OS 是從 ArkBot 四層架構升級而來的多 Agent 平台。核心差異在於：將硬編碼配置改為 Spec DSL 驅動、新增 Memory System 和 Tool Gateway、支援多 Agent 實例。

```
┌─────────────────────────────────────────────────────────┐
│                    ArkAgent OS                          │
├─────────────────────────────────────────────────────────┤
│  Agent Kernel    │ Intent Engine  │ Skill Runtime       │
│  lifecycle       │ classifier     │ registry (YAML)     │
│  config (.env    │ router         │ resolver (3-stage)  │
│   + yaml)        │ spec-driven    │ executor (sandbox)  │
│  spec_loader     │                │ scheduler (cron)    │
│  logger          │                │                     │
├──────────────────┴────────────────┴─────────────────────┤
│  Memory System              │ Tool Gateway              │
│  short_term (deque)         │ gateway (register/call)   │
│  long_term (SQLite)         │ gemini / telegram / web   │
├─────────────────────────────┴───────────────────────────┤
│  specs/           │ agents/          │ skills/           │
│  schema/*.json    │ default/         │ crawler/          │
│  runtime.yaml     │   agent.yaml     │ chat/             │
│  examples/        │                  │ dashboard/        │
└─────────────────────────────────────────────────────────┘
```

### 與 ArkBot 的映射關係

```
ArkBot 四層架構              →    ArkAgent OS 五模組
─────────────────────────────────────────────────────
Foundation Layer             →    Agent Kernel + Entry
  └─ intent_router.py        →    Intent Engine
Decision Engine              →    Intent Engine（進階版）
Skill Runtime                →    Skill Runtime（YAML 驅動）
Integration                  →    （拆散到各模組）
（無）                        →    Memory System（新增）
（無）                        →    Tool Gateway（新增）
```

---

## 2. Spec DSL 系統

Spec DSL 是 ArkAgent OS 的地基。所有配置從硬編碼轉為 YAML 定義 + JSON Schema 驗證。

### 2.1 三種 Spec 類型

| 類型 | 檔案 | 用途 |
|------|------|------|
| skill | `skills/*/skill.yaml` | 定義 Skill 的意圖、輸入輸出、執行模式 |
| agent | `agents/*/agent.yaml` | 定義 Agent 的 Skill 集合、記憶配置、入口 |
| runtime | `specs/runtime.yaml` | 全域 Runtime 設定（並行、超時、排程、安全） |

### 2.2 skill.yaml 必填欄位

```yaml
type: skill          # 固定值
name: web-scraper    # kebab-case
execution:
  mode: subprocess   # async | subprocess
  entry: skill.py    # 入口檔案
```

選填欄位：version / description / intent / examples / input / output / tags / priority / enabled / response_type

### 2.3 向後相容

`spec_loader.py` 的 `load_all_skills()` 會依序嘗試：
1. `skill.yaml`
2. `skill.yml`
3. `skill.json`（向後相容 ArkBot 格式）

### 2.4 Schema 驗證

- `specs/schema/skill.schema.json` — Skill Spec Schema
- `specs/schema/agent.schema.json` — Agent Spec Schema
- `specs/schema/runtime.schema.json` — Runtime Spec Schema
- `scripts/validate_specs.py` — 驗證腳本，掃描 specs/ + agents/ + skills/ 下所有 YAML

---

## 3. Agent Kernel

Agent Kernel 是 ArkAgent OS 的核心，負責 Agent 生命週期管理。

### 3.1 AgentBase 類別

```python
class AgentBase:
    async def start()           # 啟動 Agent，呼叫 on_start
    async def stop()            # 停止 Agent，呼叫 on_stop
    async def handle_message()  # 統一訊息入口，呼叫 on_message

    # Lifecycle Hooks（子類別覆寫）
    async def on_start()        # 初始化資源
    async def on_message()      # 處理訊息
    async def on_stop()         # 釋放資源
```

### 3.2 config.py

統一載入配置，優先順序：
1. `.env` 環境變數（API Key、Token 等敏感資訊）
2. `specs/runtime.yaml`（Runtime 設定）
3. 預設值

### 3.3 spec_loader.py

核心函式：
- `load_spec(path)` — 自動偵測 YAML/JSON 並載入
- `validate_schema(data, schema_dir)` — JSON Schema 驗證
- `load_and_validate(path, schema_dir)` — 載入 + 驗證一步完成
- `load_all_skills(skills_dir, schema_dir)` — 掃描 skills/ 載入所有 Skill

### 3.4 logger.py

結構化日誌，格式：`%(asctime)s [%(name)s] %(levelname)s: %(message)s`

---

## 4. Intent Engine

Intent Engine 負責意圖分類與路由，沿用 ArkBot 的雙層決策架構。

### 4.1 模組對應

| ArkAgent OS | ArkBot 原始 | 職責 |
|-------------|-------------|------|
| `intent/classifier.py` | `intent_router.py` | 意圖分類（Gemini API） |
| `intent/router.py` | `hybrid_router.py` | Intent + Resolver 整合 |

### 4.2 Spec 驅動

未來可從 `agent.yaml` 的 `intents` 欄位動態載入意圖列表，取代硬編碼的 DASHBOARD / RESEARCH / CASUAL。目前版本仍使用固定 3 種意圖。

---

## 5. Skill Runtime

沿用 ArkBot 的 Skill Runtime，但 Skill 定義從 `skill.json` 改為 `skill.yaml`。

### 5.1 模組對應

| ArkAgent OS | ArkBot 原始 | 職責 |
|-------------|-------------|------|
| `runtime/registry.py` | `skill_registry.py` | Skill 註冊表 |
| `runtime/resolver.py` | `skill_resolver.py` | 三階段決策 |
| `runtime/prompt.py` | `skill_prompt.py` | LLM Prompt 建構 |
| `runtime/executor.py` | `executor.py` | Skill 執行器 |
| `runtime/scheduler.py` | `scheduler.py` | 排程引擎 |

### 5.2 執行模式

- **async**：in-process 動態載入，支援 `run_async()` 或 `run()`
- **subprocess**：隔離執行，捕獲 stdout/stderr，timeout 30 秒

---

## 6. Memory System

全新模組，為 Agent 提供對話記憶能力。

### 6.1 ShortTermMemory

- 使用 `collections.deque` 實作固定長度佇列
- `max_turns` 控制保留的對話輪數（預設 20）
- `get_context_string()` 將歷史格式化為 LLM prompt 可用的字串
- 記憶體內運作，Agent 重啟後清空

### 6.2 LongTermMemory

- 使用 SQLite 持久化儲存
- 支援 CRUD + 關鍵字搜尋
- `agent_name` 欄位支援多 Agent 隔離
- `category` 欄位支援分類（general / conversation / knowledge）
- 預留介面供未來擴展 vector DB

### 6.3 配置

在 `agent.yaml` 中定義：

```yaml
memory:
  short_term:
    max_turns: 20
  long_term:
    backend: sqlite
    path: data/memory.db
```

---

## 7. Tool Gateway

全新模組，統一管理所有外部工具呼叫。

### 7.1 BaseTool 介面

```python
class BaseTool:
    name: str           # 工具名稱
    description: str    # 工具描述
    async def call(**kwargs) -> Any      # 執行工具
    async def health_check() -> bool     # 健康檢查
```

### 7.2 ToolGateway

```python
class ToolGateway:
    register(tool)              # 註冊工具
    unregister(name)            # 取消註冊
    call(name, **kwargs)        # 呼叫工具
    list_tools()                # 列出所有工具
    health_check_all()          # 全部健康檢查
```

### 7.3 內建工具

| 工具 | 名稱 | 用途 |
|------|------|------|
| GeminiTool | `gemini` | Gemini API 文字生成 |
| TelegramTool | `telegram` | Telegram Bot API |
| WebTool | `web` | HTTP GET/POST 請求 |

### 7.4 擴展方式

實作 `BaseTool` 介面，呼叫 `gateway.register(MyTool())` 即可。

---

## 8. 多 Agent 支援

### 8.1 目錄結構

```
agents/
├── default/
│   └── agent.yaml      # 預設 Agent
├── fish/
│   └── agent.yaml      # 魚機分析 Agent
└── aiops/
    └── agent.yaml      # AIOps Agent
```

### 8.2 Agent 選擇

入口層透過 `--agent` 參數選擇 Agent：

```bash
python entry/cli_entry.py --agent fish
python entry/web_entry.py --agent default
```

### 8.3 隔離

- 每個 Agent 有獨立的 Skill 集合（由 agent.yaml 的 `skills` 欄位定義）
- Memory System 透過 `agent_name` 欄位隔離
- Tool Gateway 共享（所有 Agent 使用同一組工具）

---

## 9. Architecture Reviewer

內建架構審查工具，可對產出的專案進行自動品質評分。

### 9.1 五維度評分（0-100）

| 維度 | 分數 | 檢查項目 |
|------|------|---------|
| Layering | 0-20 | 層級一致性，是否有跨層邏輯 |
| Decoupling | 0-20 | 解耦程度，是否有 God Object |
| Scalability | 0-20 | 擴展性，新增 Skill 是否需改多處 |
| Maintainability | 0-20 | 可維護性，是否有統一 Schema |
| Spec Integrity | 0-20 | 規格一致性，Spec 是否有衝突 |

### 9.2 使用方式

```bash
python scripts/review_architecture.py [project_dir]
```

輸出 JSON 格式的評分報告。需要 Gemini API Key。

---

## 10. 產出結構總覽

`generate_arkagent.py` 產出 ~80 個檔案：

```
{project-name}/
├── .env.example                        # 環境變數範本
├── requirements.txt                    # 含 pyyaml + jsonschema
├── start.bat                           # 一鍵啟動（含 Spec 驗證）
├── specs/                              # Spec DSL
│   ├── schema/                         # JSON Schema（3 個）
│   ├── runtime.yaml                    # 全域 Runtime 設定
│   └── examples/                       # 範例 YAML（2 個）
├── kernel/                             # Agent Kernel（5 個）
├── intent/                             # Intent Engine（3 個）
├── runtime/                            # Skill Runtime（6 個）
├── memory/                             # Memory System（3 個）
├── tools/                              # Tool Gateway（5 個）
├── controller/                         # Domain Controller（5 個）
├── planner/                            # Skill Planner（3 個）
├── gateway/                            # API Gateway（5 個）
├── config/                             # 設定（mcp.json）
├── agents/default/agent.yaml           # 預設 Agent 配置
├── entry/                              # 入口層（3 個：telegram / web / cli）
├── src/                                # 相容層（沿用 ArkBot 模組）
├── skills/                             # Skill Package（3 個，YAML 版）
├── web/index.html                      # Web 對話頁
├── data/                               # 資料目錄
├── scripts/                            # 腳本（init_db + validate_specs + review_architecture）
├── docs/bot_test_guide.md              # 測試指南
└── tests/                              # 測試（14 個 test_*.py）
```

---

## 11. 已知限制與未來擴展

| 項目 | 現狀 | 未來 |
|------|------|------|
| 意圖分類 | Spec 驅動動態意圖（從 agent.yaml 讀取） | meta-router 自動選擇 Agent |
| Memory 後端 | SQLite | 擴展 vector DB（FAISS / ChromaDB） |
| 多 Agent 路由 | 入口層 `--agent` 參數 | 自動 Agent 選擇（meta-router） |
| Tool Gateway | 3 個內建工具 | Plugin 市集（自動發現 + 安裝） |
| Architecture Reviewer | 依賴 Gemini API | 離線靜態規則 fallback |
| Spec DSL | YAML + JSON Schema | 支援 Spec 繼承 + 組合 |
| Domain Controller | MCP 骨架模式 | 完整 JSON-RPC stdio 通訊 |
| Skill Planner | LLM 拆解 + sequential | 並行執行 + 動態重規劃 |

---

## 12. Domain Controller（三種執行模式）

Domain Controller 是 Skill 與外部世界之間的抽象層。Skill 回傳 Action 指令，由 Controller 路由到對應的執行模式。

### 12.1 架構

```
Skill Executor
    ↓ Action dict
┌─────────────────────────────────────────────────────────┐
│  Domain Controller（路由層）                              │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │MCP Controller│  │Python Ctrl   │  │System Ctrl   │  │
│  │• MCP Server  │  │• run_function│  │• scheduler   │  │
│  │• call_tool   │  │• run_script  │  │• skill mgmt  │  │
│  │• list_tools  │  │• 白名單+沙箱 │  │• admin API   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 12.2 Action 統一格式

```python
{
    "type": "action",
    "controller": "mcp|python|system",
    "action": "call_tool|run_script|scheduler.add|...",
    "params": { ... },
    "fallback_text": "操作完成的文字描述"
}
```

Skill 回傳純文字時走原有邏輯（完全向後相容）。Executor 偵測到 Action 格式後自動交給 DomainController。

### 12.3 三個子 Controller

**SystemController** — 操作 ArkBot 內建系統：
- `scheduler.*`：排程 CRUD（list / add / remove / toggle / trigger）
- `skill.*`：Skill 管理（list / enable / disable / reload / info）
- `admin.*`：系統管理（status / config / logs）

**PythonController** — 安全執行 Python 腳本/函式：
- `run_script`：subprocess 執行，白名單限制（scripts/ + skills/）
- `run_function`：動態載入模組並呼叫函式
- 安全機制：路徑正規化防目錄穿越、timeout 強制終止

**MCPController** — MCP Protocol 連接（骨架）：
- `connect` / `disconnect`：管理 MCP Server 連線
- `call_tool`：呼叫 MCP tool（JSON-RPC）
- `list_tools`：列出可用 tools
- 設定：`config/mcp.json`

### 12.4 產出目錄

```
controller/
├── __init__.py
├── domain_controller.py    # 統一路由器
├── system_controller.py    # 內建系統操作
├── python_controller.py    # Python 腳本執行
└── mcp_controller.py       # MCP Protocol（骨架）

config/
└── mcp.json                # MCP Server 設定
```

---

## 13. Skill Planner（多步驟規劃）

Skill Planner 是 LLM 驅動的需求拆解器，將複雜請求分解為多個 Skill 的執行計畫。

### 13.1 工作流程

```
使用者輸入
    ↓
SkillPlanner.analyze()
    ├── 簡單請求（「你好」）→ ExecutionPlan.simple("chat")
    └── 複雜請求（「產生儀表板並排程」）→ ExecutionPlan（多步驟）
    ↓
Executor.execute_plan(plan)
    ├── step 1: dashboard Skill → 產出儀表板
    └── step 2: system controller → scheduler.add
    ↓
彙整結果回傳
```

### 13.2 ExecutionPlan 結構

```python
@dataclass
class PlanStep:
    step: int           # 步驟編號
    skill_id: str       # Skill ID（Skill 執行）
    input: str          # 使用者輸入
    controller: str     # Controller 名稱（Controller 操作）
    action: str         # Controller 動作
    params: dict        # 動作參數
    depends_on: list    # 前置步驟（DAG 依賴）

@dataclass
class ExecutionPlan:
    steps: list[PlanStep]
    strategy: str       # sequential | parallel | mixed
    is_simple: bool     # True = 不需拆解
```

### 13.3 LLM Prompt 設計

Planner 的 prompt 包含：
- 可用 Skill 清單（從 registry 動態生成）
- 可用 System Controller 操作清單
- 3 個 few-shot 範例（簡單 / 單一 Skill / 多步驟）
- 對話 context（最近 N 輪）

### 13.4 產出目錄

```
planner/
├── __init__.py
├── planner.py          # SkillPlanner（LLM 驅動）
└── execution_plan.py   # ExecutionPlan（DAG 結構）
```

---

## 14. API Gateway（獨立化）

API Gateway 從 web_server.py 抽出，形成獨立的認證 + 限流 + 路由層。

### 14.1 中介層

- **AuthMiddleware**：API Key / Bearer Token 驗證，公開路徑（/ /health /ws/chat）免認證
- **RateLimiterMiddleware**：Sliding Window 限流，預設每分鐘 60 次，僅對 /api/ 路徑生效

### 14.2 端點

| 路徑 | 方法 | 認證 | 說明 |
|------|------|------|------|
| `/` | GET | 否 | Web 對話頁 |
| `/health` | GET | 否 | 健康檢查 |
| `/dashboard` | GET | 否 | 儀表板 HTML |
| `/ws/chat` | WS | 否 | WebSocket 對話 |
| `/api/skills` | GET | 是 | 列出所有 Skill |
| `/api/skill/{id}` | POST | 是 | 執行指定 Skill |

### 14.3 產出目錄

```
gateway/
├── __init__.py
├── app.py                  # FastAPI 主應用（create_app）
├── auth.py                 # 認證中介層
├── rate_limiter.py         # 限流中介層
└── websocket_handler.py    # WebSocket 對話處理器
```
