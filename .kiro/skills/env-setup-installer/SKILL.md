---
name: env-setup-installer
description: "確認並安裝 ArkBot 與 Kiro Skills 專案所需的完整執行環境。涵蓋 Python 版本檢查與安裝指引、requirements.txt 套件自動安裝、.env 環境變數設定引導、Google Gemini API 連通性驗證與可用模型清單、Telegram Bot Token 有效性驗證與 Bot 資訊。當使用者提到環境安裝、安裝環境、setup environment、安裝套件、install packages、設定環境、環境建置、初始化環境、env setup、環境設定、部署準備時，請務必使用此技能。"
---

# 環境與服務安裝（Environment Setup Installer）

一站式完成 ArkBot 專案的環境建置與服務驗證。與 `env-smoke-test`（唯讀檢查）互補——本技能是「先裝再驗」，能自動安裝缺失套件並引導設定。

## 使用時機

- 首次部署 ArkBot 專案，需要從零建置環境
- 新機器或新虛擬環境，需要安裝所有依賴
- 更換 API Key 或 Token 後，需要驗證連通性
- 搭配 `env-smoke-test`（驗環境健康）形成完整的環境管理流程

## 工作流程

### 步驟 1：確認專案路徑

使用者提供 ArkBot 專案根目錄路徑（如 `nana_bot/`）。該目錄應包含 `requirements.txt`。

若使用者未指定路徑，詢問：「請提供 ArkBot 專案的根目錄路徑（如 `nana_bot/`）」

### 步驟 2：確認安裝範圍

使用者可選擇安裝範圍（預設 `full`）：

| 選項 | 涵蓋範圍 |
|------|---------|
| `python` | 僅 Python 環境檢查 |
| `packages` | Python + 套件自動安裝 |
| `env` | Python + 套件 + .env 設定引導 |
| `gemini` | Python + 套件 + .env + Gemini API 驗證 |
| `telegram` | Python + 套件 + .env + Telegram Token 驗證 |
| `full` | 全部（預設） |

### 步驟 3：執行安裝腳本

執行 `scripts/env_setup.py`：

```bash
py scripts/env_setup.py --path <專案路徑> --scope <安裝範圍>
```

腳本位於此技能的 `scripts/` 目錄下。執行時使用 `py`（Python Launcher）。

### 步驟 4：回報結果與後續指引

將腳本輸出呈現給使用者。腳本會自動處理可修復的問題（安裝套件、複製 .env），並在報告末尾列出「待辦事項」供使用者手動完成（如填入 API Key）。

若有無法自動修復的問題，提供具體的修復建議：

- Python 版本不足 → 建議 `winget install Python.Python.3.12` 或從 python.org 下載
- pip 安裝失敗 → 提供手動安裝指令
- Gemini API 失敗 → 檢查 GOOGLE_API_KEY 是否正確
- Telegram Token 失敗 → 檢查 TELEGRAM_TOKEN 是否正確
- 網路問題 → 檢查代理設定（HTTPS_PROXY）

## 與 env-smoke-test 的差異

| 面向 | env-setup-installer | env-smoke-test |
|------|-------------------|----------------|
| 定位 | 安裝 + 驗證 | 唯讀檢查 |
| 使用時機 | 首次部署、環境建置 | 日常維護、健康檢查 |
| 自動修復 | ✅ 安裝套件、複製 .env | ❌ 僅回報問題 |
| 輸出 | 報告 + 待辦事項 | 報告 |

## 安全注意事項

- 腳本不記錄、不顯示 API Key 或 Token 的實際值
- 不自動修改使用者 `.env` 中已有的值（僅新增或從範本複製）
- 重複執行不會造成副作用（冪等性）

## 附帶資源

- `references/setup-guide.md` — 各階段詳細檢查項目、套件對照表、常見問題排查指南。執行安裝流程前載入此文件以取得完整的檢查清單與排查步驟。
- `scripts/env_setup.py` — 主要安裝與驗證腳本，涵蓋 5 個階段的完整流程。
