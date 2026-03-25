# 測試驅動開發工作流（TDD Workflow）

> 引導開發者遵循 Red-Green-Refactor 循環，在撰寫實作程式碼之前先寫測試。涵蓋 pytest 測試設計、邊界值分析、Mock 策略與測試反模式。

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

提供完整的測試驅動開發（TDD）工作流指引，以 Python pytest 為主要框架。核心流程為 Red-Green-Refactor 循環：先寫一個失敗的測試、寫最少的程式碼讓它通過、再重構。涵蓋測試設計模式（邊界值分析、等價類劃分）、Mock 策略、Bug 修復流程與完成檢查清單。

## 使用方式

觸發此技能的方式：

```
「幫我用 TDD 方式開發一個計算機模組」
「這個函式需要什麼測試案例？」
「先寫測試再寫實作」
「幫我設計 pytest 測試」
「用 Red-Green-Refactor 流程開發」
```

## 檔案結構

```
.kiro/skills/tdd-workflow/
├── SKILL.md                          # 主要技能指令（Red-Green-Refactor 循環）
├── README.md                         # 本文件
└── references/                       # 詳細指南（按需載入）
    ├── testing-patterns.md           # 測試設計模式：單元/整合/E2E、Mock 進階策略
    └── pytest-recipes.md             # pytest 常用配方：conftest.py、plugin、coverage
```

## 設計參考

本技能參考 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 的 test-driven-development Skill（by obra/superpowers），
針對本專案的 Python + pytest 環境進行在地化調整，並加入繁體中文指引。

## 變更紀錄

### v0.1.1（2026-03-25）
- SKILL.md frontmatter 驗證通過（移除非預期屬性、修正格式）
- 審閱 SKILL.md 內容品質，確認結構完整

### v0.1.0（2026-03-24）
- 初始版本建立
- Red-Green-Refactor 完整循環指引
- pytest 快速參考（參數化測試、Fixture 管理）
- 測試設計模式（邊界值分析、等價類劃分、Mock 策略）
- Bug 修復流程與完成檢查清單
- 2 個 references 檔案（testing-patterns.md、pytest-recipes.md）
