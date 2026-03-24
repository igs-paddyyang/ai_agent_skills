# 通用 Canvas 數據契約

## 標準格式

Gemini Canvas 儀表板接受以下標準 JSON 結構。所有區塊皆為選填，
Gemini 會根據提供的區塊自動產出對應的視覺化元件。

### 頂層欄位

| 欄位 | 型態 | 必填 | 說明 |
|------|------|------|------|
| title | string | 否 | 儀表板標題 |
| kpi_cards | array | 否 | KPI 指標卡片 |
| trend_data | array | 否 | 時間序列趨勢資料 |
| category_ratio | array | 否 | 分類佔比資料 |
| recent_transactions | array | 否 | 明細表格資料 |

### kpi_cards

```json
[
  {
    "title": "指標名稱",
    "value": "顯示值（字串）",
    "trend": "+12%",
    "color": "blue|green|purple|red|orange"
  }
]
```

### trend_data

```json
[
  { "date": "03-01", "field_1": 520, "field_2": 8200 }
]
```

- `date` 為 X 軸標籤
- 其餘數值欄位自動成為折線圖的各條線

### category_ratio

```json
[
  { "name": "分類名稱", "value": 45 }
]
```

- 自動產出 Doughnut Chart

### recent_transactions

```json
[
  { "id": "TX001", "user": "User_1", "amount": "$320", "status": "成功" }
]
```

- 自動產出斑馬紋表格
- `status` 欄位自動套用狀態色標

## 自訂格式

若 JSON 不符合標準格式，Gemini 會自動推斷：

- 頂層為陣列 → 表格
- 物件含數值欄位 → KPI 卡片
- 陣列含 name + value → 圓餅圖
- 陣列含日期 + 數值 → 折線圖
- 巢狀結構 → 分區塊顯示
