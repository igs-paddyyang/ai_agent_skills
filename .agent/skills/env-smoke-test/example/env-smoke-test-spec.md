# Environment Smoke Test Skill Spec

**作者**: paddyyang
**日期**: 2026-03-18
**版本**: v0.1
**目標**: 作為 skill-creator 的輸入，產出 env-smoke-test 技能

---

## 1. 技能定義

- **名稱**: env-smoke-test
- **一句話描述**: 對 ArkBot 執行環境進行煙霧測試，驗證 Python 版本、套件安裝、Gemini API 可用模型、Telegram Bot Token 有效性
- **觸發描述（description 欄位草稿）**:
  > 對 ArkBot 執行環境進行煙霧測試（Environment Smoke Test），快速驗證 Python 版本與執行環境、requirements.txt 套件安裝狀態、Google Gemini API 連通性與可用模型清單、Telegram Bot Token 有效性與 Bot 資訊。當使用者提到環境測試、env smoke test、檢查環境、驗證 API、測試 Gemini、測試 Telegram、Token 驗證、環境健康檢查、套件檢查時，請務必使用此技能。

## 2. 行為規格

### 2.1 輸入
- **專案路徑**（必要）：ArkBot 專案根目錄（如 `nana_bot/`），用於讀取 `.env` 和 `requirements.txt`
- **測試項目**（選用）：指定要執行的檢查項目，預設全部
  - `python` — 僅 Python 環境
  - `packages` — Python + 套件
  - `gemini` — Python + 套件 + Gemini API
  - `telegram` — Python + 套件 + Telegram API
  - `all` — 全部（預設）

### 2.2 處理邏輯
