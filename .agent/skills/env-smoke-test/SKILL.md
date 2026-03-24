---
name: env-smoke-test
description: "對 ArkBot 執行環境進行煙霧測試（Environment Smoke Test），快速驗證 Python 版本與執行環境、requirements.txt 套件安裝狀態、Google Gemini API 連通性與可用模型清單、Telegram Bot Token 有效性與 Bot 資訊。當使用者提到環境測試、env smoke test、檢查環境、驗證 API、測試 Gemini、測試 Telegram、Token 驗證、環境健康檢查、套件檢查時，請務必使用此技能。"
---

# Environment Smoke Test

對 ArkBot 專案的執行環境進行煙霧測試，確認「環境能跑」。

## 使用時機

- 首次部署 ArkBot 專案後，驗證環境是否就緒
- 更換 API Key 或 Token 後，確認連通性
- 安裝套件後，確認所有依賴都已就位
- 搭配 `smoke-test-runner`（驗專案結構）使用，形成完整驗收流程

## 工作流程

### 步驟 1：確認專案路徑

使用者必須提供 ArkBot 專案根目錄路徑（如 `nana_bot/`）。該目錄應包含 `.env`（或 `.env.example`）和 `requirements.txt`。

若使用者未指定路徑，詢問：「請提供 ArkBot 專案的根目錄路徑（如 `nana_bot/`）」

### 步驟 2：確認測試範圍

使用者可選擇測試項目（預設 `all`）：

| 選項 | 涵蓋範圍 |
|------|---------|
| `python` | 僅 Python 環境 |
| `packages` | Python + 套件安裝 |
| `gemini` | Python + 套件 + Gemini API |
| `telegram` | Python + 套件 + Telegram API |
| `all` | 全部（預設） |

### 步驟 3：執行測試腳本

執行 `scripts/env_smoke_test.py`：

```bash
py scripts/env_smoke_test.py --path <專案路徑> --scope <測試範圍>
```

腳本位於此技能的 `scripts/` 目錄下。執行時使用 `py`（Python Launcher）。

### 步驟 4：回報結果

將腳本輸出直接呈現給使用者。若有失敗項目，提供修復建議：

- Python 版本不足 → 建議升級 Python
- 套件缺失 → 提供 `pip install` 指令
- Gemini API 失敗 → 檢查 GOOGLE_API_KEY 是否正確設定
- Telegram Token 失敗 → 檢查 TELEGRAM_TOKEN 是否正確設定
- `.env` 不存在 → 建議從 `.env.example` 複製

## 測試項目詳情

詳細的檢查項目清單請參考 `references/check-items.md`。

## 注意事項

- 此技能會實際呼叫外部 API（Gemini、Telegram），需要有效的網路連線
- API Key 和 Token 從專案的 `.env` 讀取，絕不 hard-code
- 若環境有代理需求，確認 `.env` 中的 `HTTPS_PROXY` 已設定
- 此技能驗證「環境能跑」，不驗證「專案結構完整」（那是 smoke-test-runner 的職責）
