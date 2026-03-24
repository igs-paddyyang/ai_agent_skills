# DSL Generator Prompt 設計指南

DSL Generator 是系統中唯一使用 LLM 的環節。Prompt 的核心限制：只產出 JSON DSL，不產出 HTML。

## Prompt 策略

### 輸入給 LLM 的資訊

不要把完整 JSON 丟給 LLM。而是提取摘要：

```python
def build_data_summary(data: dict) -> str:
    """產生資料摘要，供 LLM 理解資料結構"""
    summary = {
        "fields": list(data.keys()),
        "sample": {}
    }
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            summary["sample"][key] = {
                "type": "array",
                "length": len(value),
                "columns": list(value[0].keys()) if isinstance(value[0], dict) else [],
                "first_row": value[0] if isinstance(value[0], dict) else value[0],
            }
        elif isinstance(value, dict):
            summary["sample"][key] = {
                "type": "object",
                "keys": list(value.keys()),
            }
        else:
            summary["sample"][key] = {"type": type(value).__name__, "value": value}
    return json.dumps(summary, ensure_ascii=False, indent=2)
```

### Prompt 模板核心

見 `assets/dsl_prompt.txt`。關鍵要素：

1. 角色設定：BI Dashboard Planner
2. 硬性限制：只產出 JSON DSL，不產出 HTML
3. 支援的 widget type 清單與必要欄位
4. 資料摘要（非完整資料）
5. 輸出格式範例

### 常見問題與對策

| 問題 | 對策 |
|------|------|
| LLM 產出 HTML 而非 DSL | Prompt 中多次強調「ONLY output JSON DSL」 |
| source 路徑錯誤 | 在 prompt 中列出所有可用的 source 路徑 |
| 選錯圖表類型 | 提供圖表選擇指南（時間序列→折線、分類比較→長條、佔比→圓餅） |
| 產出非法 JSON | 使用 json.loads() 驗證，失敗則重試 1 次 |

### 圖表選擇指南（嵌入 Prompt）

```
Chart Type Selection Guide:
- Time series data (dates) → line_chart
- Category comparison → bar_chart
- Distribution / proportion → pie_chart
- Detailed records → table
- Summary metrics → kpi_group
```

## Fallback 策略

LLM 產出非法 DSL 時（重試 1 次仍失敗），使用 fallback DSL：

```python
def build_fallback_dsl(data: dict, title: str) -> dict:
    """產生最基礎的 fallback DSL — 只有 table widget"""
    widgets = []
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            widgets.append({
                "id": f"table_{key}",
                "type": "table",
                "source": key,
                "title": key,
            })
    return {
        "title": title or "Data Dashboard",
        "theme": "light",
        "layout": "grid",
        "widgets": widgets[:5],  # 最多 5 個 table
    }
```
