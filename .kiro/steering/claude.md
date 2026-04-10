---
inclusion: always
version: "1.4.0"
last_synced: "2026-04-10"
---

# AI 協作規範

本專案的開發規範與行為準則，供 Kiro 環境自動注入。

---

## 專案性質

本專案是 Agent Skills Factory — 建立 AI Agent 架構與 Agent Skills 的開發專案。工作區包含：
- `.kiro/skills/` — 研發系統（使用 Kiro IDE 開發技能，核心產出物，21 個技能）
- `.agent/skills/` — 正式環境（無 Kiro IDE 時的技能部署位置 / 備份，由 skill-sync 同步）
- `kiro_agent/` — kiro-agent 多 Agent 艦隊管理系統（獨立子專案，含原始碼 + 測試 + 文件）
- `llm-mcp-server/` — LLM MCP Server（多 Provider 切換的 MCP 伺服器）
- `docs/` — 設計文件與規格
- `output/` — 產出物暫存

Agent 範例專案由 `arkbot-agent-generator` 產出至工作區外部目錄，不納入本 repo 版控。

---

## Kiro Skill 開發規範

### 技能結構
每個技能必須包含：
- `SKILL.md` — 主要技能指令（YAML 前置資料 + Markdown 指令，理想 <500 行）
- `README.md` — 技能說明文件（版本資訊表格 + 功能說明 + 使用方式 + 檔案結構 + 變更紀錄）
- `references/` — 按需載入的詳細指南（選用）
- `scripts/` — 可執行腳本（選用）
- `assets/` — 範本、圖片等（選用）

### SKILL.md 撰寫規範
- YAML 前置資料必須包含 `name`（kebab-case，≤64 字元）和 `description`（≤1024 字元）
- description 要「積極」觸發：同時包含功能描述和使用情境關鍵字
- 祈使句寫作風格，解釋為什麼重要而非堆砌 MUST
- 漸進式揭露：中繼資料 → SKILL.md 本體 → 附帶資源

### README.md 撰寫規範
- 使用 `skill-creator/templates/readme.md` 範本格式
- 必須包含：版本資訊表格、功能說明、使用方式、檔案結構、變更紀錄
- 版本採用 Semantic Versioning（MAJOR.MINOR.PATCH）
- 新建技能從 `0.1.0` 開始，經 eval 驗證穩定後升級為 `1.0.0`

---

## ArkBot / ArkAgent OS 開發規範（產出的 Agent）

### 架構模式
- ArkBot：entry/ → src/ → controller/ + memory/ + planner/（PYTHONPATH=src）
- ArkAgent OS：entry/ → compat/ → controller/ + memory/ + planner/（PYTHONPATH=compat），額外有 kernel/ intent/ runtime/ tools/ gateway/ specs/
- 意圖分類 → Skill Registry → Executor（v2 Runtime Dispatcher）路由
- Skills 為純函式或薄封裝，不持有狀態

### 代碼風格
- Python 3.12+（generator 產出的 Agent 最低相容 3.9+），遵循 PEP 8
- 函數優先（非 class-based），保持簡潔
- 每個檔案單一職責
- 變數與函式使用 `snake_case`

### 安全規範
- 嚴禁 Hard-code 密碼或 API Key
- SQL 查詢應使用參數化查詢
- 日誌禁止記錄用戶 PII

### Generator 同步規範
- 在 Agent 專案中驗證的改進，必須同步回寫至 generator 模板（templates/*.py）
- 回寫後更新 generator README.md 版本號與變更紀錄

---

## 版本控管規則（Semantic Versioning）

### Steering 文件版本
適用：`.kiro/steering/*.md` 的 YAML front-matter `version` 欄位。

| 版本位 | 何時遞增 | 範例 |
|--------|---------|------|
| MAJOR | 文件定位或結構大幅重組 | 合併/拆分文件、章節架構重寫 |
| MINOR | 新增章節、新增規則 | 新增「版本控管規則」章節 |
| PATCH | 修正錯字、更新數據 | 修正技能數量、更新日期 |

### Skill 文件版本
適用：每個技能的 `README.md` 版本資訊表格。

| 版本位 | 何時遞增 | 範例 |
|--------|---------|------|
| MAJOR | 觸發條件大改、輸出格式變更 | SKILL.md 指令重寫、介面變更 |
| MINOR | 新增功能、擴充場景 | 新增模板、支援新參數 |
| PATCH | 修正錯誤、微調模板 | 修正 bug、改善提示詞 |

規則：MAJOR 遞增時 MINOR+PATCH 歸零，MINOR 遞增時 PATCH 歸零。

---

## 文件更新決策表

| 改了什麼 | 更新哪些文件 |
|---------|-------------|
| 新增/修改 Kiro Skill | 技能 README.md（版本+變更紀錄）+ structure.md + memory.md |
| 新增/修改 Agent 功能 | structure.md + memory.md |
| 新增套件或指令 | tech.md + requirements.txt |
| 架構決策或重大變更 | memory.md（決策紀錄） |
| 開發規範或代碼風格 | claude.md（遞增 version） |
| 產品定位或功能描述 | product.md（遞增 version） |
| 新增設計文件 | docs/ + memory.md |
| Agent 改進回寫 generator | generator README.md + templates/ |
| 修改 steering 文件 | 遞增該檔 YAML front-matter 的 `version` 欄位 |

---

## Memory 修剪指南

`memory.md` 超過 80 行時：
- 已完成的里程碑濃縮為一行摘要
- 超過 1 個月的決策紀錄只保留結論
- 上次對話摘要只保留最近 3 次
- 已解決的問題立即刪除

---

## 對話結束前

1. 總結本次對話（1-3 句話）
2. 更新 `memory.md` 的「上次對話摘要」
3. 若新增/刪除技能，檢查 `structure.md` 和 `product.md` 是否需同步

---

## 避坑指南

> 每次踩坑後，評估屬於「通用規則」或「特定技術細節」，分別記錄到 claude.md（本節）或 memory.md（環境備註）。

### Windows / PowerShell 環境
- `py` 啟動器執行 Python（非 `python`），避免路徑衝突
- PowerShell 會把 Python stderr 當 NativeCommandError 拋出 → `logging.basicConfig()` 加 `stream=sys.stdout`
- `subprocess` 輸出預設 cp950 編碼 → 加 `encoding="utf-8"` + `sys.stdout.reconfigure(encoding='utf-8')`
- 模板字串和 `start.bat` 禁用 emoji → cp950 無法編碼，改用 `[OK]` `[ERROR]` 等文字標記
- `chcp 65001` 放在 bat 檔開頭確保 UTF-8 輸出

### MCP Server 整合
- 每個 MCP Server 的 tool 名稱和參數命名風格不同，必須實測確認（不能靠文件猜）
- MCP config 中的憑證用 `${ENV_VAR}` 引用，禁止硬編碼
- MCPController 的 `TOOL_ALIASES` 和 `PARAM_ALIASES` 是解決命名差異的正確方式
- 特定 MCP Server 版本細節記錄在 `memory.md` 環境備註

### Generator 模板
- 模板中的字串用 `\\'{name}\\'` 跳脫單引號（因為模板本身在 Python 三引號字串內）
- `__COMPAT_DIR__` 佔位符在 registry.py 的 `_replace_compat()` 替換，arkbot→`src`，arkagent→`compat`
- 新增 Skill 模板後，必須同步更新：`__init__.py` 匯出、`registry.py` gen_* 函式、`manifest.py` modules 清單、README.md 變更紀錄
- Dry-run 驗證（`--dry-run`）是確認產出檔案數的最快方式

### Skill 開發
- `skill.yaml` 的 `runtime` 欄位決定 Executor 路由（python / mcp / ai / composite），漏填預設為 python
- 二層子目錄的 Skill（如 `skills/workflows/daily-report/`）需要 SkillRegistry 支援二層掃描
- MCP runtime 的 Skill 不需要 `skill.py`，只需 `skill.yaml`（由 MCPAdapter 直接呼叫 MCP tool）

---

## 禁止事項

| 禁止 | 原因 |
|---|---|
| 修改技能時不更新 README.md 版本號 | 版本追蹤是技能管理的基礎 |
| SKILL.md 超過 500 行 | 超過時應拆分到 references/ |
| description 超過 1024 字元 | Kiro 平台限制 |
| 技能內包含惡意程式碼 | 無意外原則 |
| Agent 改進不回寫 generator | 下次產出會重複相同問題 |

---

## 語言規範

- 文件與註解優先使用繁體中文
- 代碼內的變數名、日誌可使用英文

---

## Gemini 模型規範

- 預設模型：`models/gemini-2.5-flash-lite`
- 使用 `google-genai` 套件（非 `google.generativeai`）
- API Key 一律從 `.env` 的 `GOOGLE_API_KEY` 讀取
- 切換模型時須全專案搜尋替換（Python 程式碼 + 文件 + steering）
