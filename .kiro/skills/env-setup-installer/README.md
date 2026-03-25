# env-setup-installer（環境與服務安裝）

**一站式完成 ArkBot 專案的 Python 環境建置、套件安裝、API 連通性驗證。**
**作者**: paddyyang

| 項目 | 值 |
|------|-----|
| 版本 | 0.1.1 |
| 建立日期 | 2026-03-19 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

env-setup-installer 是一個環境建置技能，涵蓋 5 個階段：

1. Python 版本檢查與安裝指引
2. requirements.txt 套件自動安裝（缺失時自動 pip install）
3. .env 環境變數設定引導（自動從 .env.example 複製）
4. Google Gemini API 連通性驗證與可用模型清單
5. Telegram Bot Token 有效性驗證與 Bot 資訊

與 `env-smoke-test`（唯讀檢查）互補——本技能是「先裝再驗」。

## 使用方式

```
「幫我安裝 nana_bot 的環境」
「安裝環境並驗證 API」
「setup nana_bot environment」
「安裝套件到 nana_bot」
```

### 腳本直接執行

```bash
# 完整安裝（預設）
py .kiro/skills/env-setup-installer/scripts/env_setup.py --path nana_bot

# 僅安裝套件
py .kiro/skills/env-setup-installer/scripts/env_setup.py --path nana_bot --scope packages

# 驗證 Gemini API
py .kiro/skills/env-setup-installer/scripts/env_setup.py --path nana_bot --scope gemini
```

## 檔案結構

```
.kiro/skills/env-setup-installer/
├── SKILL.md                    # 主要技能指令
├── README.md                   # 本文件
├── references/
│   └── setup-guide.md          # 詳細檢查項目、套件對照表、排查指南
├── scripts/
│   └── env_setup.py            # 主要安裝與驗證腳本
└── spec/
    └── env-setup-installer-spec.md  # Skill Spec
```

## 變更紀錄

### v0.1.1（2026-03-25）
- SKILL.md frontmatter 驗證通過（移除非預期屬性、修正格式）
- 審閱 SKILL.md 內容品質，確認結構完整

### v0.1.0（2026-03-19）
- 初始版本
- 5 階段安裝流程：Python → 套件 → .env → Gemini → Telegram
- 自動安裝缺失套件（pip install -r requirements.txt）
- 自動從 .env.example 複製 .env
- 待辦事項清單輸出
