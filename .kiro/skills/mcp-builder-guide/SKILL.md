---
name: mcp-builder-guide
description: "引導建立符合 Model Context Protocol（MCP）規範的 Server，涵蓋 Python SDK 快速上手、Tool/Resource/Prompt 定義、參數驗證與常見模式。當使用者提到 MCP、Model Context Protocol、MCP Server、MCP 開發、建立 MCP、MCP Tool、MCP Resource、mcp-builder、MCP Python SDK、Tool Gateway、MCP 整合時，請務必使用此技能。"
---

# MCP Server 建立指引（MCP Builder Guide）

MCP（Model Context Protocol）讓 AI 助手能安全地存取外部工具和資料。
這份指引幫你從零建立一個 MCP Server，讓 AI 能呼叫你的工具。

## 使用時機

- 需要建立新的 MCP Server
- 需要為 MCP Server 新增 Tool、Resource 或 Prompt
- 需要了解 MCP 協議的核心概念
- 需要將既有 API 包裝成 MCP Server
- 需要整合 MCP Server 到 ArkAgent OS 的 Tool Gateway

## MCP 核心概念

MCP Server 提供三種能力給 AI 助手：

| 能力 | 說明 | 類比 |
|------|------|------|
| Tools | AI 可以呼叫的函式 | API 端點 |
| Resources | AI 可以讀取的資料 | 檔案或資料庫查詢結果 |
| Prompts | 預定義的提示範本 | 可重用的指令模板 |

### 通訊方式

```
AI 助手（Client）  ←── JSON-RPC over stdio ──→  MCP Server
```

MCP 使用 JSON-RPC 2.0 協議，透過 stdio（標準輸入/輸出）通訊。
你不需要處理 HTTP、WebSocket 或任何網路協議。

## 快速開始：Python MCP Server

### 安裝

```bash
pip install mcp
```

### 最小可用範例

```python
from mcp.server.fastmcp import FastMCP

# 建立 Server
mcp = FastMCP("my-server")

# 定義 Tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """兩數相加"""
    return a + b

# 定義 Resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """取得問候語"""
    return f"你好，{name}！"

# 啟動
if __name__ == "__main__":
    mcp.run()
```

### 執行與測試

```bash
# 直接執行（stdio 模式）
python my_server.py

# 用 MCP Inspector 測試（推薦）
npx @modelcontextprotocol/inspector python my_server.py
```

## Tool 定義詳解

Tool 是 MCP 最常用的能力。AI 助手會根據 Tool 的名稱和描述決定何時呼叫。

### 基本 Tool

```python
@mcp.tool()
def search_database(query: str, limit: int = 10) -> str:
    """搜尋資料庫

    Args:
        query: 搜尋關鍵字
        limit: 回傳筆數上限（預設 10）
    """
    results = db.search(query, limit=limit)
    return format_results(results)
```

### 帶型別驗證的 Tool

```python
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    query: str = Field(description="搜尋關鍵字")
    category: str = Field(default="all", description="分類篩選")
    limit: int = Field(default=10, ge=1, le=100, description="回傳筆數")

@mcp.tool()
def advanced_search(params: SearchParams) -> str:
    """進階搜尋，支援分類篩選"""
    # params 已經過 Pydantic 驗證
    results = db.search(params.query, category=params.category, limit=params.limit)
    return format_results(results)
```

### 非同步 Tool

```python
import httpx

@mcp.tool()
async def fetch_url(url: str) -> str:
    """抓取網頁內容"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text[:5000]  # 限制回傳長度
```

### Tool 命名原則

| 原則 | 好的命名 | 壞的命名 |
|------|---------|---------|
| 動詞開頭 | `search_users` | `users` |
| 具體描述 | `get_order_by_id` | `get_data` |
| 一致風格 | `create_*` / `update_*` / `delete_*` | 混用 `add` / `modify` / `remove` |

## Resource 定義

Resource 讓 AI 可以讀取結構化資料。

```python
@mcp.resource("config://app")
def get_app_config() -> str:
    """取得應用程式設定"""
    config = load_config()
    return json.dumps(config, indent=2, ensure_ascii=False)

@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """取得使用者個人資料"""
    user = db.find_user(user_id)
    return json.dumps(user, ensure_ascii=False)
```

## Prompt 定義

Prompt 提供可重用的提示範本。

```python
@mcp.prompt()
def code_review(code: str, language: str = "python") -> str:
    """程式碼審查提示"""
    return f"""請審查以下 {language} 程式碼：

```{language}
{code}
```

請檢查：
1. 潛在的 Bug
2. 效能問題
3. 安全漏洞
4. 程式碼風格
"""
```

## 常見 MCP Server 模式

### 資料庫查詢 Server

```python
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("db-query")

DB_PATH = "app.db"

@mcp.tool()
def query_sql(sql: str) -> str:
    """執行唯讀 SQL 查詢（僅支援 SELECT）

    Args:
        sql: SQL 查詢語句（僅允許 SELECT）
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "錯誤：僅允許 SELECT 查詢"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return json.dumps(rows, ensure_ascii=False, indent=2)

@mcp.resource("schema://tables")
def get_schema() -> str:
    """取得資料庫表結構"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table'"
    )
    schemas = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return "\n\n".join(schemas)
```

### API 代理 Server

```python
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("api-proxy")

API_BASE = "https://api.example.com"

@mcp.tool()
async def api_get(endpoint: str) -> str:
    """呼叫外部 API（GET）

    Args:
        endpoint: API 路徑（例如 /users、/orders/123）
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}{endpoint}")
        return response.text
```

## Kiro 配置

在 `.kiro/settings/mcp.json` 中註冊你的 MCP Server：

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["path/to/my_server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 安全注意事項

- SQL 查詢只允許 SELECT（防止資料修改）
- 限制回傳資料量（避免 token 爆炸）
- 敏感資訊用環境變數，不要 hard-code
- 驗證所有輸入參數（用 Pydantic）
- 記錄操作日誌（但不記錄 PII）

## 除錯技巧

```bash
# 用 MCP Inspector 互動式測試
npx @modelcontextprotocol/inspector python my_server.py

# 設定日誌等級
FASTMCP_LOG_LEVEL=DEBUG python my_server.py

# 檢查 JSON-RPC 通訊
python my_server.py 2>debug.log
```

## 完成檢查清單

- [ ] 每個 Tool 都有清楚的 docstring
- [ ] 參數有型別標註和描述
- [ ] 錯誤處理完善（不會讓 Server 崩潰）
- [ ] 回傳資料量有限制
- [ ] 敏感資訊不外洩
- [ ] MCP Inspector 測試通過
- [ ] Kiro mcp.json 配置正確

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/mcp-python-sdk.md | Python MCP SDK API 參考與進階用法 | 需要深入 SDK 功能時 |
| references/mcp-patterns.md | 常見 MCP Server 模式：檔案操作、排程、多 Tool 組合 | 需要更多實作範例時 |
