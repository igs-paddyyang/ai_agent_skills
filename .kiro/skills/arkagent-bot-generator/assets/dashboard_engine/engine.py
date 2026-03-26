"""Dashboard Engine — 三層架構：JSON → DSL → Renderer → HTML

從 dashboard-skill-generator 移植，內嵌於 NinjaBot-Agent。
不含 CLI 入口，僅提供 generate_dashboard() 等函式。
"""
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ── 路徑設定 ──
ENGINE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ENGINE_DIR / "assets"

logger = logging.getLogger("dashboard-engine")

# ── Chart.js 配色 ──
CHART_COLORS = [
    "#2563eb", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#6b7280", "#ec4899", "#14b8a6",
]


# ═══════════════════════════════════════════════════
# 1. Data Validator
# ═══════════════════════════════════════════════════

def validate_data(data: dict) -> list[str]:
    """驗證 JSON 資料，回傳錯誤清單（空 = 通過）"""
    errors = []
    if not data:
        errors.append("資料為空")
    if not isinstance(data, dict):
        errors.append("資料必須是 JSON 物件（dict）")
    return errors


def detect_data_type(data: dict) -> str:
    """偵測資料類型：revenue / slots / fish / general"""
    title = str(data.get("title", "")).lower()
    source = str(data.get("source", "")).lower()
    combined = title + " " + source
    if any(kw in combined for kw in ["revenue", "營收", "arpu", "ggr"]):
        return "revenue"
    if any(kw in combined for kw in ["slot", "老虎機", "spin"]):
        return "slots"
    if any(kw in combined for kw in ["fish", "魚機", "shark", "捕魚"]):
        return "fish"
    return "general"


# ═══════════════════════════════════════════════════
# 2. DSL Generator（AI 層）
# ═══════════════════════════════════════════════════

def build_data_summary(data: dict) -> str:
    """產生資料摘要，供 LLM 理解資料結構（不送完整資料）"""
    summary = {}
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict):
                summary[key] = {
                    "type": "array",
                    "length": len(value),
                    "columns": list(value[0].keys()),
                    "first_row": value[0],
                }
            else:
                summary[key] = {"type": "array", "length": len(value), "sample": value[:3]}
        elif isinstance(value, dict):
            sub = {}
            for sk, sv in value.items():
                if isinstance(sv, list) and len(sv) > 0 and isinstance(sv[0], dict):
                    sub[sk] = {"type": "array", "length": len(sv), "columns": list(sv[0].keys())}
                else:
                    sub[sk] = {"type": type(sv).__name__}
            summary[key] = {"type": "object", "children": sub}
        else:
            summary[key] = {"type": type(value).__name__, "value": value}
    return json.dumps(summary, ensure_ascii=False, indent=2)


def list_available_sources(data: dict, prefix: str = "") -> list[str]:
    """列出所有可用的 source 路徑（含 dot notation）"""
    sources = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, list):
            sources.append(path)
        elif isinstance(value, dict):
            sources.extend(list_available_sources(value, path))
    return sources


def generate_dsl_with_ai(data: dict, title: str = None) -> dict:
    """呼叫 Gemini API 產生 Dashboard DSL"""
    from google import genai

    prompt_path = ASSETS_DIR / "dsl_prompt.txt"
    prompt_template = prompt_path.read_text(encoding="utf-8")

    data_summary = build_data_summary(data)
    available_sources = "\n".join(f"- {s}" for s in list_available_sources(data))

    prompt = (
        prompt_template
        .replace("{data_summary}", data_summary)
        .replace("{available_sources}", available_sources)
    )

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    logger.info(f"呼叫 Gemini API 產生 DSL（model={model}）")
    response = client.models.generate_content(model=model, contents=prompt)

    if not response.text:
        raise ValueError("Gemini API 回應為空")

    text = response.text.strip()
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()

    dsl = json.loads(text)
    if title and not dsl.get("title"):
        dsl["title"] = title

    return dsl


def _detect_array_shape(arr: list[dict]) -> str:
    """偵測陣列的資料形狀，回傳建議的 widget type"""
    if not arr or not isinstance(arr[0], dict):
        return "table"
    cols = set(arr[0].keys())
    # KPI 模式：{label/title, value} 且無日期欄位
    if cols & {"label", "title"} and "value" in cols and len(cols) <= 5:
        return "kpi_group"
    # 時間序列：有 date/time/month/day 欄位
    date_fields = cols & {"date", "time", "month", "day", "period", "week"}
    if date_fields:
        return "line_chart"
    # 有類別 + 數值 → bar_chart
    return "bar_chart"


def _find_fields(arr: list[dict], role: str) -> str | list[str] | None:
    """從陣列第一筆資料自動偵測欄位名稱"""
    if not arr or not isinstance(arr[0], dict):
        return None
    row = arr[0]
    cols = list(row.keys())

    # 常見的類別/ID 欄位名稱（即使值是數值也不當 metric）
    category_hints = {"id", "level", "vip_level", "rank", "tier", "grade", "code", "type", "status"}

    if role == "x_date":
        for c in cols:
            if c in ("date", "time", "month", "day", "period", "week"):
                return c
        return cols[0]
    elif role == "x_category":
        # 第一個非數值欄位，或名稱像類別的欄位
        for c in cols:
            if not isinstance(row[c], (int, float)) or c.lower() in category_hints:
                return c
        return cols[0]
    elif role == "metrics":
        x_cat = _find_fields(arr, "x_category")
        return [c for c in cols if isinstance(row[c], (int, float)) and c != x_cat][:3]
    elif role == "dimension":
        for c in cols:
            if not isinstance(row[c], (int, float)) or c.lower() in category_hints:
                return c
        return cols[0]
    elif role == "metric":
        dim = _find_fields(arr, "dimension")
        for c in cols:
            if isinstance(row[c], (int, float)) and c != dim:
                return c
        return cols[-1]
    return None


def build_fallback_dsl(data: dict, title: str = None) -> dict:
    """Fallback DSL — LLM 失敗時，智慧偵測資料形狀產生合適的 widget"""
    widgets = []
    sources = list_available_sources(data)

    for source_path in sources:
        arr = resolve_source(data, source_path)
        if not isinstance(arr, list) or len(arr) == 0 or not isinstance(arr[0], dict):
            continue

        shape = _detect_array_shape(arr)
        safe_id = source_path.replace(".", "_")

        if shape == "kpi_group":
            widgets.append({
                "id": f"kpi_{safe_id}",
                "type": "kpi_group",
                "source": source_path,
                "title": source_path,
            })
        elif shape == "line_chart":
            x = _find_fields(arr, "x_date")
            metrics = _find_fields(arr, "metrics")
            if x and metrics:
                widgets.append({
                    "id": f"line_{safe_id}",
                    "type": "line_chart",
                    "source": source_path,
                    "x": x,
                    "metrics": metrics,
                    "title": source_path,
                })
        elif shape == "bar_chart":
            x = _find_fields(arr, "x_category")
            metrics = _find_fields(arr, "metrics")
            if x and metrics:
                widgets.append({
                    "id": f"bar_{safe_id}",
                    "type": "bar_chart",
                    "source": source_path,
                    "x": x,
                    "metrics": metrics,
                    "title": source_path,
                })
        else:
            widgets.append({
                "id": f"table_{safe_id}",
                "type": "table",
                "source": source_path,
                "title": source_path,
            })

    return {
        "title": title or "Data Dashboard",
        "theme": "light",
        "layout": "grid",
        "widgets": widgets[:8],
    }


# ═══════════════════════════════════════════════════
# 3. DSL Validator
# ═══════════════════════════════════════════════════

VALID_TYPES = {"kpi_group", "line_chart", "bar_chart", "pie_chart", "table"}

REQUIRED_FIELDS = {
    "kpi_group": ["source"],
    "line_chart": ["source", "x", "metrics"],
    "bar_chart": ["source", "x", "metrics"],
    "pie_chart": ["source", "dimension", "metric"],
    "table": ["source"],
}


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


def validate_dsl(dsl: dict, data: dict) -> list[str]:
    """驗證 DSL 結構，回傳錯誤清單"""
    errors = []

    if not dsl.get("widgets"):
        errors.append("DSL 缺少 widgets 陣列")
        return errors

    for i, w in enumerate(dsl["widgets"]):
        wid = w.get("id", f"widget_{i}")

        if "type" not in w:
            errors.append(f"[{wid}] 缺少 type 欄位")
            continue

        wtype = w["type"]
        if wtype not in VALID_TYPES:
            errors.append(f"[{wid}] 不支援的 type: {wtype}")
            continue

        for field in REQUIRED_FIELDS.get(wtype, []):
            if field not in w:
                errors.append(f"[{wid}] type={wtype} 缺少必要欄位: {field}")

        if "source" in w:
            source_data = resolve_source(data, w["source"])
            if source_data is None:
                errors.append(f"[{wid}] source 路徑不存在: {w['source']}")

    return errors


# ═══════════════════════════════════════════════════
# 4. Component Renderer（純程式碼，不用 LLM）
# ═══════════════════════════════════════════════════

def _escape_js(s: str) -> str:
    """跳脫 JS 字串中的特殊字元"""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")


def render_kpi_group(widget: dict, data: dict) -> tuple[str, str]:
    """渲染 KPI 卡片群組，回傳 (html, script)"""
    source = resolve_source(data, widget["source"])
    if not source or not isinstance(source, list):
        return "", ""

    cols = widget.get("columns", 4)
    cards_html = []
    for kpi in source:
        title = kpi.get("title", kpi.get("label", ""))
        raw_value = kpi.get("value", "")
        if isinstance(raw_value, (int, float)):
            if raw_value >= 1_000_000:
                value = f"${raw_value/1_000_000:,.2f}M"
            elif raw_value >= 1_000:
                value = f"{raw_value:,.0f}"
            else:
                value = f"{raw_value:,.2f}"
        else:
            value = str(raw_value)
        trend = kpi.get("trend", "")
        color = kpi.get("color", "blue")

        trend_class = "trend-up" if trend.startswith("+") else "trend-down" if trend.startswith("-") else "text-slate-400"
        trend_icon = "↑" if trend.startswith("+") else "↓" if trend.startswith("-") else ""

        color_map = {
            "blue": "#2563eb", "green": "#10b981", "yellow": "#f59e0b",
            "red": "#ef4444", "purple": "#8b5cf6",
        }
        accent = color_map.get(color, "#2563eb")

        cards_html.append(f'''
    <div class="glass-card p-5 fade-in">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</span>
        <span class="w-2 h-2 rounded-full" style="background:{accent}"></span>
      </div>
      <div class="text-2xl font-bold text-slate-800">{value}</div>
      <div class="{trend_class} text-sm font-medium mt-1">{trend_icon} {trend}</div>
    </div>''')

    html = f'''
  <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-{cols} gap-4 mb-8">
    {"".join(cards_html)}
  </section>'''
    return html, ""


def render_line_chart(widget: dict, data: dict) -> tuple[str, str]:
    """渲染折線圖，回傳 (html, script)"""
    source = resolve_source(data, widget["source"])
    if not source or not isinstance(source, list):
        return "", ""

    canvas_id = widget.get("id", "line_chart")
    title = widget.get("title", "")
    x_field = widget.get("x", "date")
    metrics = widget.get("metrics", [])

    labels = [str(row.get(x_field, "")) for row in source]
    datasets = []
    for i, metric in enumerate(metrics):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        values = [row.get(metric, 0) for row in source]
        datasets.append({
            "label": metric,
            "data": values,
            "borderColor": color,
            "backgroundColor": color + "20",
            "tension": 0.3,
            "fill": True,
        })

    html = f'''
  <div class="glass-card p-6 mb-6 fade-in">
    <h3 class="text-lg font-semibold text-slate-700 mb-4">{title}</h3>
    <canvas id="{canvas_id}" height="100"></canvas>
  </div>'''

    script = f'''
  new Chart(document.getElementById('{canvas_id}'), {{
    type: 'line',
    data: {{
      labels: {json.dumps(labels, ensure_ascii=False)},
      datasets: {json.dumps(datasets, ensure_ascii=False)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'bottom' }} }},
      scales: {{ y: {{ beginAtZero: false }} }}
    }}
  }});'''
    return html, script


def render_bar_chart(widget: dict, data: dict) -> tuple[str, str]:
    """渲染長條圖"""
    source = resolve_source(data, widget["source"])
    if not source or not isinstance(source, list):
        return "", ""

    canvas_id = widget.get("id", "bar_chart")
    title = widget.get("title", "")
    x_field = widget.get("x", "name")
    metrics = widget.get("metrics", [])

    labels = [str(row.get(x_field, "")) for row in source]
    datasets = []
    for i, metric in enumerate(metrics):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        values = [row.get(metric, 0) for row in source]
        datasets.append({
            "label": metric,
            "data": values,
            "backgroundColor": color + "CC",
            "borderColor": color,
            "borderWidth": 1,
        })

    html = f'''
  <div class="glass-card p-6 mb-6 fade-in">
    <h3 class="text-lg font-semibold text-slate-700 mb-4">{title}</h3>
    <canvas id="{canvas_id}" height="100"></canvas>
  </div>'''

    script = f'''
  new Chart(document.getElementById('{canvas_id}'), {{
    type: 'bar',
    data: {{
      labels: {json.dumps(labels, ensure_ascii=False)},
      datasets: {json.dumps(datasets, ensure_ascii=False)}
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'bottom' }} }},
      scales: {{ y: {{ beginAtZero: true }} }}
    }}
  }});'''
    return html, script


def render_pie_chart(widget: dict, data: dict) -> tuple[str, str]:
    """渲染圓餅圖（Doughnut）"""
    source = resolve_source(data, widget["source"])
    if not source or not isinstance(source, list):
        return "", ""

    canvas_id = widget.get("id", "pie_chart")
    title = widget.get("title", "")
    dim_field = widget.get("dimension", "name")
    metric_field = widget.get("metric", "value")

    labels = [str(row.get(dim_field, "")) for row in source]
    values = [row.get(metric_field, 0) for row in source]
    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(labels))]

    html = f'''
  <div class="glass-card p-6 mb-6 fade-in">
    <h3 class="text-lg font-semibold text-slate-700 mb-4">{title}</h3>
    <div class="flex justify-center"><canvas id="{canvas_id}" height="120" style="max-width:400px"></canvas></div>
  </div>'''

    script = f'''
  new Chart(document.getElementById('{canvas_id}'), {{
    type: 'doughnut',
    data: {{
      labels: {json.dumps(labels, ensure_ascii=False)},
      datasets: [{{
        data: {json.dumps(values)},
        backgroundColor: {json.dumps(colors)},
        borderWidth: 2,
        borderColor: '#fff'
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ position: 'bottom' }} }}
    }}
  }});'''
    return html, script


def render_table(widget: dict, data: dict) -> tuple[str, str]:
    """渲染數據表格"""
    source = resolve_source(data, widget["source"])
    if not source or not isinstance(source, list) or len(source) == 0:
        return "", ""

    title = widget.get("title", "")
    columns = list(source[0].keys())

    th_html = "".join(
        f'<th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{col}</th>'
        for col in columns
    )

    rows_html = []
    for i, row in enumerate(source):
        bg = "bg-slate-50/50" if i % 2 == 0 else ""
        cells = "".join(
            f'<td class="px-4 py-3 text-sm text-slate-700">{row.get(col, "")}</td>'
            for col in columns
        )
        rows_html.append(f'<tr class="{bg}">{cells}</tr>')

    html = f'''
  <div class="glass-card p-6 mb-6 fade-in">
    <h3 class="text-lg font-semibold text-slate-700 mb-4">{title}</h3>
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="border-b border-slate-200"><tr>{th_html}</tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
      </table>
    </div>
  </div>'''
    return html, ""


# Component Registry
COMPONENT_REGISTRY = {
    "kpi_group": render_kpi_group,
    "line_chart": render_line_chart,
    "bar_chart": render_bar_chart,
    "pie_chart": render_pie_chart,
    "table": render_table,
}


# ═══════════════════════════════════════════════════
# 5. Layout Planner + HTML Assembler
# ═══════════════════════════════════════════════════

def render_all_widgets(dsl: dict, data: dict) -> tuple[str, str]:
    """渲染所有 widget，回傳 (widgets_html, chart_scripts)"""
    type_order = {"kpi_group": 0, "line_chart": 1, "bar_chart": 1, "pie_chart": 1, "table": 2}
    widgets = sorted(dsl.get("widgets", []), key=lambda w: type_order.get(w.get("type", ""), 9))

    all_html = []
    all_scripts = []
    chart_widgets = []

    for w in widgets:
        wtype = w.get("type", "")
        renderer = COMPONENT_REGISTRY.get(wtype)
        if not renderer:
            logger.warning(f"跳過不支援的 widget type: {wtype}")
            continue

        html, script = renderer(w, data)
        if not html:
            continue

        if wtype in ("line_chart", "bar_chart", "pie_chart"):
            chart_widgets.append((html, script))
        else:
            if chart_widgets:
                all_html.append(_wrap_chart_grid(chart_widgets))
                all_scripts.extend(s for _, s in chart_widgets if s)
                chart_widgets = []
            all_html.append(html)
            if script:
                all_scripts.append(script)

    if chart_widgets:
        all_html.append(_wrap_chart_grid(chart_widgets))
        all_scripts.extend(s for _, s in chart_widgets if s)

    return "\n".join(all_html), "\n".join(all_scripts)


def _wrap_chart_grid(chart_widgets: list) -> str:
    """將 chart widget 包在 2 欄 grid 中"""
    inner = "".join(h for h, _ in chart_widgets)
    return f'\n  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">{inner}\n  </div>'


def assemble_html(dsl: dict, data: dict) -> str:
    """組裝最終 HTML（使用 re.sub + counter callback 避免無限迴圈）"""
    template_path = ASSETS_DIR / "base_template.html"
    template = template_path.read_text(encoding="utf-8")

    title = dsl.get("title", "Data Dashboard")
    data_type = detect_data_type(data)
    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    subtitle = f"資料日期：{date_str} | 類型：{data_type}"

    widgets_html, chart_scripts = render_all_widgets(dsl, data)
    data_json = json.dumps(data, ensure_ascii=False, indent=2)

    html = (
        template
        .replace("{{TITLE}}", title)
        .replace("{{SUBTITLE}}", subtitle)
        .replace("{{WIDGETS}}", widgets_html)
        .replace("{{DATA_JSON}}", data_json)
        .replace("{{CHART_SCRIPTS}}", chart_scripts)
    )

    # 加入 fade-in 動畫延遲（使用 re.sub + counter callback，不可用 while loop）
    _fade_counter = [0]
    def _add_delay(m):
        delay = _fade_counter[0] * 0.1
        _fade_counter[0] += 1
        return f'{m.group(0)} style="animation-delay:{delay:.1f}s"'

    html = re.sub(r'class="glass-card[^"]*fade-in"', _add_delay, html)

    return html


# ═══════════════════════════════════════════════════
# 6. 主流程
# ═══════════════════════════════════════════════════

def generate_dashboard(
    data: dict,
    mode: str = "auto",
    dsl: dict = None,
    title: str = None,
    theme: str = "light",
    output_dir: Path = None,
) -> dict:
    """
    主流程：JSON → DSL → Renderer → HTML

    Args:
        data: JSON 資料
        mode: "auto"（AI 產 DSL）或 "dsl"（使用者提供）
        dsl: 使用者自訂 DSL（mode=dsl 時必要）
        title: 儀表板標題
        theme: "light" 或 "dark"
        output_dir: 輸出目錄（預設 data/dashboard/）

    Returns:
        {"html_path": str, "dsl": dict, "metadata": dict} 或 {"error": str}
    """
    # 1. Data Validation
    errors = validate_data(data)
    if errors:
        return {"error": f"資料驗證失敗：{'; '.join(errors)}"}

    data_type = detect_data_type(data)
    if not title:
        title = data.get("title", {
            "revenue": "營收分析儀表板",
            "slots": "老虎機分析儀表板",
            "fish": "魚機分析儀表板",
            "general": "數據儀表板",
        }.get(data_type, "數據儀表板"))

    # 2. DSL Generation
    if mode == "dsl" and dsl:
        final_dsl = dsl
    else:
        try:
            final_dsl = generate_dsl_with_ai(data, title)
        except Exception as e:
            logger.warning(f"AI DSL 產生失敗：{e}，嘗試重試...")
            try:
                final_dsl = generate_dsl_with_ai(data, title)
            except Exception as e2:
                logger.warning(f"重試仍失敗：{e2}，使用 fallback DSL")
                final_dsl = build_fallback_dsl(data, title)

    final_dsl["theme"] = theme

    # 3. DSL Validation（失敗時自動 fallback）
    dsl_errors = validate_dsl(final_dsl, data)
    if dsl_errors:
        valid_widgets = []
        for w in final_dsl.get("widgets", []):
            w_errors = validate_dsl({"widgets": [w]}, data)
            if not w_errors:
                valid_widgets.append(w)
        if not valid_widgets:
            logger.warning(f"AI DSL 全部驗證失敗：{'; '.join(dsl_errors)}，使用 fallback DSL")
            final_dsl = build_fallback_dsl(data, title)
        else:
            logger.warning(f"移除 {len(final_dsl['widgets']) - len(valid_widgets)} 個有問題的 widget")
            final_dsl["widgets"] = valid_widgets

    # 4. Render HTML
    html = assemble_html(final_dsl, data)

    # 5. Save
    if output_dir is None:
        cwd = Path.cwd()
        output_dir = cwd / "data" / "dashboard"

    type_dir = output_dir / data_type
    type_dir.mkdir(parents=True, exist_ok=True)

    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    ts = datetime.now().strftime("%H%M%S")
    filename = f"{date_str}_{ts}.html"
    output_path = type_dir / filename

    output_path.write_text(html, encoding="utf-8")
    logger.info(f"儀表板已存檔：{output_path}")

    # 6. Metadata
    widget_types = [w.get("type") for w in final_dsl.get("widgets", [])]
    metadata = {
        "widgets": len(widget_types),
        "charts": sum(1 for t in widget_types if t in ("line_chart", "bar_chart", "pie_chart")),
        "tables": sum(1 for t in widget_types if t == "table"),
        "kpi_cards": sum(1 for t in widget_types if t == "kpi_group"),
        "data_type": data_type,
        "theme": theme,
    }

    return {
        "html_path": str(output_path),
        "dsl": final_dsl,
        "metadata": metadata,
    }
