# 技能規格撰寫師（Skill Spec Writer）

> 為 Kiro Skill 產出輕量、結構化的規格文件，可直接作為 skill-creator 的輸入。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.2.1 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-18 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

將技能構想轉化為結構化的 Skill Spec 文件，對齊 skill-creator 的輸入格式。產出的 Spec 涵蓋技能定義、行為規格、資源需求與測試案例，讓 skill-creator 能跳過意圖釐清階段直接進入檔案產生。

## 使用方式

觸發此技能的方式：

```
「幫我規劃一個 [技能名稱] 技能的規格」
「我想做一個技能，先幫我寫 skill spec」
「設計一個 [功能描述] 的技能規格」
「幫這個技能寫 spec 給 skill-creator 用」
```

## 與其他技能的關係

```
skill-spec-writer    → 技能級規格（Skill Spec）
  ↓
skill-creator        → 消費 Spec，產出 Skill Package
```

- `software-spec-writer`：專案級規格（多模組、多 Phase）
- `skill-spec-writer`：技能級規格（單一觸發、單一行為）

## 檔案結構

```
.kiro/skills/skill-spec-writer/
├── SKILL.md              # 主要技能指令
├── README.md             # 本文件
└── references/           # 詳細指南（按需載入）
    ├── spec-examples.md  # Skill Spec 範例（2 個完整範例）
    └── skill-standards.md # Agent Skills 標準與範例參考
```

## 變更紀錄

### v0.2.1（2026-03-25）
- 移除 SKILL.md frontmatter 中非預期的 `author` 屬性（通過 quick_validate 驗證）

### v0.2.0（2026-03-18）
- 新增 `references/skill-standards.md` — 整合 Agent Skills 規範、官方與社群技能範例
- SKILL.md 新增「參考資源」章節，引導在階段 2/3 參考外部標準
- 資料來源：[anthropics/skills](https://github.com/anthropics/skills)、[antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### v0.1.0（2026-03-18）
- 初始版本建立
- 5 階段工作流程：意圖釐清 → 行為定義 → 資源規劃 → 測試案例 → 產出規格
- 產出格式對齊 skill-creator 階段 1 的 4 個核心問題
- 自我檢核清單確保 Spec 品質
