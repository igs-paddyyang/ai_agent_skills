# D3 資料綁定核心概念

本文件深入說明 D3.js 的資料綁定機制與動畫轉場。

## Enter / Update / Exit 模式

D3 的資料綁定將資料陣列與 DOM 元素配對：

```
資料: [A, B, C, D, E]
DOM:  [■, ■, ■]

Enter:  D, E（有資料但沒有 DOM → 建立新元素）
Update: A, B, C（資料和 DOM 都有 → 更新屬性）
Exit:   （沒有，因為資料比 DOM 多）
```

### 傳統寫法

```javascript
const selection = svg.selectAll("rect").data(data);

// Enter：新增元素
selection.enter()
  .append("rect")
  .attr("fill", "steelblue");

// Update：更新既有元素
selection
  .attr("width", d => xScale(d.value));

// Exit：移除多餘元素
selection.exit().remove();
```

### 現代寫法（推薦）

```javascript
// .join() 一次處理 enter + update + exit
svg.selectAll("rect")
  .data(data)
  .join("rect")
  .attr("x", (d, i) => i * 60)
  .attr("width", 50)
  .attr("height", d => yScale(d.value))
  .attr("fill", "steelblue");
```

### 自訂 join 行為

```javascript
svg.selectAll("rect")
  .data(data, d => d.id)  // key function
  .join(
    enter => enter.append("rect")
      .attr("fill", "green")        // 新元素是綠色
      .attr("opacity", 0)
      .call(enter => enter.transition()
        .attr("opacity", 1)),
    update => update
      .attr("fill", "steelblue")    // 更新元素是藍色
      .call(update => update.transition()
        .attr("width", d => xScale(d.value))),
    exit => exit
      .attr("fill", "red")          // 移除元素變紅
      .call(exit => exit.transition()
        .attr("opacity", 0)
        .remove())
  );
```

## Transition（動畫轉場）

### 基本轉場

```javascript
svg.selectAll("rect")
  .data(data)
  .join("rect")
  .attr("height", 0)              // 初始高度 0
  .attr("y", height)              // 從底部開始
  .transition()                    // 開始轉場
  .duration(800)                   // 800ms
  .delay((d, i) => i * 100)       // 每個元素延遲 100ms
  .ease(d3.easeCubicOut)           // 緩動函式
  .attr("height", d => height - yScale(d.value))
  .attr("y", d => yScale(d.value));
```

### 常用緩動函式

| 函式 | 效果 |
|------|------|
| `d3.easeLinear` | 等速 |
| `d3.easeCubicOut` | 先快後慢（推薦） |
| `d3.easeBounce` | 彈跳效果 |
| `d3.easeElastic` | 彈性效果 |
| `d3.easeBack` | 回彈效果 |

### 鏈式轉場

```javascript
svg.selectAll("circle")
  .transition()
  .duration(500)
  .attr("r", 10)           // 先放大
  .transition()
  .duration(500)
  .attr("fill", "red")     // 再變色
  .transition()
  .duration(500)
  .attr("r", 5);           // 最後縮小
```

## Key Function

Key function 決定資料如何與 DOM 元素配對：

```javascript
// 預設：按索引配對（資料順序改變時會出問題）
svg.selectAll("rect").data(data);

// 推薦：按 key 配對（資料順序改變時正確追蹤）
svg.selectAll("rect").data(data, d => d.id);
```

### 為什麼需要 Key Function

```javascript
// 資料從 [A, B, C] 變成 [B, C, D]
// 沒有 key：A→B, B→C, C→D（錯誤配對）
// 有 key：B→B, C→C, A exit, D enter（正確配對）
```

## 實用技巧

### 防止重複繪製

```javascript
// ❌ 每次呼叫都新增元素
function draw(data) {
  svg.selectAll("rect").data(data).enter().append("rect");
}

// ✅ 用 join 自動處理
function draw(data) {
  svg.selectAll("rect").data(data, d => d.id).join("rect")
    .attr("width", d => xScale(d.value));
}
```

### 格式化數字

```javascript
const format = d3.format(",.0f");    // 千分位，無小數
const percent = d3.format(".1%");    // 百分比，一位小數

// 座標軸格式化
svg.append("g").call(
  d3.axisLeft(yScale).tickFormat(d => `$${format(d)}`)
);
```

### 顏色方案

```javascript
// 內建色彩方案
d3.schemeCategory10    // 10 色
d3.schemeSet2          // 8 色（柔和）
d3.schemePaired        // 12 色（配對）

// 連續色彩
d3.interpolateBlues    // 藍色漸層
d3.interpolateViridis  // 科學視覺化常用
```
