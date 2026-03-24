# 環境煙霧測試 — 檢查項目清單

## 階段 1：Python 環境

| # | 檢查項目 | 通過條件 |
|---|---------|---------|
| 1.1 | Python 版本 | `sys.version_info >= (3, 9)` |
| 1.2 | Python 執行路徑 | `sys.executable` 可取得 |
| 1.3 | 平台資訊 | `platform.platform()` 可取得 |

## 階段 2：套件安裝

讀取專案的 `requirements.txt`，逐一檢查套件是否可匯入。

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

注意：套件名稱與匯入名稱不一定相同（如 `beautifulsoup4` → `bs4`）。

## 階段 3：Gemini API

前置條件：`.env` 中 `GOOGLE_API_KEY` 已設定且非空。

| # | 檢查項目 | 方法 | 通過條件 |
|---|---------|------|---------|
| 3.1 | API Key 存在 | 讀取 `.env` | `GOOGLE_API_KEY` 非空 |
| 3.2 | Client 初始化 | `genai.Client(api_key=...)` | 無例外 |
| 3.3 | 可用模型清單 | `client.models.list()` | 回傳至少 1 個模型 |
| 3.4 | 列出模型名稱 | 過濾 `gemini` 開頭的模型 | 顯示可用模型清單 |

## 階段 4：Telegram Bot Token

前置條件：`.env` 中 `TELEGRAM_TOKEN` 已設定且非空。

| # | 檢查項目 | 方法 | 通過條件 |
|---|---------|------|---------|
| 4.1 | Token 存在 | 讀取 `.env` | `TELEGRAM_TOKEN` 非空 |
| 4.2 | Token 有效性 | `GET https://api.telegram.org/bot{token}/getMe` | HTTP 200 + `ok: true` |
| 4.3 | Bot 資訊 | 解析 getMe 回應 | 顯示 bot username、first_name、id |
