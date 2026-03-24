# 軟體架構指引（Software Architecture Guide）

> 提供軟體架構決策的結構化指引，涵蓋 Clean Architecture、SOLID 原則、設計模式與架構決策紀錄（ADR）。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-24 |
| 最後更新 | 2026-03-24 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

提供軟體架構決策的結構化指引。核心內容包含 Clean Architecture 四層分層原則（Entity → Use Case → Interface Adapter → Framework）、SOLID 五大原則的 Python 實踐範例、常用設計模式速查表、架構決策紀錄（ADR）格式，以及與 ArkBot 四層架構的對應關係。

## 使用方式

觸發此技能的方式：

```
「這個專案應該用什麼架構？」
「幫我做架構決策紀錄」
「檢查這段程式碼是否符合 SOLID 原則」
「用 Clean Architecture 重構這個模組」
「幫我選擇適合的設計模式」
```

## 檔案結構

```
.kiro/skills/software-architecture-guide/
├── SKILL.md                          # 主要技能指令（架構原則與決策指引）
├── README.md                         # 本文件
└── references/                       # 詳細指南（按需載入）
    ├── clean-architecture.md         # Clean Architecture 詳細分層與完整範例
    └── design-patterns.md            # 常用設計模式詳解與 Python 實作
```

## 設計參考

本技能參考 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 的 software-architecture Skill
以及 [NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit) 的 DDD plugin（15 composable rules），
針對本專案的 Python 環境與 ArkBot 架構進行在地化調整。

## 變更紀錄

### v0.1.0（2026-03-24）
- 初始版本建立
- Clean Architecture 四層分層原則與 Python 範例
- SOLID 五大原則的 Python 實踐
- 架構決策紀錄（ADR）格式與範例
- 常用設計模式速查表
- 與 ArkBot 四層架構的對應關係
- 2 個 references 檔案（clean-architecture.md、design-patterns.md）
