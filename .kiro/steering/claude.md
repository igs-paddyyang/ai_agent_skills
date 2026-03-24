---
inclusion: always
version: "1.0.0"
last_synced: "2026-03-24"
---

# AI 協作規範

本專案的開發規範與行為準則，供 Kiro 環境自動注入。

---

## 專案性質

本專案是 Agent Skills Factory — 建立 AI Agent 架構與 Agent Skills 的開發專案。工作區包含：
- `.kiro/skills/` — 研發系統（使用 Kiro IDE 開發技能，核心產出物）
- `.agent/skills/` — 正式環境（無 Kiro IDE 時的技能部署位置 / 備份）
- `nana_bot/` — ArkBot 範例專案（由 arkbot-generator 產出）
- `docs/` — 設計文件與規格

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

## ArkBot 開發規範（產出的 Agent）

### 架構模式
- 三層架構：`arkbot_core.py` 為核心，`bot_main.py`（Telegram）和 `web_server.py`（Web）為入口
- 意圖分類 → Skill Registry → Executor 路由
- Skills 為純函式或薄封裝，不持有狀態

### 代碼風格
- Python 3.9+，遵循 PEP 8
- 函數優先（非 class-based），保持簡潔
- 每個檔案單一職責
- 變數與函式使用 `snake_case`

### 安全規範
- 嚴禁 Hard-code 密碼或 API Key
- SQL 查詢應使用參數化查詢
- 日誌禁止記錄用戶 PII

---

## 禁止事項

| 禁止 | 原因 |
|---|---|
| 修改技能時不更新 README.md 版本號 | 版本追蹤是技能管理的基礎 |
| SKILL.md 超過 500 行 | 超過時應拆分到 references/ |
| description 超過 1024 字元 | Kiro 平台限制 |
| 技能內包含惡意程式碼 | 無意外原則 |

---

## 語言規範

- 文件與註解優先使用繁體中文
- 代碼內的變數名、日誌可使用英文
