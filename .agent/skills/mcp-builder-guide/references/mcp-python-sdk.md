# MCP Python SDK 參考

本文件提供 MCP Python SDK 的進階用法與 API 參考。

## SDK 版本

- 套件名稱：`mcp`
- 安裝：`pip install mcp`
- 主要入口：`from mcp.server.fastmcp import FastMCP`

## FastMCP 類別

FastMCP 是高階 API，簡化 MCP Server 的建立。

### 初始化參數

```python
mcp = FastMCP(
    name="my-server",           # Server 名稱（必填）
)
```

### 裝飾器 API

```python
# Tool — AI 可呼叫的函式
@mcp.tool()
def my_tool(param: str) -> str:
    """Tool 描述"""
    return result

# Resource — AI 可讀取的資料
@mcp.resource("uri://path/{param}")
def my_resource(param: str) -> str:
    """Resource 描述"""
    return data

# Prompt — 可重用的提示範本
@mcp.prompt()
def my_prompt(param: str) -> str:
    """Prompt 描述"""
    return template
```

## 進階 Tool 定義

### 回傳多種內容類型

```python
from mcp.types import TextContent, ImageContent

@mcp.tool()
def analyze_image(image_path: str) -> list:
    """分析圖片並回傳文字描述"""
    # 回傳多個內容區塊
    return [
        TextContent(type="text", text="圖片分析結果：..."),
        ImageContent(type="image", data=base64_data, mimeType="image/png"),
    ]
```

### 錯誤處理

```python
@mcp.tool()
def safe_divide(a: float, b: float) -> str:
    """安全除法"""
    try:
        if b == 0:
            return "錯誤：除數不能為零"
        return str(a / b)
    except Exception as e:
        return f"計算錯誤：{e}"
```

Tool 不應該拋出未處理的例外。永遠回傳有意義的錯誤訊息。

### Context 物件

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def long_task(data: str, ctx: Context) -> str:
    """長時間執行的任務"""
    total = len(data)
    for i, chunk in enumerate(process_chunks(data)):
        await ctx.report_progress(i, total)
        # 處理 chunk...
    return "完成"
```

## 進階 Resource 定義

### 動態 Resource 列表

```python
@mcp.resource("files://{path}")
def read_file(path: str) -> str:
    """讀取檔案內容"""
    with open(path) as f:
        return f.read()
```

### Resource 與 MIME 類型

```python
@mcp.resource("data://report.json")
def get_report() -> str:
    """取得 JSON 報告"""
    report = generate_report()
    return json.dumps(report, ensure_ascii=False, indent=2)
```

## 生命週期管理

### 啟動與關閉

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(server):
    """Server 生命週期管理"""
    # 啟動時
    db = await connect_database()
    server.state["db"] = db
    try:
        yield
    finally:
        # 關閉時
        await db.close()

mcp = FastMCP("my-server", lifespan=lifespan)

@mcp.tool()
async def query(sql: str, ctx: Context) -> str:
    db = ctx.server.state["db"]
    return await db.execute(sql)
```

## 傳輸方式

### stdio（預設）

```python
# 最常用，適合本地開發
if __name__ == "__main__":
    mcp.run()  # 預設使用 stdio
```

### SSE（Server-Sent Events）

```python
# 適合遠端部署
if __name__ == "__main__":
    mcp.run(transport="sse")
```

## 測試

### 用 MCP Inspector

```bash
# 安裝並啟動 Inspector
npx @modelcontextprotocol/inspector python my_server.py
```

Inspector 提供互動式 UI，可以：
- 列出所有 Tools、Resources、Prompts
- 手動呼叫 Tool 並查看結果
- 檢查參數 schema

### 程式化測試

```python
import pytest
from mcp.server.fastmcp import FastMCP

@pytest.fixture
def server():
    mcp = FastMCP("test-server")

    @mcp.tool()
    def add(a: int, b: int) -> int:
        return a + b

    return mcp

@pytest.mark.asyncio
async def test_add_tool(server):
    result = await server.call_tool("add", {"a": 1, "b": 2})
    assert result[0].text == "3"
```
