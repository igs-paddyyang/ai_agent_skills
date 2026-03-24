# Dashboard DSL Schema

Dashboard DSL 是系統的核心中間格式。LLM 只產出 DSL，Renderer 只消費 DSL。

## 頂層結構

```json
{
  "title": "string（必要）— 儀表板標題",
  "theme": "string（選用）— light | dark，預設 light",
  "layout": "string（選用）— grid，預設 grid",
  "widgets": [
    { "...widget 定義" }
  ]
}
```

## Widget 定義

每個 widget 必須包含 `id`、`type`、`source`，其餘欄位依 type 而定。

### 共用欄位

| 欄位 | 必要 | 說明 |
|------|------|------|
| `id` | 是 | 唯一識別碼（snake_case） |
| `type` | 是 | widget 類型（見下方） |
| `source` | 是 | 資料路徑（支援 dot notation，如 `distribution.by_country`） |
| `title` | 否 | widget 標題（顯示在卡片上方） |

### kpi_group

KPI 卡片群組，自動從 source 陣列產生多張卡片。

```json
{
  "id": "kpi_main",
  "type": "kpi_group",
  "source": "kpi",
  "columns": 4
}
```

source 資料格式（陣列）：
```json
[
  { "title": "總營收", "value": "$1.2M", "trend": "+5.2%", "color": "blue" },
  { "title": "活躍用戶", "value": "3,420", "trend": "-2.1%", "color": "green" }
]
```

KPI 物件欄位：
- `title`（必要）：指標名稱
- `value`（必要）：顯示值（字串，已格式化）
- `trend`（選用）：趨勢文字（如 `+5.2%`），正值綠色、負值紅色
- `color`（選用）：卡片主色（blue / green / yellow / red / purple）

### line_chart

折線圖，適合時間序列趨勢。

```json
{
  "id": "trend_chart",
  "type": "line_chart",
  "source": "trend",
  "x": "date",
  "metrics": ["daily_bet", "daily_win", "active_users"],
  "title": "每日趨勢"
}
```

| 欄位 | 必要 | 說明 |
|------|------|------|
| `x` | 是 | X 軸欄位名（通常是日期） |
| `metrics` | 是 | Y 軸指標欄位名陣列 |

### bar_chart

長條圖，適合分類比較。

```json
{
  "id": "game_compare",
  "type": "bar_chart",
  "source": "top_games",
  "x": "game_name",
  "metrics": ["revenue", "players"],
  "title": "遊戲排行"
}
```

欄位同 line_chart。

### pie_chart

圓餅圖，適合佔比分佈。

```json
{
  "id": "country_dist",
  "type": "pie_chart",
  "source": "distribution.by_country",
  "dimension": "country",
  "metric": "daily_bet",
  "title": "國家分佈"
}
```

| 欄位 | 必要 | 說明 |
|------|------|------|
| `dimension` | 是 | 分類欄位名 |
| `metric` | 是 | 數值欄位名（單一） |

### table

數據表格，自動從 source 陣列產生表頭與列。

```json
{
  "id": "vip_table",
  "type": "table",
  "source": "distribution.by_vip",
  "title": "VIP 等級分析"
}
```

無額外必要欄位，自動從資料的 key 產生表頭。

## 完整範例

```json
{
  "title": "營收分析儀表板",
  "theme": "light",
  "layout": "grid",
  "widgets": [
    {
      "id": "kpi_main",
      "type": "kpi_group",
      "source": "kpi",
      "columns": 4
    },
    {
      "id": "trend_chart",
      "type": "line_chart",
      "source": "trend",
      "x": "date",
      "metrics": ["daily_bet", "daily_win", "active_users"],
      "title": "每日趨勢"
    },
    {
      "id": "country_dist",
      "type": "pie_chart",
      "source": "distribution.by_country",
      "dimension": "country",
      "metric": "daily_bet",
      "title": "國家分佈"
    },
    {
      "id": "vip_table",
      "type": "table",
      "source": "distribution.by_vip",
      "title": "VIP 等級分析"
    }
  ]
}
```

## Source 路徑解析

source 支援 dot notation 存取巢狀資料：

- `"kpi"` → `data["kpi"]`
- `"distribution.by_country"` → `data["distribution"]["by_country"]`
- `"stats.daily"` → `data["stats"]["daily"]`

路徑不存在時，DSL Validator 會回報錯誤。
