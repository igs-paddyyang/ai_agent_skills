# 環境安裝指南 — 詳細檢查項目與排查

## 目錄

1. [階段 1：Python 環境](#階段-1python-環境)
2. [階段 2：套件安裝](#階段-2套件安裝)
3. [階段 3：.env 環境變數](#階段-3env-環境變數)
4. [階段 4：Gemini API](#階段-4gemini-api)
5. [階段 5：Telegram Bot Token](#階段-5telegram-bot-token)
6. [常見問題排查](#常見問題排查)

---

## 階段 1：Python 環境

### 檢查項目

| # | 檢查項目 | 通過條件 |
|---|---------|---------|
| 1.1 | Python 版本 | `sys.version_info >= (3, 9)` |
| 1.2 | Python 執行路徑 | `sys.executable` 可取得 |
| 1.3 | 平台資訊 | `platform.platform()` 可取得 |

### 安裝指引（若版本不足或未安裝）

- Windows：`winget install Python.Python.3.12` 或從 https://www.python.org/downloads/ 下載
- 安裝時勾選「Add Python to PATH」
- 安裝後重新開啟終端，執行 `py --version` 確認

---

## 階段 2：套件安裝

### 套件名稱 → 匯入名稱對照表

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

### 自動安裝流程

1. 讀取 `requirements.txt`，解析套件名稱（移除版本限制與 extras）
2. 逐一嘗試匯入，記錄缺失套件
3. 若有缺失 → 執行 `py -m pip install -r requirements.txt`
4. 安裝後重新驗證每個套件
5. 回報最終狀態（已安裝數 / 總數）

### 手動安裝指令

```bash
py -m pip install -r requirements.txt
```

若特定套件安裝失敗：

```bash
py -m pip install <套件名稱> --upgrade
```

---

## 階段 3：.env 環境變數

### 必要欄位

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| GOOGLE_API_KEY | Gemini API 金鑰 | 無（必填） |
| TELEGRAM_TOKEN | Telegram Bot Token | 無（必填） |
| DATABASE_PATH | SQLite 資料庫路徑 | `data/brain.db` |
| WEB_PORT | Web 介面埠號 | `2141` |

### 選用欄位

| 欄位 | 說明 |
|------|------|
| HTTPS_PROXY | 代理伺服器（如 `http://127.0.0.1:7890`） |

### 自動處理邏輯

- `.env` 不存在但 `.env.example` 存在 → 複製為 `.env`
- `.env` 已存在 → 僅檢查欄位，不覆蓋
- 欄位值為 `your-*` 開頭 → 視為未設定

---

## 階段 4：Gemini API

### 檢查項目

| # | 檢查項目 | 方法 | 通過條件 |
|---|---------|------|---------|
| 4.1 | API Key 存在 | 讀取 `.env` | `GOOGLE_API_KEY` 非空且非預設值 |
| 4.2 | Client 初始化 | `genai.Client(api_key=...)` | 無例外 |
| 4.3 | 可用模型清單 | `client.models.list()` | 回傳至少 1 個模型 |
| 4.4 | 列出模型名稱 | 過濾 `gemini` 開頭的模型 | 顯示可用模型清單 |

### 排查

- `401 Unauthorized` → API Key 無效，重新取得：https://aistudio.google.com/apikey
- `403 Forbidden` → API Key 無權限，檢查是否啟用 Generative Language API
- 連線逾時 → 檢查網路或設定 HTTPS_PROXY

---

## 階段 5：Telegram Bot Token

### 檢查項目

| # | 檢查項目 | 方法 | 通過條件 |
|---|---------|------|---------|
| 5.1 | Token 存在 | 讀取 `.env` | `TELEGRAM_TOKEN` 非空且非預設值 |
| 5.2 | Token 有效性 | `GET /bot{token}/getMe` | HTTP 200 + `ok: true` |
| 5.3 | Bot 資訊 | 解析 getMe 回應 | 顯示 username、first_name、id |

### 排查

- `401 Unauthorized` → Token 無效，從 @BotFather 重新取得
- 連線逾時 → Telegram API 可能被封鎖，設定 HTTPS_PROXY
- `409 Conflict` → 有其他程式正在使用同一個 Token（如已啟動的 bot_main.py）

---

## 常見問題排查

### pip 不是內部或外部命令

```bash
py -m ensurepip --upgrade
py -m pip install --upgrade pip
```

### SSL 憑證錯誤

```bash
py -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### 虛擬環境

建議在虛擬環境中安裝：

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 代理設定

若在公司網路或受限環境中：

1. 在 `.env` 中設定 `HTTPS_PROXY=http://127.0.0.1:7890`
2. pip 也需要代理：`py -m pip install -r requirements.txt --proxy http://127.0.0.1:7890`
