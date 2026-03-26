"""Domain Controller 模板 — DomainController + MCPController + PythonController + SystemController"""

# ── config/mcp.json 範例 ──
MCP_CONFIG_JSON = '''{
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
            "disabled": false
        },
        "sqlite-server": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "data/brain.db"],
            "disabled": false
        },
        "bigquery-server": {
            "command": "uvx",
            "args": ["mcp-server-bigquery", "--project", "${BIGQUERY_PROJECT_ID}", "--key-file", "${GOOGLE_APPLICATION_CREDENTIALS}", "--location", "US"],
            "disabled": true
        },
        "mssql-server": {
            "command": "uvx",
            "args": ["--from", "mssql-mcp-server", "mssql_mcp_server"],
            "env": {
                "MSSQL_HOST": "${MSSQL_HOST}",
                "MSSQL_USER": "${MSSQL_USER}",
                "MSSQL_PASSWORD": "${MSSQL_PASSWORD}",
                "MSSQL_DATABASE": "${MSSQL_DATABASE}",
                "MSSQL_DRIVER": "${MSSQL_DRIVER}"
            },
            "disabled": true
        }
    }
}'''

# ── controller/__init__.py ──
CONTROLLER_INIT_PY = '''"""ArkAgent Domain Controller — 三種執行模式"""
from .domain_controller import DomainController
from .system_controller import SystemController
from .python_controller import PythonController
from .mcp_controller import MCPController

__all__ = ["DomainController", "SystemController", "PythonController", "MCPController"]
'''

# ── controller/domain_controller.py ──
DOMAIN_CONTROLLER_PY = '''"""Domain Controller — Action 統一路由器

Skill 回傳 Action 格式：
{
    "type": "action",
    "controller": "mcp|python|system",
    "action": "call_tool|run_script|scheduler.add|...",
    "params": { ... },
    "fallback_text": "操作完成的文字描述"
}
"""
import logging

logger = logging.getLogger(__name__)


class DomainController:
    """統一路由器：根據 action["controller"] 分派到對應子 Controller"""

    def __init__(self, project_root: str, registry=None):
        from .system_controller import SystemController
        from .python_controller import PythonController
        from .mcp_controller import MCPController
        from pathlib import Path

        self.project_root = Path(project_root)
        self.controllers = {
            "system": SystemController(project_root, registry),
            "python": PythonController(project_root),
            "mcp": MCPController(project_root),
        }
        logger.info(f"DomainController 初始化完成，已載入 {len(self.controllers)} 個子 Controller")

    async def execute(self, action: dict) -> dict:
        """執行 Action，路由到對應子 Controller

        Args:
            action: Action dict，必須包含 controller / action / params

        Returns:
            {"success": bool, "result": ..., "fallback_text": ...}
        """
        if not isinstance(action, dict):
            return {"success": False, "error": "Action 必須是 dict 格式"}

        if action.get("type") != "action":
            return {"success": False, "error": "Action type 必須為 'action'"}

        controller_name = action.get("controller")
        if not controller_name:
            return {"success": False, "error": "Action 缺少 controller 欄位"}

        controller = self.controllers.get(controller_name)
        if not controller:
            return {
                "success": False,
                "error": f"未知的 Controller: {controller_name}，可用: {list(self.controllers.keys())}",
            }

        action_name = action.get("action", "")
        params = action.get("params", {})
        fallback_text = action.get("fallback_text", "")

        logger.info(f"路由 Action: controller={controller_name}, action={action_name}")

        try:
            result = await controller.execute(action_name, params)
            result["fallback_text"] = fallback_text
            return result
        except Exception as e:
            logger.error(f"Controller '{controller_name}' 執行失敗: {e}")
            return {"success": False, "error": str(e), "fallback_text": fallback_text}

    def is_action(self, result) -> bool:
        """判斷 Skill 回傳結果是否為 Action 格式"""
        return (
            isinstance(result, dict)
            and result.get("type") == "action"
            and "controller" in result
            and "action" in result
        )
'''


# ── controller/system_controller.py ──
SYSTEM_CONTROLLER_PY = '''"""System Controller — ArkBot 內建系統操作

支援操作：
  scheduler.list / add / remove / toggle / trigger
  skill.list / enable / disable / reload / info
  admin.status / config / logs
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_START_TIME = time.time()


class SystemController:
    """操作 ArkBot 內建系統：排程、Skill 管理、系統管理"""

    def __init__(self, project_root: str, registry=None):
        self.project_root = Path(project_root)
        self.registry = registry
        self.schedules_path = self.project_root / "data" / "schedules.json"
        self.log_path = self.project_root / "data" / "scheduler.log"

        # action 路由表
        self._actions = {
            "scheduler.list": self._scheduler_list,
            "scheduler.add": self._scheduler_add,
            "scheduler.remove": self._scheduler_remove,
            "scheduler.toggle": self._scheduler_toggle,
            "scheduler.trigger": self._scheduler_trigger,
            "skill.list": self._skill_list,
            "skill.enable": self._skill_enable,
            "skill.disable": self._skill_disable,
            "skill.reload": self._skill_reload,
            "skill.info": self._skill_info,
            "admin.status": self._admin_status,
            "admin.config": self._admin_config,
            "admin.logs": self._admin_logs,
        }

    async def execute(self, action: str, params: dict) -> dict:
        """執行系統操作"""
        handler = self._actions.get(action)
        if not handler:
            return {
                "success": False,
                "error": f"未知的系統操作: {action}，可用: {list(self._actions.keys())}",
            }
        try:
            return await handler(params)
        except Exception as e:
            logger.error(f"SystemController '{action}' 失敗: {e}")
            return {"success": False, "error": str(e)}

    # ── 排程操作 ──

    def _load_schedules(self) -> dict:
        if not self.schedules_path.exists():
            return {"schedules": []}
        with open(self.schedules_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_schedules(self, data: dict):
        self.schedules_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.schedules_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def _scheduler_list(self, params: dict) -> dict:
        data = self._load_schedules()
        return {"success": True, "result": data.get("schedules", [])}

    async def _scheduler_add(self, params: dict) -> dict:
        required = ["id", "skill_id", "cron"]
        for key in required:
            if key not in params:
                return {"success": False, "error": f"缺少必要參數: {key}"}

        data = self._load_schedules()
        # 檢查 ID 重複
        if any(s["id"] == params["id"] for s in data["schedules"]):
            return {"success": False, "error": f"排程 ID 已存在: {params['id']}"}

        schedule = {
            "id": params["id"],
            "skill_id": params["skill_id"],
            "cron": params["cron"],
            "input": params.get("input", ""),
            "description": params.get("description", ""),
            "enabled": params.get("enabled", True),
            "created_at": datetime.now().isoformat(),
        }
        data["schedules"].append(schedule)
        self._save_schedules(data)
        return {"success": True, "result": f"排程 '{params['id']}' 已新增"}

    async def _scheduler_remove(self, params: dict) -> dict:
        schedule_id = params.get("schedule_id") or params.get("id")
        if not schedule_id:
            return {"success": False, "error": "缺少 schedule_id 參數"}

        data = self._load_schedules()
        original_len = len(data["schedules"])
        data["schedules"] = [s for s in data["schedules"] if s["id"] != schedule_id]

        if len(data["schedules"]) == original_len:
            return {"success": False, "error": f"排程 '{schedule_id}' 不存在"}

        self._save_schedules(data)
        return {"success": True, "result": f"排程 '{schedule_id}' 已移除"}

    async def _scheduler_toggle(self, params: dict) -> dict:
        schedule_id = params.get("schedule_id") or params.get("id")
        if not schedule_id:
            return {"success": False, "error": "缺少 schedule_id 參數"}

        data = self._load_schedules()
        for s in data["schedules"]:
            if s["id"] == schedule_id:
                enabled = params.get("enabled")
                if enabled is None:
                    s["enabled"] = not s.get("enabled", True)
                else:
                    s["enabled"] = bool(enabled)
                self._save_schedules(data)
                state = "啟用" if s["enabled"] else "停用"
                return {"success": True, "result": f"排程 '{schedule_id}' 已{state}"}

        return {"success": False, "error": f"排程 '{schedule_id}' 不存在"}

    async def _scheduler_trigger(self, params: dict) -> dict:
        schedule_id = params.get("schedule_id") or params.get("id")
        if not schedule_id:
            return {"success": False, "error": "缺少 schedule_id 參數"}

        data = self._load_schedules()
        schedule = next((s for s in data["schedules"] if s["id"] == schedule_id), None)
        if not schedule:
            return {"success": False, "error": f"排程 '{schedule_id}' 不存在"}

        # 觸發排程（透過 Executor，需外部注入）
        return {
            "success": True,
            "result": f"排程 '{schedule_id}' 已觸發（skill={schedule['skill_id']}）",
            "schedule": schedule,
        }

    # ── Skill 管理 ──

    async def _skill_list(self, params: dict) -> dict:
        if not self.registry:
            return {"success": False, "error": "SkillRegistry 未初始化"}
        skills = [
            {"skill_id": k, "description": v.get("description", ""), "enabled": v.get("enabled", True)}
            for k, v in self.registry.skills.items()
        ]
        return {"success": True, "result": skills}

    async def _skill_enable(self, params: dict) -> dict:
        skill_id = params.get("skill_id")
        if not skill_id:
            return {"success": False, "error": "缺少 skill_id 參數"}
        if not self.registry or skill_id not in self.registry.skills:
            return {"success": False, "error": f"Skill '{skill_id}' 不存在"}
        self.registry.skills[skill_id]["enabled"] = True
        return {"success": True, "result": f"Skill '{skill_id}' 已啟用"}

    async def _skill_disable(self, params: dict) -> dict:
        skill_id = params.get("skill_id")
        if not skill_id:
            return {"success": False, "error": "缺少 skill_id 參數"}
        if not self.registry or skill_id not in self.registry.skills:
            return {"success": False, "error": f"Skill '{skill_id}' 不存在"}
        self.registry.skills[skill_id]["enabled"] = False
        return {"success": True, "result": f"Skill '{skill_id}' 已停用"}

    async def _skill_reload(self, params: dict) -> dict:
        if not self.registry:
            return {"success": False, "error": "SkillRegistry 未初始化"}
        count_before = len(self.registry.skills)
        self.registry.scan()
        count_after = len(self.registry.skills)
        return {
            "success": True,
            "result": f"Skill 重新掃描完成：{count_before} → {count_after} 個",
        }

    async def _skill_info(self, params: dict) -> dict:
        skill_id = params.get("skill_id")
        if not skill_id:
            return {"success": False, "error": "缺少 skill_id 參數"}
        if not self.registry:
            return {"success": False, "error": "SkillRegistry 未初始化"}
        meta = self.registry.get_skill(skill_id)
        if not meta:
            return {"success": False, "error": f"Skill '{skill_id}' 不存在"}
        return {"success": True, "result": meta}

    # ── 系統管理 ──

    async def _admin_status(self, params: dict) -> dict:
        uptime = int(time.time() - _START_TIME)
        skill_count = len(self.registry.skills) if self.registry else 0
        schedules = self._load_schedules().get("schedules", [])
        return {
            "success": True,
            "result": {
                "uptime_seconds": uptime,
                "skill_count": skill_count,
                "scheduler_count": len(schedules),
                "scheduler_active": sum(1 for s in schedules if s.get("enabled", True)),
            },
        }

    async def _admin_config(self, params: dict) -> dict:
        import os
        return {
            "success": True,
            "result": {
                "project_root": str(self.project_root),
                "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                "web_port": os.getenv("WEB_PORT", "2141"),
                "skill_count": len(self.registry.skills) if self.registry else 0,
            },
        }

    async def _admin_logs(self, params: dict) -> dict:
        lines = params.get("lines", 20)
        if not self.log_path.exists():
            return {"success": True, "result": "（尚無日誌）"}
        with open(self.log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        return {"success": True, "result": "".join(all_lines[-lines:])}
'''


# ── controller/python_controller.py ──
PYTHON_CONTROLLER_PY = '''"""Python Controller — 安全執行 Python 腳本與函式

支援操作：
  run_function — 動態載入模組並呼叫函式
  run_script   — subprocess 執行腳本（白名單 + timeout）
"""
import importlib.util
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 預設 timeout（秒）
DEFAULT_TIMEOUT = 30

# 允許執行的目錄白名單（相對於 project_root）
ALLOWED_DIRS = ["scripts", "skills"]


class PythonController:
    """安全執行 Python 腳本與函式"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    async def execute(self, action: str, params: dict) -> dict:
        """執行 Python 操作"""
        handlers = {
            "run_function": self._run_function,
            "run_script": self._run_script,
        }
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "error": f"未知的 Python 操作: {action}，可用: {list(handlers.keys())}"}
        return await handler(params)

    def _validate_path(self, script_path: str) -> tuple[bool, str]:
        """驗證路徑安全性：白名單 + 防目錄穿越"""
        try:
            target = (self.project_root / script_path).resolve()
        except (ValueError, OSError) as e:
            return False, f"路徑解析失敗: {e}"

        # 防目錄穿越：必須在 project_root 內
        if not str(target).startswith(str(self.project_root)):
            return False, f"路徑超出專案範圍: {script_path}"

        # 白名單檢查
        rel = target.relative_to(self.project_root)
        first_dir = rel.parts[0] if rel.parts else ""
        if first_dir not in ALLOWED_DIRS:
            return False, f"路徑不在白名單內（允許: {ALLOWED_DIRS}）: {script_path}"

        if not target.exists():
            return False, f"檔案不存在: {script_path}"

        if not target.suffix == ".py":
            return False, f"只允許執行 .py 檔案: {script_path}"

        return True, str(target)

    async def _run_script(self, params: dict) -> dict:
        """subprocess 執行 Python 腳本"""
        script_path = params.get("script")
        if not script_path:
            return {"success": False, "error": "缺少 script 參數"}

        valid, result = self._validate_path(script_path)
        if not valid:
            return {"success": False, "error": result}

        timeout = params.get("timeout", DEFAULT_TIMEOUT)
        args = params.get("args", [])

        cmd = [sys.executable, result] + [str(a) for a in args]
        logger.info(f"執行腳本: {' '.join(cmd)} (timeout={timeout}s)")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root),
            )
            return {
                "success": proc.returncode == 0,
                "result": proc.stdout.strip() if proc.stdout else "",
                "stderr": proc.stderr.strip() if proc.stderr else "",
                "returncode": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"腳本執行超時（{timeout} 秒），已強制終止"}
        except Exception as e:
            return {"success": False, "error": f"腳本執行失敗: {e}"}

    async def _run_function(self, params: dict) -> dict:
        """動態載入模組並呼叫函式"""
        module_path = params.get("module")
        func_name = params.get("function")
        func_args = params.get("args", [])
        func_kwargs = params.get("kwargs", {})

        if not module_path or not func_name:
            return {"success": False, "error": "缺少 module 或 function 參數"}

        valid, resolved = self._validate_path(module_path)
        if not valid:
            return {"success": False, "error": resolved}

        try:
            spec = importlib.util.spec_from_file_location("dynamic_module", resolved)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            func = getattr(module, func_name, None)
            if not func or not callable(func):
                return {"success": False, "error": f"函式 '{func_name}' 不存在或不可呼叫"}

            result = func(*func_args, **func_kwargs)
            return {"success": True, "result": str(result) if result is not None else "（無回傳值）"}
        except Exception as e:
            return {"success": False, "error": f"函式執行失敗: {e}"}
'''

# ── controller/mcp_controller.py ──
MCP_CONTROLLER_PY = '''"""MCP Controller — Model Context Protocol stdio/JSON-RPC 通訊

支援操作：
  connect    — 啟動 MCP Server subprocess + JSON-RPC initialize 握手
  disconnect — 終止 MCP Server subprocess
  call_tool  — 透過 JSON-RPC 呼叫 MCP tool
  list_tools — 列出所有已設定的 MCP Server 和 tools

通訊協定：
  - 透過 stdin/stdout 進行 JSON-RPC 2.0 通訊
  - 訊息格式：JSON 一行一筆（newline-delimited JSON）
  - Server 回應可能帶 Content-Length header 或 bare JSON
"""
import asyncio
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2024-11-05"
CONNECT_TIMEOUT = 10
REQUEST_TIMEOUT = 30


class MCPServerConnection:
    """單一 MCP Server 的 stdio 連接管理"""

    def __init__(self, name: str, config: dict, project_root: Path):
        self.name = name
        self.config = config
        self.project_root = project_root
        self.process: subprocess.Popen | None = None
        self.connected = False
        self.tools: list[dict] = []
        self._req_id = 0
        self._pending: dict[int, dict] = {}
        self._reader_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _build_env(self) -> dict:
        """建立 subprocess 環境變數（展開 ${VAR} 引用）"""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        server_env = self.config.get("env", {})
        for key, value in server_env.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env[key] = os.environ.get(env_var, "")
            else:
                env[key] = str(value)
        return env

    def _reader_loop(self):
        """背景 thread：持續讀取 stdout，解析 JSON-RPC 回應並喚醒等待者"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith("content-length:"):
                    length = int(line.split(":")[1].strip())
                    self.process.stdout.readline()
                    body = self.process.stdout.read(length)
                    try:
                        msg = json.loads(body)
                    except json.JSONDecodeError:
                        continue
                elif line.startswith("{"):
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                else:
                    continue
                msg_id = msg.get("id")
                if msg_id is not None:
                    with self._lock:
                        pending = self._pending.get(msg_id)
                        if pending:
                            pending["result"] = msg
                            pending["event"].set()
            except Exception:
                break
        logger.debug(f"MCP Server \\'{self.name}\\' reader loop 結束")

    def _send_request(self, method: str, params: dict = None, timeout: float = REQUEST_TIMEOUT) -> dict | None:
        """發送 JSON-RPC request 並同步等待回應"""
        if not self.process or not self.process.stdin:
            return None
        req_id = self._next_id()
        msg = {"jsonrpc": "2.0", "method": method, "id": req_id}
        if params is not None:
            msg["params"] = params
        event = threading.Event()
        with self._lock:
            self._pending[req_id] = {"event": event, "result": None}
        try:
            payload = json.dumps(msg) + "\\n"
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            with self._lock:
                self._pending.pop(req_id, None)
            return {"error": f"寫入失敗: {e}"}
        if event.wait(timeout=timeout):
            with self._lock:
                pending = self._pending.pop(req_id, {})
            return pending.get("result")
        else:
            with self._lock:
                self._pending.pop(req_id, None)
            return {"error": f"請求超時（{timeout}s）"}

    def _send_notification(self, method: str, params: dict = None):
        """發送 JSON-RPC notification（無 id，不等回應）"""
        if not self.process or not self.process.stdin:
            return
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        try:
            payload = json.dumps(msg) + "\\n"
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def connect(self) -> dict:
        """啟動 subprocess + JSON-RPC initialize 握手"""
        if self.connected and self.process and self.process.poll() is None:
            return {"success": True, "result": f"MCP Server \\'{self.name}\\' 已連接"}
        command = self.config.get("command", "")
        args = self.config.get("args", [])
        cmd = [command] + args
        try:
            self.process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, bufsize=0,
                cwd=str(self.project_root), env=self._build_env(),
            )
        except FileNotFoundError:
            return {"success": False, "error": f"指令 \\'{command}\\' 未安裝"}
        except Exception as e:
            return {"success": False, "error": f"啟動 MCP Server \\'{self.name}\\' 失敗: {e}"}
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()
        time.sleep(1)
        resp = self._send_request("initialize", {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "{name}-Agent", "version": "1.0.0"},
        }, timeout=CONNECT_TIMEOUT)
        if not resp or "error" in resp:
            self.disconnect_sync()
            err = resp.get("error", "無回應") if resp else "initialize 超時"
            return {"success": False, "error": f"MCP Server \\'{self.name}\\' 握手失敗: {err}"}
        self._send_notification("notifications/initialized")
        server_info = resp.get("result", {}).get("serverInfo", {})
        self.connected = True
        logger.info(f"MCP Server \\'{self.name}\\' 已連接: {server_info.get(\\'name\\', \\'?\\')} v{server_info.get(\\'version\\', \\'?\\')}")
        self._fetch_tools()
        return {"success": True, "result": f"MCP Server \\'{self.name}\\' 已連接（{len(self.tools)} tools）"}

    def _fetch_tools(self):
        """取得 MCP Server 的 tools 清單"""
        resp = self._send_request("tools/list", {})
        if resp and "result" in resp:
            self.tools = resp["result"].get("tools", [])
            logger.info(f"MCP Server \\'{self.name}\\' tools: {[t[\\'name\\'] for t in self.tools]}")
        else:
            logger.warning(f"MCP Server \\'{self.name}\\' 無法取得 tools 清單")

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """呼叫 MCP tool"""
        if not self.connected:
            return {"success": False, "error": f"MCP Server \\'{self.name}\\' 未連接"}
        resp = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
        if not resp:
            return {"success": False, "error": "MCP tool 呼叫無回應"}
        if "error" in resp:
            return {"success": False, "error": str(resp["error"])}
        result = resp.get("result", {})
        content = result.get("content", [])
        texts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
        output = "\\n".join(texts) if texts else json.dumps(result, ensure_ascii=False)
        return {"success": True, "result": output}

    def get_tool_names(self) -> list[str]:
        return [t["name"] for t in self.tools]

    def disconnect_sync(self):
        """終止 subprocess"""
        self.connected = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                pass
            self.process = None
        self.tools = []
        logger.info(f"MCP Server \\'{self.name}\\' 已斷開")


class MCPController:
    """MCP Controller — 管理多個 MCP Server 連接

    功能：Lazy connect、Tool name 解析、Param name 映射
    """

    TOOL_ALIASES = {
        "query": "read_query",
        "write": "write_query",
        "tables": "list_tables",
        "describe": "describe_table",
    }

    PARAM_ALIASES = {
        "read_query": {"sql": "query"},
        "write_query": {"sql": "query"},
        "execute_sql": {"sql": "query"},
        "execute-query": {"sql": "query"},
    }

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config = self._load_config()
        self._connections: dict[str, MCPServerConnection] = {}
        server_count = len([s for s, c in self.config.items() if not c.get("disabled")])
        logger.info(f"MCPController 初始化：{server_count} 個啟用的 MCP Server")

    def _load_config(self) -> dict:
        config_path = self.project_root / "config" / "mcp.json"
        if not config_path.exists():
            logger.warning(f"MCP 設定檔不存在: {config_path}")
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("mcpServers", {})
        except Exception as e:
            logger.error(f"載入 MCP 設定失敗: {e}")
            return {}

    def _get_connection(self, server_name: str) -> MCPServerConnection | None:
        if server_name in self._connections:
            conn = self._connections[server_name]
            if conn.connected and conn.process and conn.process.poll() is None:
                return conn
            conn.disconnect_sync()
        server_config = self.config.get(server_name)
        if not server_config:
            logger.error(f"MCP Server \\'{server_name}\\' 未設定")
            return None
        if server_config.get("disabled"):
            logger.warning(f"MCP Server \\'{server_name}\\' 已停用")
            return None
        conn = MCPServerConnection(server_name, server_config, self.project_root)
        result = conn.connect()
        if result.get("success"):
            self._connections[server_name] = conn
            return conn
        logger.error(f"MCP Server \\'{server_name}\\' 連接失敗: {result.get(\\'error\\')}")
        return None

    def _resolve_tool_name(self, conn: MCPServerConnection, tool_name: str) -> str:
        available = conn.get_tool_names()
        if tool_name in available:
            return tool_name
        alias = self.TOOL_ALIASES.get(tool_name)
        if alias and alias in available:
            logger.info(f"Tool 別名解析: {tool_name} → {alias}")
            return alias
        for avail in available:
            if tool_name in avail:
                logger.info(f"Tool 模糊匹配: {tool_name} → {avail}")
                return avail
        logger.warning(f"Tool \\'{tool_name}\\' 在 Server 中找不到，可用: {available}")
        return tool_name

    def _resolve_params(self, tool_name: str, params: dict) -> dict:
        mapping = self.PARAM_ALIASES.get(tool_name)
        if not mapping:
            return params
        resolved = {}
        for key, value in params.items():
            new_key = mapping.get(key, key)
            if new_key != key:
                logger.info(f"Param 映射: {key} → {new_key}")
            resolved[new_key] = value
        return resolved

    async def execute(self, action: str, params: dict) -> dict:
        if action == "call_tool":
            return await self._call_tool(params)
        elif action == "connect":
            return self._connect(params)
        elif action == "disconnect":
            return self._disconnect(params)
        elif action == "list_tools":
            return self._list_tools(params)
        return {"success": False, "error": f"未知的 MCP action: {action}"}

    async def _call_tool(self, params: dict) -> dict:
        server_name = params.get("server")
        tool_name = params.get("tool")
        tool_params = params.get("params", {})
        if not server_name or not tool_name:
            return {"success": False, "error": "缺少 server 或 tool 參數"}
        conn = self._get_connection(server_name)
        if not conn:
            return {"success": False, "error": f"無法連接 MCP Server \\'{server_name}\\'"}
        resolved_tool = self._resolve_tool_name(conn, tool_name)
        resolved_params = self._resolve_params(resolved_tool, tool_params)
        logger.info(f"MCP call: {server_name}/{resolved_tool} params={resolved_params}")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, conn.call_tool, resolved_tool, resolved_params)
        return result

    def _connect(self, params: dict) -> dict:
        server_name = params.get("server")
        if not server_name:
            return {"success": False, "error": "缺少 server 參數"}
        conn = self._get_connection(server_name)
        if conn:
            return {"success": True, "result": f"MCP Server \\'{server_name}\\' 已連接"}
        return {"success": False, "error": f"MCP Server \\'{server_name}\\' 連接失敗"}

    def _disconnect(self, params: dict) -> dict:
        server_name = params.get("server")
        if not server_name:
            for conn in self._connections.values():
                conn.disconnect_sync()
            self._connections.clear()
            return {"success": True, "result": "所有 MCP Server 已斷開"}
        conn = self._connections.pop(server_name, None)
        if conn:
            conn.disconnect_sync()
            return {"success": True, "result": f"MCP Server \\'{server_name}\\' 已斷開"}
        return {"success": True, "result": f"MCP Server \\'{server_name}\\' 未連接"}

    def _list_tools(self, params: dict) -> dict:
        server_name = params.get("server")
        result = {}
        if server_name:
            conn = self._get_connection(server_name)
            if conn:
                result[server_name] = conn.get_tool_names()
            else:
                return {"success": False, "error": f"MCP Server \\'{server_name}\\' 無法連接"}
        else:
            for name, config in self.config.items():
                if config.get("disabled"):
                    result[name] = "(disabled)"
                elif name in self._connections:
                    result[name] = self._connections[name].get_tool_names()
                else:
                    result[name] = "(未連接)"
        return {"success": True, "result": result}
'''
