# 遊戲企劃文件撰寫師（Game Design Document Writer）

> 根據遊戲構想產出結構化的遊戲企劃文件（GDD），涵蓋概念、玩法、敘事、美術、音效、技術與營運規劃。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.1 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-19 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

根據使用者的遊戲構想，產出完整的遊戲企劃文件（Game Design Document）。支援兩種輸出模式：完整 GDD（10 章節）和精簡版 One Pager。內建 8 種遊戲類型的章節側重指南，自動調整重點章節深度。

## 使用方式

觸發此技能的方式：

```
「幫我設計一個末日殭屍捕魚機博弈遊戲」
「寫一個開放世界 RPG 的 GDD，參考薩爾達」
「設計一個手機休閒消除遊戲，onepager 模式」
「幫我寫遊戲企劃文件」
```

## 檔案結構

```
.kiro/skills/game-design-document-writer/
├── SKILL.md              # 主要技能指令
├── README.md             # 本文件
├── example/
│   ├── zombie-fishing-machine-gdd.md         # 末日殭屍捕魚機 GDD（完整範例）
│   ├── zombie-fishing-machine-prompt.md      # GDD 提詞範本
│   └── zombie-fishing-machine-references.md  # 遊戲企劃規格書（參考資料）
├── references/
│   ├── gdd-template.md   # GDD 10 章節模板 + One Pager 模板
│   └── genre-guides.md   # 8 種遊戲類型章節側重指南
└── spec/
    └── game-design-document-writer-spec.md   # Skill Spec
```

## 變更紀錄

### v0.1.1（2026-03-25）
- 安裝 pyyaml 後 YAML folded scalar description 驗證通過
- 審閱 SKILL.md 內容品質，確認結構完整

### v0.1.0（2026-03-19）
- 初始版本建立
- 支援完整 GDD（10 章節）和 One Pager 兩種輸出模式
- 內建 8 種遊戲類型側重指南
- 參考 Indie Game Academy GDD 模板、業界標準 GDD 結構
