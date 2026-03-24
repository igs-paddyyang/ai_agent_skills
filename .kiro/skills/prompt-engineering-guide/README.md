# Prompt 工程指引（Prompt Engineering Guide）

> 系統化的 prompt 設計方法論，涵蓋 SKILL.md description 撰寫公式、指令設計原則與常見反模式修正。

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

提供系統化的 prompt 設計方法論，特別針對 Kiro Skill 的 description 撰寫與指令設計。核心內容包含 description 撰寫公式（功能描述 + 觸發關鍵字）、指令設計五大原則（祈使句、漸進式揭露、結構化、具體範例、限制邊界）、常見反模式與修正方式、品質自我檢核清單，以及改善既有技能的流程。

## 使用方式

觸發此技能的方式：

```
「幫我改善這個技能的 description」
「這個 prompt 怎麼寫比較好？」
「檢查這個 SKILL.md 的品質」
「幫我設計觸發關鍵字」
「prompt engineering 最佳實踐」
```

## 檔案結構

```
.kiro/skills/prompt-engineering-guide/
├── SKILL.md                              # 主要技能指令（description 公式與指令設計原則）
├── README.md                             # 本文件
└── references/                           # 詳細指南（按需載入）
    ├── anthropic-best-practices.md       # Anthropic 官方 prompt 最佳實踐摘要
    └── skill-description-examples.md     # 優秀 description 範例集與分析
```

## 設計參考

本技能參考 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 的 prompt-engineering Skill
以及 Anthropic 官方 prompt engineering 文件，針對 Kiro Skill 的 description 撰寫需求進行在地化調整。

## 變更紀錄

### v0.1.0（2026-03-24）
- 初始版本建立
- Description 撰寫公式與檢核清單
- 指令設計五大原則（祈使句、漸進式揭露、結構化、具體範例、限制邊界）
- 常見反模式與修正表
- SKILL.md 品質評分標準
- 改善既有技能的流程
- 2 個 references 檔案（anthropic-best-practices.md、skill-description-examples.md）
