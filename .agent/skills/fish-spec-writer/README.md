# 捕魚機規格撰寫師（Fish Spec Writer）

> 根據捕魚機遊戲類型，產出完整的遊戲機台規格文件，涵蓋魚種分值表、砲台倍率系統、特殊功能、RTP 機率分析、硬體機台規格、營運參數等。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-20 |
| 最後更新 | 2026-03-20 |
| 平台 | Antigravity / Kiro |
| 語言 | 繁體中文 |

## 功能說明

根據使用者的捕魚機遊戲需求，參考業界標準（Ocean King / Sea King 系列），自動產出結構化的遊戲機台規格文件。支援完整規格文件（9 章節）和精簡版速查表兩種輸出模式。

## 使用方式

觸發此技能的方式：

```
「幫我做一個捕魚機遊戲的規格文件」
「我需要一份 Ocean King 風格的捕魚機規格」
「幫我設計一款海洋主題的捕魚機」
「產出捕魚機速查表」
「列出海王2的魚種分值和砲台倍率」
「設計一款新的捕魚遊戲機台」
「分析捕魚機的 RTP 和機率系統」
```

## 支援的輸出模式

| 模式 | 說明 | 適用場景 |
|------|------|---------|
| `full`（預設） | 9 章節完整規格文件 | 產品開發、完整企劃 |
| `quickref` | 4 區塊精簡速查表 | 現場參考、快速查閱 |

## 檔案結構

```
.agent/skills/fish-spec-writer/
├── SKILL.md              # 主要技能指令
├── README.md             # 本文件
└── references/           # 詳細指南（按需載入）
    ├── ocean-king-spec.md    # 海王系列完整規格參考
    └── fish-species-db.md    # 魚種資料庫與分值對照表
```

## 產出文件結構（full 模式）

1. 遊戲概述（Overview）
2. 核心玩法（Core Gameplay）
3. 魚種與分值系統（Fish Species & Payout Table）
4. 特殊功能與迷你遊戲（Mini-Games & Special Features）
5. 砲台與倍率系統（Cannon & Multiplier System）
6. RTP 與機率系統（Return to Player & Probability）
7. 機台硬體規格（Arcade Cabinet Specifications）
8. 營運與合規（Operations & Compliance）
9. 競品對比（Competitive Analysis）

## 變更紀錄

### v0.1.0（2026-03-20）
- 初始版本建立
- 完成 SKILL.md 核心指令
- 建立 references/ocean-king-spec.md 海王系列參考規格
- 建立 references/fish-species-db.md 魚種資料庫
