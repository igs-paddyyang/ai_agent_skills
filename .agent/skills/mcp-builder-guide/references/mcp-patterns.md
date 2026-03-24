# 常見 MCP Server 模式

本文件提供常見 MCP Server 的實作模式與完整範例。

## 檔案操作 Server

```python
import os
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file-ops")

ALLOWED_DIR = Path("./workspace")

def safe_path(path: str) -> Path:
    """確保路徑在允許的目錄內"""
    resolved = (ALLOWED_DIR / path).resolve()
    if not str(resolved).startswith(str(ALLOWED_DIR.resolve())):
        raise ValueError("路徑超出允許範圍")
    return resolved

@mcp.tool()
def list_files(directory: str = ".") -> str:
    """列出目錄中的檔案

    Args:
        directory: 相對於 workspace 的目錄路徑
    """
    target = safe_path(directory)
    if not target.is_dir():
        return f"錯誤：{directory} 不是目錄"

    files = []
    for item in target.iterdir():
        files.append({
            "name": item.name,
            "type": "dir" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else None,
        })
    return json.dumps(files, ensure_ascii=False, indent=2)

@mcp.tool()
def read_file(path: str) -> str:
    """讀取檔案內容

    Args:
        path: 相對於 workspace 的檔案路徑
    """
    target = safe_path(path)
    if not target.is_file():
        return f"錯誤：{path} 不存在或不是檔案"
    return target.read_text(encoding="utf-8")

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """寫入檔案內容

    Args:
        path: 相對於 workspace 的檔案路徑
        content: 要寫入的內容
    """
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已寫入 {path}（{len(content)} 字元）"
```

## 多 Tool 組合模式

當多個 Tool 需要共用狀態或資源時，用類別封裝。

```python
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("task-manager")

class TaskDB:
    """任務資料庫封裝"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

db = TaskDB("tasks.db")

@mcp.tool()
def create_task(title: str) -> str:
    """建立新任務"""
    conn = db._conn()
    cursor = conn.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return f"已建立任務 #{task_id}: {title}"

@mcp.tool()
def list_tasks(status: str = "all") -> str:
    """列出任務

    Args:
        status: 篩選狀態（all / pending / done）
    """
    conn = db._conn()
    if status == "all":
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks WHERE status = ?", (status,)).fetchall()
    conn.close()
    tasks = [dict(row) for row in rows]
    return json.dumps(tasks, ensure_ascii=False, indent=2, default=str)

@mcp.tool()
def complete_task(task_id: int) -> str:
    """完成任務

    Args:
        task_id: 任務 ID
    """
    conn = db._conn()
    conn.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return f"任務 #{task_id} 已完成"
```

## API 代理模式（帶快取）

```python
import httpx
import json
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("api-cache-proxy")

# 簡單的記憶體快取
_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL = 300  # 5 分鐘

async def cached_get(url: str) -> str:
    """帶快取的 HTTP GET"""
    now = time.time()
    if url in _cache:
        cached_time, cached_data = _cache[url]
        if now - cached_time < CACHE_TTL:
            return cached_data

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        data = response.text
        _cache[url] = (now, data)
        return data

@mcp.tool()
async def fetch_api(endpoint: str) -> str:
    """呼叫 API 並快取結果（5 分鐘）

    Args:
        endpoint: 完整的 API URL
    """
    try:
        return await cached_get(endpoint)
    except httpx.HTTPError as e:
        return f"API 呼叫失敗：{e}"
```

## 與 ArkAgent OS Tool Gateway 整合

MCP Server 可以作為 ArkAgent OS 的 Tool Gateway 擴展：

```
ArkAgent OS
├── Tool Gateway
│   ├── MCP Client（連接外部 MCP Server）
│   ├── Built-in Tools（內建工具）
│   └── Tool Registry（工具註冊表）
└── Skill Runtime
    └── 透過 Tool Gateway 呼叫 MCP Tools
```

整合步驟：
1. 建立 MCP Server（本指引的內容）
2. 在 ArkAgent OS 的 `mcp.json` 中註冊
3. Tool Gateway 自動發現並載入 MCP Tools
4. Skill 透過 Tool Gateway 呼叫

## Server 部署清單

- [ ] 所有 Tool 都有 docstring 和參數描述
- [ ] 錯誤處理完善，不會讓 Server 崩潰
- [ ] 敏感資訊使用環境變數
- [ ] 回傳資料量有合理限制
- [ ] 路徑操作有安全檢查（防止路徑穿越）
- [ ] SQL 操作使用參數化查詢
- [ ] MCP Inspector 測試通過
- [ ] mcp.json 配置正確
