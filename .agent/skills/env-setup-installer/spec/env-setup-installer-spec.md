# env-setup-installer Skill Spec

**作者**: paddyyang
**日期**: 2026-03-19
**版本**: v0.1
**目標**: 作為 skill-creator 的輸入，產出 env-setup-installer 技能

---

## 1. 技能定義

- **名稱**: env-setup-installer
- **一句話描述**: 確認並安裝 ArkBot / Kiro Skills 專案所需的 Python 環境、套件依賴、Gemini API 連通性與 Telegram Bot Token，一站式完成環境建置。
- **觸發描述（description 欄位草稿）**:
  > 確認並安裝 ArkBot 與 Kiro Skills 專案所需的完整執行環境。涵蓋 Python 版本檢查與安裝指引、requirements.txt 套件自動安裝、.env 環境變數設定引導、Google Gemini API 連通性驗證與可用模型清單、Telegram Bot Token 有效性驗證與 Bot 資訊。當使用者提到環境安裝、安裝環境、setup environment、安裝套件、install packages、設定環境、環境建置、初始化環境、env setup、環境設定、部署準備時，請務必使用此技能。

## 2. 行為規格

### 2.1 輸入

- **專案路徑**（必要）：ArkBot 專案根目錄（如 `nana_bot/`），需包含 `requirements.txt`
- **安裝模式**（選用，預設 `full`）：

| 模式 | 涵蓋範圍 |
|------|---------|
| `python` | 僅檢查 Python 環境，提供安裝指引 |
| `packages` | Python + 自動安裝套件 |
| `env` | Python + 套件 + .env 設定引導 |
| `gemini` | Python + 套件 + .env + Gemini API 驗證 |
| `telegram` | Python + 套件 + .env + Telegram Token 驗證 |
| `full` | 全部（預設） |

### 2.2 處理邏輯

整體流程分為 5 個階段，每個階段先「檢查」再「修復/安裝」：

#### 階段 1：Python 環境檢查

1. 偵測 Python 版本（`py --version` 或 `python --version`）
2. 若版本 ≥ 3.9 → ✅ 通過，顯示版本與路徑
3. 若版本不足或未安裝 → ❌ 提供安裝指引：
   - Windows：建議從 python.org 下載，或使用 `winget install Python.Python.3.12`
   - 提醒勾選「Add Python to PATH」
4. 顯示 `sys.executable` 與 `platform.platform()`

#### 階段 2：套件安裝

1. 讀取專案的 `requirements.txt`
2. 逐一檢查套件是否已安裝（使用匯入測試）
3. 已安裝的套件 → ✅ 標記通過
4. 缺失的套件 → 自動執行 `py -m pip install -r requirements.txt` 安裝
5. 安裝後重新驗證，回報最終狀態
6. 若安裝失敗 → 顯示錯誤訊息與手動安裝指令

套件名稱 → 匯入名稱對照表（內建於腳本）：

| 套件名稱 | 匯入名稱 | 用途 |
|----------|---------|------|
| python-telegram-bot | telegram | Telegram Bot 入口 |
| google-genai | google.genai | Gemini API |
| requests | requests | HTTP 呼叫 |
| beautifulsoup4 | bs4 | HTML 解析 |
| markdownify | markdownify | HTML → Markdown |
| python-dotenv | dotenv | .env 載入 |
| fastapi | fastapi | Web API 框架 |
| uvicorn | uvicorn | ASGI 伺服器 |
| websockets | websockets | WebSocket 支援 |

#### 階段 3：.env 環境變數設定

1. 檢查專案根目錄是否存在 `.env`
2. 若不存在但有 `.env.example` → 自動複製為 `.env`，提示使用者填入實際值
3. 若 `.env` 已存在 → 檢查必要欄位：
   - `GOOGLE_API_KEY`：非空且非預設值（`your-*`）
   - `TELEGRAM_TOKEN`：非空且非預設值
   - `DATABASE_PATH`：有值（可為預設 `data/brain.db`）
   - `WEB_PORT`：有值（可為預設 `2141`）
4. 缺失或為預設值的欄位 → 列出需要填入的項目與說明
5. 若有 `HTTPS_PROXY` 需求 → 提醒設定

#### 階段 4：Gemini API 驗證

前置條件：階段 3 確認 `GOOGLE_API_KEY` 已設定。

1. 初始化 `genai.Client(api_key=...)`
2. 呼叫 `client.models.list()` 取得可用模型
3. 過濾並列出 `gemini` 開頭的模型名稱
4. 若連線失敗 → 顯示錯誤原因與排查建議（API Key 無效、網路問題、代理設定）

#### 階段 5：Telegram Bot Token 驗證

前置條件：階段 3 確認 `TELEGRAM_TOKEN` 已設定。

1. 呼叫 `GET https://api.telegram.org/bot{token}/getMe`
2. 若支援代理 → 使用 `.env` 中的 `HTTPS_PROXY`
3. 成功 → 顯示 Bot username、first_name、id
4. 失敗 → 顯示錯誤原因與排查建議（Token 無效、網路問題、代理設定）

### 2.3 輸出格式

腳本輸出為結構化的終端報告，格式如下：

```
🔧 ArkBot 環境安裝與驗證報告
========================================
專案路徑：nana_bot
執行時間：2026-03-19 14:30:00

🐍 Python 環境 ........................ ✅（3/3）
   ℹ️  Python 3.12.0
   ℹ️  C:\Python312\python.exe
   ℹ️  Windows-11-10.0.22631-SP0

📦 套件安裝 .......................... ✅（9/9）
   🔧 已自動安裝 3 個缺失套件
   ℹ️  全部 9 個套件已就緒

📝 環境變數 .......................... ⚠️（3/4）
   ✅ GOOGLE_API_KEY：已設定
   ❌ TELEGRAM_TOKEN：未設定（請編輯 .env 填入）
   ✅ DATABASE_PATH：data/brain.db
   ✅ WEB_PORT：2141

🤖 Gemini API ........................ ✅（3/3）
   ℹ️  找到 15 個 Gemini 模型
   ℹ️  models/gemini-2.5-flash
   ℹ️  models/gemini-2.5-pro
   ...

🤖 Telegram Bot ...................... ⏭️ 跳過（Token 未設定）

========================================
結果：⚠️ 部分完成（4/5 階段通過）

📋 待辦事項：
  1. 編輯 nana_bot/.env，填入 TELEGRAM_TOKEN
  2. 填入後重新執行：py scripts/env_setup.py --path nana_bot --scope telegram
```

### 2.4 邊界案例

- **不該做**：不自動修改使用者的 `.env` 中已有的值（只新增缺失欄位或從 `.env.example` 複製）
- **不該做**：不在報告中顯示 API Key 或 Token 的實際值（僅顯示「已設定」/「未設定」）
- **錯誤處理**：
  - 專案路徑不存在 → 立即報錯退出
  - `requirements.txt` 不存在 → 階段 2 標記失敗，繼續後續階段
  - pip 安裝失敗 → 顯示錯誤，提供手動安裝指令
  - API 連線逾時 → 10 秒 timeout，顯示網路排查建議
  - `.env` 與 `.env.example` 都不存在 → 提示使用者手動建立

## 3. 資源需求

### scripts/

| 腳本 | 用途 |
|------|------|
| `env_setup.py` | 主要安裝與驗證腳本，涵蓋 5 個階段的完整流程 |

### references/

| 文件 | 涵蓋範圍 |
|------|---------|
| `setup-guide.md` | 各階段的詳細檢查項目、套件對照表、常見問題排查指南 |

### SKILL.md 預估
- 預估行數：~120 行（工作流程簡潔，細節放 references/）
- 是否需要拆分到 references/：是（詳細檢查項目與排查指南放 `setup-guide.md`）

## 4. 測試案例

| # | 提示詞 | 預期輸出 | 驗證方式 |
|---|--------|---------|---------|
| 1 | `幫我安裝 nana_bot 的環境` | 執行完整 5 階段流程，自動安裝缺失套件，產出報告 | 報告包含 5 個階段結果，缺失套件被安裝 |
| 2 | `檢查 nana_bot 的 Python 和套件` | 僅執行階段 1-2（scope=packages），不觸碰 API 驗證 | 報告僅包含 Python 環境與套件安裝兩個階段 |
| 3 | `我換了 Gemini API Key，幫我驗證一下` | 執行 scope=gemini，驗證 API 連通性並列出可用模型 | 報告包含 Gemini API 階段結果與模型清單 |
| 4 | `安裝環境，但專案路徑不存在` | 立即報錯「專案路徑不存在」 | 不執行任何階段，直接顯示錯誤訊息 |
| 5 | `幫我設定 nana_bot 環境（.env 不存在）` | 從 .env.example 複製 .env，提示填入 API Key 和 Token | 報告顯示 .env 已從範本建立，列出待填欄位 |

## 5. 備註

- **與 env-smoke-test 的關係**：`env-smoke-test` 是「唯讀檢查」（只驗不修），本技能是「安裝 + 驗證」（先裝再驗）。兩者互補：
  - `env-setup-installer`：首次部署時使用，自動安裝缺失項目
  - `env-smoke-test`：日常維護時使用，快速確認環境健康
- **安全性**：腳本不記錄、不顯示 API Key / Token 的實際值
- **冪等性**：重複執行不會造成副作用（已安裝的套件不會重裝，已存在的 .env 不會覆蓋）
- **離線場景**：階段 1-3 可在無網路環境下執行（若套件已快取），階段 4-5 需要網路
- **未來擴展**：可考慮加入 `--fix` 旗標，自動修復所有可修復的問題（如自動建立 data/ 目錄、初始化資料庫等）
