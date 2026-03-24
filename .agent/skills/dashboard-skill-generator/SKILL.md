---
name: dashboard-skill-generator
description: >
  產品級 Dashboard 產生器。將 JSON 資料透過 AI 轉換為 Dashboard DSL，再由確定性 Renderer 產出穩定的 HTML 儀表板。
  採用三層架構（JSON → DSL → Renderer → HTML），取代 LLM 直出 HTML 的不穩定模式。
  支援 KPI 卡片、折線圖、圓餅圖、長條圖、數據表格等元件，可接入 ArkBot / ArkAgent OS 的 Skill Runtime。
  當使用者提到 dashboard generator、儀表板產生器、DSL 儀表板、dashboard skill、
  產生儀表板引擎、dashboard engine、BI 儀表板、AI 儀表板、dashboard-skill-generator 時，請使用此技能。
---

# Dashboard Skill Generator

產品級 AI-Native Dashboard 產生器。核心理念：LLM 只負責「理解資料 → 產出 DSL」，HTML 渲染由確定性程式碼完成。

## 架構概覽

```
JSON Data → [Data Validator] → [DSL Generator (AI)] → [DSL Validator] → [Renderer (Code)] → HTML
```

三層分離的好處：
- DSL 是可驗證的中間格式，壞了能定位是 AI 還是 Renderer 的問題
- Renderer 是純程式碼，不依賴 LLM，輸出永遠穩定
- 新增 widget type 只需擴充 Component Registry，不需改 prompt

## 工作流程

### 步驟 1：資料驗證

讀取使用者提供的 JSON 資料，執行基本驗證：
- 非空、可序列化
- 偵測資料類型（revenue / slots / fish / general）
- 提取欄位清單與資料統計

### 步驟 2：DSL 產生

根據 mode 決定 DSL 來源：

- `mode=auto`（預設）：將資料摘要送給 Gemini API，產出 Dashboard DSL
  - Prompt 核心限制：「只產出 JSON DSL，不產出 HTML」
  - 使用 `assets/dsl_prompt.txt` 作為 prompt 模板
- `mode=dsl`：使用者直接提供 DSL，跳過 AI

DSL Schema 定義在 `references/dsl-schema.md`，產出時參考該文件。

### 步驟 3：DSL 驗證

驗證 DSL 結構：
- 必要欄位存在（title, widgets）
- 每個 widget 的 type 在支援清單中
- widget.source 路徑在 data 中存在
- widget.metrics / dimension 欄位在 source 中存在

驗證失敗時回傳具體錯誤訊息（哪個 widget 的哪個欄位有問題）。

### 步驟 4：渲染

使用 `scripts/generate_dashboard.py` 執行渲染流程：

```bash
# 基本用法
py scripts/generate_dashboard.py --input data.json

# 指定輸出
py scripts/generate_dashboard.py --input data.json --output output.html

# 使用自訂 DSL
py scripts/generate_dashboard.py --input data.json --dsl my_dsl.json --mode dsl

# 指定主題
py scripts/generate_dashboard.py --input data.json --theme dark
```

渲染流程（純程式碼，不用 LLM）：
1. Layout Planner 根據 widget 數量決定 grid 佈局
2. Component Registry 將每個 widget type 對應到 renderer 函式
3. 每個 renderer 讀取 DSL widget 定義 + data source，產出 HTML 片段
4. HTML Assembler 套用 base template，嵌入所有片段

### 步驟 5：輸出

產出結果：
- HTML 檔案存至 `data/dashboard/{type}/{date}_{time}.html`
- 回傳 `{ html_path, dsl, metadata }`

## 支援的 Widget Types

| type | 說明 | 必要欄位 |
|------|------|---------|
| `kpi_group` | KPI 卡片群組 | source |
| `line_chart` | 折線圖（趨勢） | source, x, metrics |
| `bar_chart` | 長條圖（比較） | source, x, metrics |
| `pie_chart` | 圓餅圖（佔比） | source, dimension, metric |
| `table` | 數據表格 | source |

新增 widget type 時，在 Component Registry 加入對應的 renderer 函式即可。

## 邊界案例處理

- 空資料 → 回傳錯誤，不產出 HTML
- DSL 驗證失敗 → 回傳具體欄位錯誤
- LLM 產出非法 DSL → 重試 1 次，仍失敗則 fallback 為基礎 DSL（只有 table）
- 不支援的 widget type → 跳過，log warning，繼續渲染其餘
- 超大資料 → 截斷至前 500 筆送 LLM，完整資料仍嵌入 HTML

## 附帶資源

- `scripts/generate_dashboard.py` — CLI 入口 + 完整渲染引擎
- `references/dsl-schema.md` — Dashboard DSL 完整 Schema 定義與範例
- `references/renderer-guide.md` — Component Renderer 實作指南
- `references/prompt-guide.md` — DSL Generator Prompt 設計指南
- `assets/base_template.html` — HTML 基底模板
- `assets/dsl_prompt.txt` — Gemini DSL 產生 Prompt 模板
