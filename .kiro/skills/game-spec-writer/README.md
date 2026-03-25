# 遊戲機台規格撰寫師（Game Spec Writer）

> 根據遊戲機台類型（捕魚機、老虎機、棋牌等），產出完整的遊戲機台規格文件。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.2.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-20 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

根據使用者的遊戲機台需求，產出結構化的規格文件。支援多種遊戲類型（捕魚機、老虎機、棋牌），每種類型有專屬的參考指南。支援完整規格文件（9 章節）和精簡版速查表兩種輸出模式。

由 `fish-spec-writer` v0.1.1 泛化而來，保留原有捕魚機規格能力，擴展支援老虎機和棋牌。

## 使用方式

```
「幫我設計一個捕魚機規格」
「設計一個五軸老虎機的規格文件」
「產出百家樂的機台規格」
「game spec 龍虎」
「幫我做一個 Ocean King 風格的捕魚機」
```

## 檔案結構

```
game-spec-writer/
├── SKILL.md                              # 主要技能指令（通用框架）
├── README.md                             # 本文件
└── references/
    ├── fish-game.md                      # 捕魚機規格指南
    ├── fish-game-ocean-king.md           # 海王系列完整規格參考
    ├── fish-game-species-db.md           # 魚種資料庫
    ├── slot-machine.md                   # 老虎機規格指南
    └── card-game.md                      # 棋牌規格指南
```

## 變更紀錄

### v0.2.0（2026-03-25）
- 從 `fish-spec-writer` 泛化為通用遊戲機台規格撰寫師
- SKILL.md 改為通用 9 章節框架，根據遊戲類型載入對應 reference
- 新增 `references/slot-machine.md`（老虎機規格指南）
- 新增 `references/card-game.md`（棋牌規格指南）
- 原有捕魚機內容保留於 `references/fish-game*.md`
- 重命名 `fish-spec-writer` → `game-spec-writer`

### v0.1.1（2026-03-25）
- 移除 SKILL.md frontmatter 中非預期的 `author` 屬性
- 審閱 SKILL.md 內容品質，確認結構完整

### v0.1.0（2026-03-20）
- 初始版本建立（fish-spec-writer）
- 捕魚機專用規格文件（9 章節 + 速查表）
- 含海王系列參考與魚種資料庫
