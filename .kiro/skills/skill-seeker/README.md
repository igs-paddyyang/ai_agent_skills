# 技能探索器（Skill Seeker）

> 讀取文件來源（URL、GitHub repo、本地檔案）並自動轉換為完整的 Kiro Skill 草稿目錄。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.2.1 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-24 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

將任意文件來源自動轉換為符合 Kiro Skill 規範的技能草稿。支援 4 種來源類型（URL、GitHub、本地檔案、本地目錄），
透過三階段流程（擷取 → 結構化 → 產生）產出包含 SKILL.md、README.md 與 references/ 的完整技能目錄。

## 使用方式

觸發此技能的方式：

```
「幫我把 https://fastapi.tiangolo.com/ 轉成一個 Kiro Skill」
「從 langchain-ai/langchain 這個 GitHub repo 建立技能」
「把 docs/fish-game-sea-king-spec.md 這個本地檔案轉成技能」
「從文件建立技能」
「doc to skill」
```

## 檔案結構

```
.kiro/skills/skill-seeker/
├── SKILL.md                          # 主要技能指令（三階段轉換流程）
├── README.md                         # 本文件
└── references/                       # 詳細指南（按需載入）
    ├── conversion-guide.md           # 來源類型轉換策略與內容分類規則
    └── output-templates.md           # 產出範本與範例
```

## 設計參考

本技能的設計借鏡 [Skill Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) 的三階段架構，
但不做獨立爬蟲工具，而是作為純 Kiro Skill 指令，利用平台已有的 web fetch / readFile 工具擷取內容。

## 變更紀錄

### v0.2.1（2026-03-25）
- SKILL.md frontmatter 驗證通過（移除非預期屬性、修正格式）
- 審閱 SKILL.md 內容品質，確認結構完整

### v0.2.0（2026-03-24）
- 技能更名：doc-to-skill-converter → skill-seeker
- 更新所有檔案中的名稱引用

### v0.1.0（2026-03-24）
- 初始版本建立
- 支援 4 種來源類型：URL、GitHub、本地檔案、本地目錄
- 三階段轉換流程：Ingest → Structure → Generate
- 自我檢核機制確保產出符合 Kiro Skill 規範
