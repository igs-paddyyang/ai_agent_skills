# Gemini Canvas 通用儀表板（Gemini Canvas Dashboard）

> 餵入任意 data.json，透過 Gemini API 自動產出專業 HTML 儀表板。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 1.0.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-17 |
| 最後更新 | 2026-03-17 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

接受任意結構化 JSON 資料，透過 Gemini API 自動推斷最佳視覺化方式，產出包含 Tailwind CSS + Chart.js 的獨立 HTML 儀表板。支援 KPI 卡片、趨勢圖、佔比圖、數據表格等視覺化元件。與 `market-revenue-dashboard`（專用營收報表、固定模板）不同，本技能為通用型，適用於任何數據場景。可整合至 TigerBot 透過對話觸發。

> **與 `dashboard-skill-generator` 的差異**：本技能由 Gemini 自由排版，適合快速原型和探索性分析；`dashboard-skill-generator` 走 DSL 確定性路線（JSON → DSL → Renderer），適合產品級穩定輸出。需要穩定可控的儀表板時，請使用 `dashboard-skill-generator`。

## 使用方式

觸發此技能的方式：

```
「幫我用這份 data.json 產生儀表板」
「generate dashboard」
「產生一個銷售分析的視覺化儀表板」
「canvas dashboard」
```

CLI 用法：

```bash
py scripts/generate_canvas.py --input data/my_data.json
py scripts/generate_canvas.py --input data/my_data.json --output data/my_dashboard.html --title "銷售分析儀表板"
```

## 檔案結構

```
.kiro/skills/gemini-canvas-dashboard/
├── SKILL.md                        # 主要技能指令
├── README.md                       # 本文件
├── references/
│   └── canvas_data_contract.md     # 通用數據契約
├── scripts/
│   └── generate_canvas.py          # 核心產生腳本
└── assets/
    └── prompt_template.txt         # Gemini 提詞模板
```

## 變更紀錄

### v1.0.0（2026-03-17）
- 初始版本建立
- 支援標準格式與自訂 JSON 結構
- 整合 TigerBot DASHBOARD 意圖
