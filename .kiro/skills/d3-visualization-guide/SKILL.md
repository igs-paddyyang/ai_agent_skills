---
name: d3-visualization-guide
description: "產出 D3.js 互動圖表與資料視覺化，涵蓋折線圖、長條圖、圓餅圖、散佈圖、樹狀圖等常用圖表類型，支援響應式設計與動畫。可與 gemini-canvas-dashboard 互補使用。當使用者提到 D3、D3.js、資料視覺化、data visualization、互動圖表、折線圖、長條圖、圓餅圖、散佈圖、樹狀圖、SVG 圖表、d3-visualization 時，請務必使用此技能。"
---

# D3.js 視覺化指引（D3 Visualization Guide）

D3.js 讓你用資料驅動 DOM，產出任何你想得到的圖表。
這份指引幫你快速產出常用的互動圖表，不用從零學 D3 的所有 API。

## 使用時機

- 需要產出互動式圖表（折線圖、長條圖、圓餅圖等）
- gemini-canvas-dashboard 的圖表類型不夠用時
- 需要自訂圖表樣式或動畫
- 需要處理大量資料的視覺化
- 需要響應式圖表設計

## 與 gemini-canvas-dashboard 的關係

| 面向 | gemini-canvas-dashboard | d3-visualization-guide |
|------|------------------------|----------------------|
| 產生方式 | Gemini API 自動產生 HTML | 手動/半自動產出 D3 程式碼 |
| 圖表類型 | KPI 卡片、基本圖表 | 任意自訂圖表 |
| 互動性 | 低 | 高（hover、zoom、drag） |
| 適用場景 | 快速產出儀表板 | 需要精細控制的圖表 |
| 學習成本 | 低 | 中 |

建議：先用 gemini-canvas-dashboard 快速產出，不夠用時再用 D3 補充。

## D3 核心概念

### 資料綁定（Data Binding）

D3 的核心是把資料綁定到 DOM 元素：

```javascript
const data = [10, 20, 30, 40, 50];

d3.select("svg")
  .selectAll("rect")
  .data(data)
  .join("rect")           // enter + update + exit 一次搞定
  .attr("x", (d, i) => i * 60)
  .attr("y", d => 200 - d * 3)
  .attr("width", 50)
  .attr("height", d => d * 3)
  .attr("fill", "steelblue");
```

### Scale（比例尺）

將資料值映射到視覺屬性：

```javascript
// 線性比例尺（數值 → 像素）
const xScale = d3.scaleLinear()
  .domain([0, 100])     // 資料範圍
  .range([0, 800]);     // 像素範圍

// 序數比例尺（類別 → 像素）
const colorScale = d3.scaleOrdinal()
  .domain(["A", "B", "C"])
  .range(["#e41a1c", "#377eb8", "#4daf4a"]);

// 時間比例尺
const timeScale = d3.scaleTime()
  .domain([new Date("2026-01-01"), new Date("2026-12-31")])
  .range([0, 800]);
```

### Axis（座標軸）

```javascript
const xAxis = d3.axisBottom(xScale);
const yAxis = d3.axisLeft(yScale);

svg.append("g")
  .attr("transform", `translate(0, ${height})`)
  .call(xAxis);

svg.append("g")
  .call(yAxis);
```

## 常用圖表範例

### 折線圖（Line Chart）

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .line { fill: none; stroke: steelblue; stroke-width: 2; }
    .dot { fill: steelblue; }
    .axis text { font-size: 12px; }
  </style>
</head>
<body>
<svg id="chart" width="800" height="400"></svg>
<script>
const data = [
  { date: "2026-01", value: 30 },
  { date: "2026-02", value: 45 },
  { date: "2026-03", value: 38 },
  { date: "2026-04", value: 52 },
  { date: "2026-05", value: 48 },
];

const margin = { top: 20, right: 30, bottom: 40, left: 50 };
const width = 800 - margin.left - margin.right;
const height = 400 - margin.top - margin.bottom;

const svg = d3.select("#chart")
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scalePoint()
  .domain(data.map(d => d.date))
  .range([0, width]);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value) * 1.1])
  .range([height, 0]);

// 座標軸
svg.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(x));
svg.append("g").call(d3.axisLeft(y));

// 折線
const line = d3.line().x(d => x(d.date)).y(d => y(d.value));
svg.append("path").datum(data).attr("class", "line").attr("d", line);

// 資料點
svg.selectAll(".dot").data(data).join("circle")
  .attr("class", "dot").attr("cx", d => x(d.date))
  .attr("cy", d => y(d.value)).attr("r", 4);
</script>
</body>
</html>
```

### 長條圖（Bar Chart）

```javascript
const data = [
  { label: "產品A", value: 30 },
  { label: "產品B", value: 45 },
  { label: "產品C", value: 22 },
  { label: "產品D", value: 58 },
];

const x = d3.scaleBand()
  .domain(data.map(d => d.label))
  .range([0, width])
  .padding(0.2);

const y = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value)])
  .range([height, 0]);

svg.selectAll("rect").data(data).join("rect")
  .attr("x", d => x(d.label))
  .attr("y", d => y(d.value))
  .attr("width", x.bandwidth())
  .attr("height", d => height - y(d.value))
  .attr("fill", "steelblue");
```

### 圓餅圖（Pie Chart）

```javascript
const data = [
  { label: "類別A", value: 30 },
  { label: "類別B", value: 45 },
  { label: "類別C", value: 25 },
];

const radius = Math.min(width, height) / 2;
const color = d3.scaleOrdinal(d3.schemeCategory10);

const pie = d3.pie().value(d => d.value);
const arc = d3.arc().innerRadius(0).outerRadius(radius);

const g = svg.append("g")
  .attr("transform", `translate(${width/2},${height/2})`);

g.selectAll("path").data(pie(data)).join("path")
  .attr("d", arc)
  .attr("fill", (d, i) => color(i))
  .attr("stroke", "white");
```

## 互動功能

### Tooltip

```javascript
const tooltip = d3.select("body").append("div")
  .style("position", "absolute")
  .style("background", "rgba(0,0,0,0.8)")
  .style("color", "white")
  .style("padding", "8px")
  .style("border-radius", "4px")
  .style("display", "none");

svg.selectAll("rect")
  .on("mouseover", (event, d) => {
    tooltip.style("display", "block")
      .html(`${d.label}: ${d.value}`)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 10) + "px");
  })
  .on("mouseout", () => tooltip.style("display", "none"));
```

### 響應式設計

```javascript
function resize() {
  const container = document.getElementById("chart-container");
  const newWidth = container.clientWidth;
  // 重新計算 scale 和重繪...
}
window.addEventListener("resize", resize);
```

## 完成檢查清單

- [ ] 圖表有標題和座標軸標籤
- [ ] 資料點有 tooltip 或標籤
- [ ] 顏色對比度足夠（無障礙）
- [ ] 響應式設計（或固定合理尺寸）
- [ ] 載入 D3 v7 CDN
- [ ] HTML 結構完整可直接開啟

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/d3-chart-recipes.md | 各圖表類型完整程式碼：散佈圖、樹狀圖、熱力圖 | 需要更多圖表類型時 |
| references/d3-bindng-guide.md | D3 資料綁定核心概念：enter/update/exit、transition | 需要深入理解 D3 機制時 |
