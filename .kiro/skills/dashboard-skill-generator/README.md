# Dashboard Skill Generator

> 產品級 AI-Native Dashboard 產生器。以 DSL 中間層取代 LLM 直出 HTML，確保穩定、可控、可擴展的儀表板輸出。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.3.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-24 |
| 最後更新 | 2026-03-24 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

三層架構 Dashboard 產生器：`JSON → DSL → Renderer → HTML`

> **與 `gemini-canvas-dashboard` 的差異**：本技能走 DSL 確定性路線，Renderer 為純程式碼渲染，產出穩定可控，適合產品級儀表板；`gemini-canvas-dashboard` 由 Gemini 自由排版，適合快速原型和探索性分析。需要快速產出時，請使用 `gemini-canvas-dashboard`。

- Data Validator：驗證 JSON 結構、偵測資料類型、提取欄位統計
- DSL Generator：透過 Gemini API 將資料轉換為 Dashboard DSL（或使用者直接提供）
- DSL Validator：驗證 DSL 結構、source 路徑、欄位對應
- Component Renderer：純程式碼渲染，支援 5 種 widget type（kpi_group / line_chart / bar_chart / pie_chart / table）
- HTML Assembler：套用 base template（Tailwind CSS + Chart.js），產出獨立 HTML

## 使用方式

觸發此技能的方式：

```
「產生儀表板引擎」
「用 DSL 產生 dashboard」
「dashboard-skill-generator」
「幫我建立 BI 儀表板」
```

CLI 用法：

```bash
# 基本用法
py scripts/generate_dashboard.py --input data.json

# 指定輸出與標題
py scripts/generate_dashboard.py --input data.json --output my_dashboard.html --title "營收分析"

# 使用自訂 DSL（跳過 AI）
py scripts/generate_dashboard.py --input data.json --dsl my_dsl.json --mode dsl
```

## 檔案結構

```
dashboard-skill-generator/
├── SKILL.md                          # 技能指令
├── README.md                         # 本文件
├── scripts/
│   └── generate_dashboard.py         # CLI 入口 + 渲染引擎
├── references/
│   ├── dsl-schema.md                 # DSL Schema 定義
│   ├── renderer-guide.md             # Renderer 實作指南
│   └── prompt-guide.md               # Prompt 設計指南
└── assets/
    ├── base_template.html            # HTML 基底模板
    └── dsl_prompt.txt                # Gemini Prompt 模板
```

## 變更紀錄

### v0.3.0（2026-03-24）
- 強化 `dsl_prompt.txt`：新增 CRITICAL 標記、範例 DSL、明確禁止捏造 source 路徑
- 智慧 `build_fallback_dsl`：自動偵測資料形狀（kpi_group / line_chart / bar_chart / table），取代舊版只產 table
- DSL 驗證失敗時自動 fallback（不再回傳 error），確保儀表板永遠能產出
- 新增 `_detect_array_shape()` + `_find_fields()` 輔助函式
- `_find_fields` 支援 category_hints（vip_level 等數值型類別欄位不誤判為 metric）

### v0.2.0（2026-03-24）
- 修復 assemble_html fade-in 動畫延遲無限迴圈（改用 re.sub 一次性替換）
- 支援 p-5（KPI）和 p-6 mb-6（charts/tables）兩種 card 樣式的動畫延遲
- E2E 測試通過：DSL mode 完整 pipeline（4 widgets, 12KB HTML）

### v0.1.0（2026-03-24）
- 初始版本
- 建立三層架構：Data Validator → DSL Generator → Renderer
- 支援 5 種 widget type：kpi_group / line_chart / bar_chart / pie_chart / table
- DSL Schema 定義
- Gemini API DSL 產生 Prompt
- HTML base template（Tailwind CSS + Chart.js + Inter 字型）
