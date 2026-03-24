# 網頁搜尋摘要師（WebSearch Summarizer）

> 搜尋並抓取網頁內容，產出結構化的摘要文件。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-19 |
| 最後更新 | 2026-03-19 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

接受 URL 或搜尋關鍵字，抓取網頁內容後產出結構化的 Markdown 摘要文件。摘要包含元資料、一句話摘要、核心概念、分類表格、關鍵細節與行動建議，讓使用者快速掌握資源全貌。

## 使用方式

觸發此技能的方式：

```
「幫我整理這個網站 https://github.com/example/repo」
「摘要這個 URL 的內容」
「搜尋 Kiro Skills 最佳實踐，整理成摘要」
「幫我看這個連結 https://docs.example.com/api」
```

## 檔案結構

```
.kiro/skills/websearch-summarizer/
├── SKILL.md              # 主要技能指令
├── README.md             # 本文件
├── example/
│   ├── anthropic-skills-summary.md            # Anthropic Skills 摘要範例
│   ├── antigravity-awesome-skills-summary.md  # Antigravity Skills 摘要範例
│   └── skillsmp-summary.md                    # SkillsMP 摘要範例
└── references/
    └── output-template.md  # 摘要文件模板與範例
```

## 變更紀錄

### v0.1.0（2026-03-19）
- 初始版本建立
- 支援 URL 直接抓取、GitHub Repo、搜尋關鍵字三種輸入
- 包含結構化摘要模板（references/output-template.md）
