# 文件摘要師（Document Summarizer）

> 讀取本地長文件並產出結構化的摘要文件，包含一句話摘要、核心概念、分類表格與行動建議。

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

接受本地文件（Markdown、PDF、程式碼、純文字等），分析文件結構後產出結構化的 Markdown 摘要。與 `websearch-summarizer` 互補 — websearch 處理網頁 URL，document 處理本地檔案，兩者共用相同的輸出模板骨架。

## 使用方式

觸發此技能的方式：

```
「幫我整理這份文件 docs/arkbot-spec.md」
「摘要這個檔案的重點」
「讀這份規格文件給我重點」
「整理 src/ 目錄下的程式碼結構」
```

## 檔案結構

```
.kiro/skills/document-summarizer/
├── SKILL.md              # 主要技能指令
├── README.md             # 本文件
└── references/
    └── output-template.md  # 摘要文件模板（含各類文件的區塊組合）
```

## 變更紀錄

### v0.1.0（2026-03-19）
- 初始版本建立
- 支援 Markdown、PDF、程式碼、純文字等多種文件類型
- 包含 6 種文件類型的區塊組合模板（規格、設計、API、程式碼、會議紀錄、通用）
- 與 websearch-summarizer 共用輸出模板骨架
