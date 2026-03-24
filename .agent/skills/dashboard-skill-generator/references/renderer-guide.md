# Component Renderer 實作指南

Renderer 是純程式碼，不依賴 LLM。每個 widget type 對應一個 renderer 函式。

## Component Registry

```python
COMPONENT_REGISTRY = {
    "kpi_group": render_kpi_group,
    "line_chart": render_line_chart,
    "bar_chart": render_bar_chart,
    "pie_chart": render_pie_chart,
    "table": render_table,
}
```

新增 widget type 時，只需：
1. 在 Registry 加入對應函式
2. 實作 `render_xxx(widget, data) -> str` 函式
3. 在 DSL Schema 文件加入定義

## Renderer 函式簽名

```python
def render_xxx(widget: dict, data: dict) -> str:
    """
    Args:
        widget: DSL 中的 widget 定義（含 id, type, source, ...）
        data: 完整的原始 JSON 資料
    Returns:
        HTML 片段字串（不含 <html>/<body>，只有 widget 區塊）
    """
```

## 資料存取

使用 `resolve_source(data, source_path)` 函式解析 dot notation：

```python
def resolve_source(data: dict, path: str):
    """解析 dot notation 路徑，如 'distribution.by_country'"""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current
```

## 各 Widget Renderer 要點

### render_kpi_group

- 從 source 取得 KPI 陣列
- 每張卡片包含：title、value、trend badge（正值綠、負值紅）
- 使用 grid 佈局，columns 決定每列幾張（預設 4）
- 卡片有 glass-morphism 效果

### render_line_chart / render_bar_chart

- 從 source 取得資料陣列
- x 欄位作為 labels
- metrics 陣列中每個欄位作為一條線 / 一組柱
- 使用 Chart.js 初始化，每個圖表有唯一 canvas id
- 配色使用預定義調色盤

### render_pie_chart

- 從 source 取得資料陣列
- dimension 欄位作為 labels
- metric 欄位作為 values
- 使用 Chart.js Doughnut 類型

### render_table

- 從 source 取得資料陣列
- 自動從第一筆資料的 keys 產生表頭
- 交替列背景色
- 支援 overflow-x-auto 橫向捲動

## Chart.js 配色

```python
CHART_COLORS = [
    "#2563eb",  # blue
    "#10b981",  # green
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#8b5cf6",  # purple
    "#6b7280",  # gray
    "#ec4899",  # pink
    "#14b8a6",  # teal
]
```

## HTML 組裝

Layout Planner 決定 widget 排列：
1. kpi_group → 頂部，全寬
2. chart 類（line_chart / bar_chart / pie_chart）→ 中間，2 欄 grid
3. table → 底部，全寬

最終由 HTML Assembler 將所有片段嵌入 `assets/base_template.html`。
