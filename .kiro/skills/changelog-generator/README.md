# 變更紀錄產生器（Changelog Generator）

> 從 git commits 自動產生結構化的變更紀錄，支援 Conventional Commits 解析與版本號推導。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.1 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-24 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

從 git commits 自動產生結構化的變更紀錄（changelog）。核心功能包含 Conventional Commits 格式解析（feat/fix/docs/refactor 等 11 種 type）、版本號自動推導（基於 Semantic Versioning）、Markdown 格式輸出（含 emoji 分類標題），以及整合到 README.md 變更紀錄區塊的能力。

## 使用方式

觸發此技能的方式：

```
「幫我產生這個專案的 changelog」
「整理最近的 git commits 為變更紀錄」
「推導下一個版本號」
「產生 release notes」
「更新 README 的變更紀錄」
```

## 檔案結構

```
.kiro/skills/changelog-generator/
├── SKILL.md                          # 主要技能指令（changelog 產生流程）
├── README.md                         # 本文件
└── references/                       # 詳細指南（按需載入）
    └── conventional-commits.md       # Conventional Commits 規範與團隊導入指南
```

## 設計參考

本技能參考 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 的 Changelog Generator Skill，
以及 [Conventional Commits](https://www.conventionalcommits.org/) 規範，針對本專案的 Kiro Skill 版本管理需求進行調整。

## 變更紀錄

### v0.1.1（2026-03-25）
- SKILL.md frontmatter 驗證通過（移除非預期屬性、修正格式）
- 審閱 SKILL.md 內容品質，確認結構完整

### v0.1.0（2026-03-24）
- 初始版本建立
- Conventional Commits 格式解析（11 種 type）
- 版本號自動推導（Semantic Versioning）
- Markdown 格式輸出（含 emoji 分類）
- 整合到 README.md 變更紀錄區塊
- 非 Conventional Commits 的容錯處理
- 1 個 references 檔案（conventional-commits.md）
