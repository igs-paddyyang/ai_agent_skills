# D3 圖表配方集

本文件提供更多 D3.js 圖表類型的完整程式碼範例。

## 散佈圖（Scatter Plot）

```javascript
const data = [
  { x: 10, y: 20, label: "A" },
  { x: 30, y: 45, label: "B" },
  { x: 50, y: 30, label: "C" },
  { x: 70, y: 60, label: "D" },
  { x: 90, y: 40, label: "E" },
];

const xScale = d3.scaleLinear()
  .domain([0, 100]).range([0, width]);
const yScale = d3.scaleLinear()
  .domain([0, 80]).range([height, 0]);

// 座標軸
svg.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(xScale));
svg.append("g").call(d3.axisLeft(yScale));

// 資料點
svg.selectAll("circle").data(data).join("circle")
  .attr("cx", d => xScale(d.x))
  .attr("cy", d => yScale(d.y))
  .attr("r", 6)
  .attr("fill", "steelblue")
  .attr("opacity", 0.7);

// 標籤
svg.selectAll("text.label").data(data).join("text")
  .attr("class", "label")
  .attr("x", d => xScale(d.x) + 10)
  .attr("y", d => yScale(d.y) + 4)
  .text(d => d.label)
  .style("font-size", "12px");
```

## 水平長條圖（Horizontal Bar Chart）

```javascript
const data = [
  { label: "JavaScript", value: 65 },
  { label: "Python", value: 58 },
  { label: "TypeScript", value: 42 },
  { label: "Rust", value: 28 },
  { label: "Go", value: 25 },
];

const y = d3.scaleBand()
  .domain(data.map(d => d.label))
  .range([0, height])
  .padding(0.2);

const x = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value)])
  .range([0, width]);

svg.selectAll("rect").data(data).join("rect")
  .attr("x", 0)
  .attr("y", d => y(d.label))
  .attr("width", d => x(d.value))
  .attr("height", y.bandwidth())
  .attr("fill", "steelblue");

// 數值標籤
svg.selectAll("text.value").data(data).join("text")
  .attr("class", "value")
  .attr("x", d => x(d.value) + 5)
  .attr("y", d => y(d.label) + y.bandwidth() / 2 + 4)
  .text(d => d.value)
  .style("font-size", "12px");
```

## 甜甜圈圖（Donut Chart）

```javascript
const data = [
  { label: "完成", value: 65 },
  { label: "進行中", value: 25 },
  { label: "待處理", value: 10 },
];

const radius = Math.min(width, height) / 2;
const color = d3.scaleOrdinal()
  .domain(data.map(d => d.label))
  .range(["#4caf50", "#ff9800", "#f44336"]);

const pie = d3.pie().value(d => d.value).sort(null);
const arc = d3.arc().innerRadius(radius * 0.5).outerRadius(radius * 0.9);
const labelArc = d3.arc().innerRadius(radius * 0.7).outerRadius(radius * 0.7);

const g = svg.append("g")
  .attr("transform", `translate(${width/2},${height/2})`);

g.selectAll("path").data(pie(data)).join("path")
  .attr("d", arc)
  .attr("fill", d => color(d.data.label))
  .attr("stroke", "white")
  .attr("stroke-width", 2);

// 標籤
g.selectAll("text").data(pie(data)).join("text")
  .attr("transform", d => `translate(${labelArc.centroid(d)})`)
  .attr("text-anchor", "middle")
  .text(d => `${d.data.label} ${d.data.value}%`)
  .style("font-size", "12px");

// 中心文字
g.append("text")
  .attr("text-anchor", "middle")
  .attr("dy", "-0.2em")
  .style("font-size", "24px")
  .style("font-weight", "bold")
  .text("65%");
g.append("text")
  .attr("text-anchor", "middle")
  .attr("dy", "1.2em")
  .style("font-size", "14px")
  .style("fill", "#666")
  .text("完成率");
```

## 堆疊長條圖（Stacked Bar Chart）

```javascript
const data = [
  { month: "1月", feat: 5, fix: 3, docs: 2 },
  { month: "2月", feat: 8, fix: 2, docs: 4 },
  { month: "3月", feat: 3, fix: 6, docs: 1 },
];

const keys = ["feat", "fix", "docs"];
const color = d3.scaleOrdinal()
  .domain(keys)
  .range(["#4caf50", "#f44336", "#2196f3"]);

const stack = d3.stack().keys(keys);
const series = stack(data);

const x = d3.scaleBand()
  .domain(data.map(d => d.month))
  .range([0, width]).padding(0.2);

const y = d3.scaleLinear()
  .domain([0, d3.max(series, s => d3.max(s, d => d[1]))])
  .range([height, 0]);

svg.selectAll("g.series").data(series).join("g")
  .attr("class", "series")
  .attr("fill", d => color(d.key))
  .selectAll("rect").data(d => d).join("rect")
    .attr("x", d => x(d.data.month))
    .attr("y", d => y(d[1]))
    .attr("height", d => y(d[0]) - y(d[1]))
    .attr("width", x.bandwidth());
```

## 樹狀圖（Tree Diagram）

```javascript
const treeData = {
  name: "Root",
  children: [
    { name: "A", children: [{ name: "A1" }, { name: "A2" }] },
    { name: "B", children: [{ name: "B1" }, { name: "B2" }, { name: "B3" }] },
    { name: "C" },
  ],
};

const root = d3.hierarchy(treeData);
const treeLayout = d3.tree().size([width, height - 100]);
treeLayout(root);

// 連線
svg.selectAll("path.link").data(root.links()).join("path")
  .attr("class", "link")
  .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y + 40))
  .attr("fill", "none")
  .attr("stroke", "#ccc")
  .attr("stroke-width", 1.5);

// 節點
const nodes = svg.selectAll("g.node").data(root.descendants()).join("g")
  .attr("class", "node")
  .attr("transform", d => `translate(${d.x},${d.y + 40})`);

nodes.append("circle").attr("r", 6).attr("fill", "steelblue");
nodes.append("text")
  .attr("dy", -12).attr("text-anchor", "middle")
  .text(d => d.data.name).style("font-size", "12px");
```
