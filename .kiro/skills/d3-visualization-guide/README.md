# D3.js 視覺化指引（D3 Visualization Guide）

> 產出 D3.js 互動圖表與資料視覺化，涵蓋折線圖、長條圖、圓餅圖等常用圖表，可與 gemini-canvas-dashboard 互補。

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

提供 D3.js 互動圖表的產出指引。核心內容包含 D3 資料綁定概念、Scale/Axis 設定、常用圖表範例（折線圖、長條圖、圓餅圖）、互動功能（Tooltip、響應式設計），以及與 gemini-canvas-dashboard 的互補定位說明。

## 使用方式

觸發此技能的方式：

```
「幫我畫一個折線圖」
「用 D3 做互動圖表」
「產出資料視覺化的 HTML」
「需要一個長條圖」
「D3.js 怎麼用」
```

## 檔案結構

```
.kiro/skills/d3-visualization-guide/
├── SKILL.md                          # 主要技能指令（D3 核心概念與常用圖表）
├── README.md                         # 本文件
└── references/                       # 詳細指南（按需載入）
    ├── d3-chart-recipes.md           # 更多圖表類型：散佈圖、樹狀圖、熱力圖
    └── d3-bindng-guide.md            # D3 資料綁定核心：enter/update/exit、transition
```

## 設計參考

本技能參考 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 的 D3.js Visualization Skill（by @chrisvoncsefalvay），
針對本專案的儀表板需求與 gemini-canvas-dashboard 的互補定位進行調整。

## 變更紀錄

### v0.1.0（2026-03-24）
- 初始版本建立
- D3 核心概念（資料綁定、Scale、Axis）
- 常用圖表範例（折線圖、長條圖、圓餅圖）
- 互動功能（Tooltip、響應式設計）
- 與 gemini-canvas-dashboard 互補定位說明
- 2 個 references 檔案（d3-chart-recipes.md、d3-bindng-guide.md）
