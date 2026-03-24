---
name: gemini-canvas-dashboard
author: paddyyang
description: >
  通用 Gemini Canvas 儀表板產生器。餵入任意 data.json，透過 Gemini API 自動產出專業 HTML 儀表板。
  支援 KPI 卡片、趨勢圖、佔比圖、數據表格等視覺化元件，可整合至 TigerBot 開啟。
  當使用者提到 canvas、儀表板產生、generate dashboard、視覺化、data.json 儀表板、
  產生圖表、canvas dashboard、通用儀表板時，請務必使用此技能。
---

# Gemini Canvas 通用儀表板技能

## 概述

本技能接受任意結構化 JSON 資料，透過 Gemini API 自動推斷最佳視覺化方式，
產出包含 Tailwind CSS + Chart.js 的獨立 HTML 儀表板。

與 `market-revenue-dashboard`（專用營收報表、固定模板）不同，本技能為通用型，
適用於任何數據場景。

## 數據契約

### 標準格式（建議）

```json
{
  "title": "儀表板標題",
  "kpi_cards": [{ "title": "指標名", "value": "數值", "trend": "+12%", "color": "blue" }],
  "trend_data": [{ "date": "03-01", "users": 520, "revenue": 8200 }],
  "category_ratio": [{ "name": "分類", "value": 45 }],
  "recent_transactions": [{ "id": "TX001", "user": "User_1", "amount": "$320", "status": "成功" }]
}
```

### 自訂格式

也可餵入任意 JSON 結構，Gemini 會自動推斷：
- 陣列 → 表格或圖表
- 數值欄位 → KPI 卡片或趨勢圖
- 分類 + 數值 → 圓餅圖或長條圖

## 執行方式

```bash
# 基本用法：指定 JSON 檔案
py scripts/generate_canvas.py --input data/my_data.json

# 指定輸出路徑
py scripts/generate_canvas.py --input data/my_data.json --output data/my_dashboard.html

# 指定儀表板標題
py scripts/generate_canvas.py --input data/my_data.json --title "銷售分析儀表板"
```

### 參數說明

| 參數 | 必填 | 說明 |
|------|------|------|
| `--input` | 是 | JSON 資料檔案路徑 |
| `--output` | 否 | HTML 輸出路徑（預設同目錄 `{input_name}_dashboard.html`） |
| `--title` | 否 | 儀表板標題（預設從 JSON 的 `title` 欄位讀取，或 "Data Dashboard"） |

## TigerBot 整合

使用者在對話中說「產生儀表板」或「canvas」時：

1. `intent_router.py` 分類為 `DASHBOARD` 意圖
2. `arkbot_core.py` 呼叫 `canvas_skill.generate_canvas_dashboard()`
3. 產出 HTML 存至 `tigerbot/data/`
4. 透過 `/canvas?file=xxx` 端點在瀏覽器開啟

## 技術棧

- Gemini API（`google-genai` SDK）
- 產出 HTML：Tailwind CSS (CDN) + Chart.js (CDN) + Inter 字型
- 配色：Main (#2563eb)、Success (#10b981)、Warning (#f59e0b)、Danger (#ef4444)

## 附帶資源

- `scripts/generate_canvas.py` — 核心產生腳本
- `assets/prompt_template.txt` — Gemini 提詞模板
- `references/canvas_data_contract.md` — 通用數據契約
