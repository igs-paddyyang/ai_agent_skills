# CI 自動化（CI Automation）

> 引導建立持續整合（CI）自動化流程，涵蓋本地 CI 模擬腳本與 GitHub Actions workflow。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-25 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

提供持續整合的三階段流程：Lint（ruff）→ Validate（quick_validate.py）→ Sync（skill-sync）。包含本地 CI 模擬腳本，可在提交前快速驗證。

## 使用方式

```
「幫我建立 CI 流程」
「設定 GitHub Actions」
「跑一次本地 CI」
「ci-automation」
```

本地執行：
```bash
py .kiro/skills/ci-automation/scripts/ci_local.py
```

## 檔案結構

```
ci-automation/
├── SKILL.md              # 技能指令
├── README.md             # 本文件
└── scripts/
    └── ci_local.py       # 本地 CI 模擬腳本
```

## 變更紀錄

### v0.1.0（2026-03-25）
- 初始版本建立
- 三階段 CI 流程：Lint → Validate → Sync
- 本地 CI 模擬腳本（ci_local.py）
- 支援 --skip-lint / --skip-sync 選項
