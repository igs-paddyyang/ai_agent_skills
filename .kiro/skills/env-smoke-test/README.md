# env-smoke-test

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-18 |
| 最後更新 | 2026-03-18 |

## 功能說明

對 ArkBot 執行環境進行煙霧測試，快速驗證：

1. Python 版本（≥ 3.9）與執行環境
2. requirements.txt 所有套件安裝狀態
3. Google Gemini API 連通性與可用模型清單
4. Telegram Bot Token 有效性與 Bot 資訊

## 使用方式

對話觸發：
- 「檢查 nana_bot 的環境」
- 「env smoke test nana_bot」
- 「測試 Gemini API 是否可用」
- 「驗證 Telegram Token」

腳本直接執行：
```bash
py .kiro/skills/env-smoke-test/scripts/env_smoke_test.py --path nana_bot --scope all
```

### 參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--path` | ArkBot 專案根目錄 | （必要） |
| `--scope` | 測試範圍：python / packages / gemini / telegram / all | all |

## 檔案結構

```
env-smoke-test/
├── SKILL.md                    # 技能指令
├── README.md                   # 本文件
├── example/
│   └── env-smoke-test-spec.md  # Skill Spec 範例
├── references/
│   └── check-items.md          # 詳細檢查項目清單
└── scripts/
    └── env_smoke_test.py       # 環境煙霧測試主腳本
```

## 搭配使用

| 技能 | 職責 |
|------|------|
| `env-smoke-test`（本技能） | 驗證執行環境（Python、套件、API） |
| `smoke-test-runner` | 驗證專案結構（檔案、語法、匯入、功能） |

建議流程：先跑 `env-smoke-test` 確認環境就緒，再跑 `smoke-test-runner` 驗證專案完整性。

## 變更紀錄

### 0.1.0（2026-03-18）
- 初始版本
- 支援 4 項檢查：Python 版本、套件安裝、Gemini API、Telegram Token
- 支援 `--scope` 參數選擇測試範圍
