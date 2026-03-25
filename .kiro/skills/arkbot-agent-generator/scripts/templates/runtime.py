"""執行層模板 — EXECUTOR_PY, SCHEDULER_PY + Runtime Adapter 模板"""

# ═══ Runtime Adapter 基底 ═══

RUNTIME_ADAPTER_INIT_PY = '''"""Runtime Adapter 模組 — 統一 Skill 執行介面

支援 4 種 runtime：
- python: 本地 Python skill.py 執行（subprocess / async）
- mcp: 透過 MCP Controller 呼叫外部工具
- ai: LLM 推理型 Skill（Gemini API + prompt 管理）
- composite: 組合流程（依序執行多個 Skill）
"""
from .base import RuntimeAdapter
from .python_adapter import PythonAdapter
from .mcp_adapter import MCPAdapter
from .ai_adapter import AIAdapter
from .composite_adapter import CompositeAdapter

__all__ = [
    "RuntimeAdapter",
    "PythonAdapter",
    "MCPAdapter",
    "AIAdapter",
    "CompositeAdapter",
]
'''

RUNTIME_ADAPTER_BASE_PY = '''"""RuntimeAdapter 抽象基底 — 所有 Adapter 的統一介面"""
from abc import ABC, abstractmethod


class RuntimeAdapter(ABC):
    """所有 Runtime Adapter 的基底介面

    每個 Adapter 必須實作 async run()，回傳統一格式：
    {"success": bool, "result": any, "error": str?}
    """

    @abstractmethod
    async def run(self, skill_meta: dict, user_input: str, context: dict) -> dict:
        """執行 Skill

        Args:
            skill_meta: skill.yaml 載入的完整 metadata
            user_input: 使用者輸入（或上一步的 output）
            context: {"memory": str, "prev_results": list, ...}

        Returns:
            {"success": bool, "result": any, "error": str?}
        """
        raise NotImplementedError
'''

PYTHON_ADAPTER_PY = '''"""PythonAdapter — 執行本地 Python skill.py（subprocess / async 雙模式）"""
import importlib.util
import inspect
import json
import logging
import subprocess
import sys
from pathlib import Path

from .base import RuntimeAdapter

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30


class PythonAdapter(RuntimeAdapter):
    """Python Skill 執行器，從 executor.py 抽出的核心邏輯"""

    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)

    async def run(self, skill_meta: dict, user_input: str, context: dict) -> dict:
        """根據 mode 欄位選擇 subprocess 或 async 執行"""
        skill_id = skill_meta.get("skill_id", "")
        skill_py = self.skill_dir / skill_id / "skill.py"

        if not skill_py.exists():
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 缺少 skill.py 執行檔",
            }

        mode = skill_meta.get("mode", "subprocess")
        if mode == "async":
            return await self._execute_async(skill_id, skill_py, user_input)
        else:
            return self._execute_subprocess(skill_id, skill_py, user_input)

    async def _execute_async(self, skill_id: str, skill_py: Path, user_input: str) -> dict:
        """in-process 動態載入執行，支援 async run_async() 或同步 run()"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill_id}", str(skill_py)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "run_async"):
                result = await module.run_async(user_input)
            elif hasattr(module, "run"):
                result = module.run(user_input)
                if inspect.isawaitable(result):
                    result = await result
            else:
                return {"success": False, "error": f"Skill \\'{skill_id}\\' 缺少 run() 或 run_async()"}

            if isinstance(result, dict):
                if "success" in result:
                    return result
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "result": result}
            return {"success": True, "result": str(result)}

        except Exception as e:
            logger.error(f"Skill \\'{skill_id}\\' async 執行失敗：{e}")
            return {"success": False, "error": f"async 執行失敗：{str(e)}"}

    def _execute_subprocess(self, skill_id: str, skill_py: Path, user_input: str) -> dict:
        """subprocess 隔離執行"""
        runner_code = f"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r\\"{skill_py.parent}\\")
try:
    import skill
    result = skill.run({json.dumps(user_input, ensure_ascii=False)})
    print(json.dumps({{"success": True, "result": result}}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}, ensure_ascii=False))
"""

        try:
            proc = subprocess.run(
                [sys.executable, "-c", runner_code],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=TIMEOUT_SECONDS,
                cwd=str(self.skill_dir / skill_id),
            )

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            if stderr:
                logger.warning(f"Skill \\'{skill_id}\\' stderr: {stderr[:500]}")

            if stdout:
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError:
                    return {"success": True, "result": stdout}
            else:
                return {
                    "success": False,
                    "error": f"Skill \\'{skill_id}\\' 無輸出" + (f"，stderr: {stderr[:200]}" if stderr else ""),
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Skill \\'{skill_id}\\' 執行超時（{TIMEOUT_SECONDS}s）")
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 執行超時（{TIMEOUT_SECONDS} 秒），已強制終止",
            }
        except Exception as e:
            logger.error(f"Skill \\'{skill_id}\\' 執行失敗：{e}")
            return {"success": False, "error": f"執行失敗：{str(e)}"}
'''

MCP_ADAPTER_PY = '''"""MCPAdapter — 透過 DomainController 的 MCPController 呼叫外部 MCP tool"""
import logging
from .base import RuntimeAdapter

logger = logging.getLogger(__name__)


class MCPAdapter(RuntimeAdapter):
    """MCP Runtime Adapter

    讀取 skill.yaml 的 mcp: 區塊，透過 DomainController → MCPController 呼叫 tool。

    skill.yaml 範例：
        runtime: mcp
        mcp:
          server: my-server
          tool: query_db
          param_mapping:
            query: "{user_input}"
    """

    def __init__(self, domain_controller=None):
        self.domain_controller = domain_controller

    async def run(self, skill_meta: dict, user_input: str, context: dict) -> dict:
        """執行 MCP tool 呼叫"""
        skill_id = skill_meta.get("skill_id", "")

        if not self.domain_controller:
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 需要 MCP runtime，但 DomainController 未初始化",
            }

        mcp_config = skill_meta.get("mcp", {})
        server = mcp_config.get("server")
        tool = mcp_config.get("tool")

        if not server or not tool:
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 的 mcp 設定不完整（需要 server + tool）",
            }

        # 建立 tool params（根據 param_mapping 替換佔位符）
        param_mapping = mcp_config.get("param_mapping", {})
        tool_params = {}
        for key, template in param_mapping.items():
            if isinstance(template, str):
                tool_params[key] = template.replace("{user_input}", user_input)
            else:
                tool_params[key] = template

        # 透過 DomainController 的 Action 格式呼叫 MCP
        action = {
            "type": "action",
            "controller": "mcp",
            "action": "call_tool",
            "params": {
                "server": server,
                "tool": tool,
                "params": tool_params,
            },
            "fallback_text": f"MCP tool {server}/{tool} 執行完成",
        }

        logger.info(f"MCPAdapter: {skill_id} -> {server}/{tool}")

        try:
            result = await self.domain_controller.execute(action)
            return result
        except Exception as e:
            logger.error(f"MCPAdapter \\'{skill_id}\\' 執行失敗：{e}")
            return {"success": False, "error": f"MCP 執行失敗：{str(e)}"}
'''


AI_ADAPTER_PY = '''"""AIAdapter — LLM 推理型 Skill（統一 prompt / model / fallback 管理）"""
import os
import logging
from pathlib import Path
from .base import RuntimeAdapter

logger = logging.getLogger(__name__)


class AIAdapter(RuntimeAdapter):
    """AI Runtime Adapter

    讀取 skill.yaml 的 ai: 區塊，載入 prompt 模板，呼叫 Gemini API。
    失敗時自動 fallback 到指定 Skill。

    skill.yaml 範例：
        runtime: ai
        ai:
          model: gemini-2.5-flash
          prompt_file: prompt.txt
          temperature: 0.7
          max_tokens: 2048
          output_format: text
          fallback_skill: chat
    """

    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)
        self._client = None

    def _get_client(self):
        """延遲初始化 Gemini client"""
        if self._client is None:
            try:
                from google import genai
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY 未設定")
                self._client = genai.Client(api_key=api_key)
            except ImportError:
                raise ImportError("google-genai 未安裝，無法使用 AI runtime")
        return self._client

    async def run(self, skill_meta: dict, user_input: str, context: dict) -> dict:
        """執行 AI 推理"""
        skill_id = skill_meta.get("skill_id", "")
        ai_config = skill_meta.get("ai", {})

        model = ai_config.get("model", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        prompt_file = ai_config.get("prompt_file", "prompt.txt")
        temperature = ai_config.get("temperature", 0.7)
        output_format = ai_config.get("output_format", "text")
        fallback_skill = ai_config.get("fallback_skill")

        # 載入 prompt 模板
        prompt_path = self.skill_dir / skill_id / prompt_file
        if not prompt_path.exists():
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 的 prompt 檔案不存在：{prompt_file}",
            }

        try:
            prompt_template = prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            return {"success": False, "error": f"讀取 prompt 失敗：{str(e)}"}

        # 替換佔位符
        memory = context.get("memory", "")
        prompt = prompt_template.replace("{user_input}", user_input).replace("{context}", memory)

        # 呼叫 Gemini API
        try:
            client = self._get_client()
            config = {"temperature": temperature}
            max_tokens = ai_config.get("max_tokens")
            if max_tokens:
                config["max_output_tokens"] = max_tokens

            from google.genai import types
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config),
            )
            result_text = response.text.strip() if response.text else ""

            if not result_text:
                raise ValueError("Gemini API 回傳空結果")

            logger.info(f"AIAdapter \\'{skill_id}\\' 成功，output_format={output_format}")

            # 根據 output_format 處理
            if output_format == "json":
                import json, re
                cleaned = result_text
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```\\w*\\n?", "", cleaned)
                    cleaned = re.sub(r"\\n?```$", "", cleaned)
                try:
                    parsed = json.loads(cleaned)
                    return {"success": True, "result": parsed}
                except json.JSONDecodeError:
                    return {"success": True, "result": result_text}

            return {"success": True, "result": result_text}

        except Exception as e:
            logger.warning(f"AIAdapter \\'{skill_id}\\' 失敗：{e}")

            # Fallback 機制
            if fallback_skill:
                logger.info(f"AIAdapter fallback -> {fallback_skill}")
                return {
                    "success": False,
                    "error": str(e),
                    "_fallback_skill": fallback_skill,
                    "_fallback_input": user_input,
                }

            return {"success": False, "error": f"AI 執行失敗：{str(e)}"}
'''

COMPOSITE_ADAPTER_PY = '''"""CompositeAdapter — Workflow 編排（依序執行多個 Skill）"""
import logging
from .base import RuntimeAdapter

logger = logging.getLogger(__name__)

MAX_DEPTH = 5  # 遞迴深度限制，防止循環依賴


class CompositeAdapter(RuntimeAdapter):
    """Composite Runtime Adapter

    讀取 skill.yaml 的 composite: 區塊，依序呼叫 Executor.execute()。
    支援 {prev_result} 和 {user_input} 佔位符。

    skill.yaml 範例：
        runtime: composite
        composite:
          strategy: sequential
          steps:
            - skill_id: crawler
              input_template: "爬取 {user_input}"
            - skill_id: dashboard
              input_template: "產生儀表板"
            - skill_id: notify
              input_template: "發送通報：{prev_result}"
    """

    def __init__(self, executor, depth: int = 0):
        self._executor = executor
        self._depth = depth

    async def run(self, skill_meta: dict, user_input: str, context: dict) -> dict:
        """依序執行 composite steps"""
        skill_id = skill_meta.get("skill_id", "")

        if self._depth >= MAX_DEPTH:
            return {
                "success": False,
                "error": f"Composite Skill \\'{skill_id}\\' 超過最大遞迴深度（{MAX_DEPTH}）",
            }

        composite = skill_meta.get("composite", {})
        steps = composite.get("steps", [])

        if not steps:
            return {
                "success": False,
                "error": f"Composite Skill \\'{skill_id}\\' 沒有定義 steps",
            }

        strategy = composite.get("strategy", "sequential")
        logger.info(f"CompositeAdapter \\'{skill_id}\\': {len(steps)} steps, strategy={strategy}")

        results = []
        prev_result = ""
        executed_skills = set()

        for i, step in enumerate(steps, 1):
            step_skill_id = step.get("skill_id", "")

            if not step_skill_id:
                results.append({"success": False, "error": f"Step {i} 缺少 skill_id"})
                break

            # 循環偵測
            if step_skill_id == skill_id:
                results.append({
                    "success": False,
                    "error": f"Step {i} 循環依賴：\\'{step_skill_id}\\' 呼叫自己",
                })
                break

            # 條件判斷（可選）
            condition = step.get("condition", "")
            if condition and prev_result:
                if not self._eval_condition(condition, prev_result):
                    logger.info(f"CompositeAdapter step {i} 條件不滿足，跳過：{condition}")
                    results.append({"success": True, "result": f"Step {i} 跳過（條件不滿足）", "skipped": True})
                    continue

            # 建立 step input
            input_template = step.get("input_template", "")
            if input_template:
                step_input = input_template.replace("{prev_result}", str(prev_result)).replace("{user_input}", user_input)
            else:
                step_input = user_input

            logger.info(f"CompositeAdapter step {i}/{len(steps)}: skill={step_skill_id}")

            # 執行 step（透過 Executor，走完整路由）
            result = await self._executor.execute(step_skill_id, step_input)
            results.append(result)

            if result.get("success"):
                raw = result.get("result", "")
                prev_result = str(raw) if not isinstance(raw, str) else raw
                executed_skills.add(step_skill_id)
            else:
                logger.warning(f"CompositeAdapter step {i} 失敗，中止：{result.get('error')}")
                break

        # 彙整結果
        all_success = all(r.get("success", False) or r.get("skipped", False) for r in results)
        summaries = []
        for i, r in enumerate(results, 1):
            if r.get("skipped"):
                summaries.append(f"步驟 {i}: 跳過")
            elif r.get("success"):
                text = str(r.get("result", ""))[:200]
                summaries.append(f"步驟 {i}: OK {text}")
            else:
                summaries.append(f"步驟 {i}: FAIL {r.get('error', '未知錯誤')}")

        return {
            "success": all_success,
            "result": "\\n".join(summaries),
            "step_results": results,
        }

    def _eval_condition(self, condition: str, prev_result: str) -> bool:
        """簡易條件判斷（安全版，不用 eval）"""
        condition = condition.strip().lower()
        if "prev.success == true" in condition:
            return bool(prev_result)
        if "prev.success == false" in condition:
            return not bool(prev_result)
        return True
'''


# ═══ executor.py 模板（v2: Runtime Dispatcher） ═══

EXECUTOR_PY = '''"""Skill 執行器 — Runtime Dispatcher + Action 偵測 + Plan 執行

v2: 根據 skill.runtime 欄位路由到對應 RuntimeAdapter
    python → PythonAdapter（subprocess / async）
    mcp    → MCPAdapter（透過 DomainController）
    ai     → AIAdapter（LLM 推理）
    composite → CompositeAdapter（Workflow 編排）
"""
import json
import logging
from pathlib import Path
from skill_registry import SkillRegistry
from runtime import PythonAdapter
from runtime.base import RuntimeAdapter

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, registry: SkillRegistry, skill_dir: str, domain_controller=None):
        self.registry = registry
        self.skill_dir = Path(skill_dir)
        self.domain_controller = domain_controller

        # 初始化 Python Adapter（預設，向後相容）
        self._python_adapter = PythonAdapter(self.skill_dir)

        # 延遲初始化的 Adapter（需要額外依賴時才建立）
        self._adapters: dict[str, RuntimeAdapter] = {}

    def set_domain_controller(self, controller):
        """延遲注入 DomainController（避免循環依賴）"""
        self.domain_controller = controller

    def _get_adapter(self, runtime: str) -> RuntimeAdapter | None:
        """根據 runtime 類型取得對應 Adapter"""
        if runtime == "python":
            return self._python_adapter

        # 延遲載入其他 Adapter（避免未安裝時 import 失敗）
        if runtime not in self._adapters:
            try:
                if runtime == "mcp":
                    from runtime.mcp_adapter import MCPAdapter
                    self._adapters["mcp"] = MCPAdapter(self.domain_controller)
                elif runtime == "ai":
                    from runtime.ai_adapter import AIAdapter
                    self._adapters["ai"] = AIAdapter(self.skill_dir)
                elif runtime == "composite":
                    from runtime.composite_adapter import CompositeAdapter
                    self._adapters["composite"] = CompositeAdapter(self)
                else:
                    logger.warning(f"未知的 runtime 類型：{runtime}")
                    return None
            except ImportError as e:
                logger.warning(f"Runtime \\'{runtime}\\' Adapter 載入失敗：{e}")
                return None

        return self._adapters.get(runtime)

    async def execute(self, skill_id: str, user_input: str) -> dict:
        """根據 skill.runtime 路由到對應 Adapter，並偵測 Action 格式"""
        meta = self.registry.get_skill(skill_id)
        if not meta:
            return {
                "success": False,
                "error": f"目前沒有對應的 Skill（{skill_id}），請透過 skill-creator 建立",
            }

        # ── Runtime Dispatch ──
        runtime = meta.get("runtime", "python")
        adapter = self._get_adapter(runtime)

        if not adapter:
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 的 runtime \\'{runtime}\\' 不支援或未安裝",
            }

        # ── Input Schema 驗證 ──
        validation_error = self._validate_input(meta, user_input)
        if validation_error:
            return validation_error

        # ── 執行 Adapter ──
        context = {}
        result = await adapter.run(meta, user_input, context)

        # ── AI Adapter Fallback：失敗時自動切換到指定 Skill ──
        if not result.get("success") and result.get("_fallback_skill"):
            fallback_id = result["_fallback_skill"]
            fallback_input = result.get("_fallback_input", user_input)
            logger.info(f"AI Skill \\'{skill_id}\\' fallback -> \\'{fallback_id}\\'")
            return await self.execute(fallback_id, fallback_input)

        # ── Action 偵測：Skill 回傳 Action 格式 → 交給 DomainController ──
        if result.get("success") and self.domain_controller:
            raw = result.get("result")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    raw = None
            if isinstance(raw, dict) and self.domain_controller.is_action(raw):
                logger.info(f"Skill \\'{skill_id}\\' 回傳 Action，交給 DomainController")
                action_result = await self.domain_controller.execute(raw)
                if action_result.get("success"):
                    return action_result
                else:
                    fallback = raw.get("fallback_text", action_result.get("error", "操作失敗"))
                    return {"success": False, "error": fallback}

        return result

    def _validate_input(self, meta: dict, user_input: str) -> dict | None:
        """驗證 input schema（可選），回傳 None 表示通過"""
        input_schema = meta.get("input")
        if not input_schema or not isinstance(input_schema, dict):
            return None
        return None

    async def execute_plan(self, plan) -> list[dict]:
        """執行 ExecutionPlan（多步驟）"""
        results = {}
        completed = set()

        while True:
            ready = plan.get_ready_steps(completed)
            if not ready:
                break

            for step in ready:
                if step.skill_id:
                    result = await self.execute(step.skill_id, step.input)
                elif step.controller and self.domain_controller:
                    action = {
                        "type": "action",
                        "controller": step.controller,
                        "action": step.action,
                        "params": step.params,
                    }
                    result = await self.domain_controller.execute(action)
                else:
                    result = {"success": False, "error": f"Step {step.step} 無法執行"}

                results[step.step] = result
                completed.add(step.step)
                logger.info(f"Plan step {step.step} 完成: success={result.get('success')}")

                if not result.get("success"):
                    logger.warning(f"Plan step {step.step} 失敗，中止後續步驟")
                    return list(results.values())

        return list(results.values())
'''



# scheduler.py 模板
SCHEDULER_PY = '''"""ArkBot 排程引擎 — cron 定時自動執行 Skill"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from croniter import croniter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from skill_registry import SkillRegistry
from executor import Executor

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SCHEDULES_PATH = PROJECT_ROOT / "data" / "schedules.json"
LOG_PATH = PROJECT_ROOT / "data" / "scheduler.log"
CHECK_INTERVAL = 60


def load_schedules() -> list[dict]:
    if not SCHEDULES_PATH.exists():
        logger.warning(f"排程設定不存在：{SCHEDULES_PATH}")
        return []
    try:
        with open(SCHEDULES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("schedules", [])
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"排程設定解析失敗：{e}")
        return []


def write_log(schedule_id: str, skill_id: str, success: bool, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "[OK]" if success else "[FAIL]"
    line = f"[{timestamp}] {status} [{schedule_id}] skill={skill_id} | {message}\\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    logger.info(line.strip())


def dry_run():
    schedules = load_schedules()
    if not schedules:
        print("[empty] 無排程設定")
        return
    now = datetime.now()
    print(f"[Scheduler] 排程列表（共 {len(schedules)} 個）\\n")
    for s in schedules:
        enabled = "[ON]" if s.get("enabled", True) else "[OFF]"
        cron_expr = s.get("cron", "")
        next_time = ""
        if cron_expr:
            try:
                it = croniter(cron_expr, now)
                next_time = it.get_next(datetime).strftime("%Y-%m-%d %H:%M")
            except Exception:
                next_time = "[!] cron 格式錯誤"
        print(f"  {enabled} [{s['id']}]")
        print(f"     Skill: {s['skill_id']}")
        print(f"     Cron:  {cron_expr}")
        print(f"     下次:  {next_time}")
        print()


async def run_schedule(executor, schedule):
    sid = schedule["id"]
    skill_id = schedule["skill_id"]
    user_input = schedule.get("input", "")
    params = schedule.get("params", {})
    if params:
        user_input = f"{user_input}|||{json.dumps(params, ensure_ascii=False)}"
    logger.info(f"排程觸發：[{sid}] -> skill={skill_id}")
    try:
        result = await executor.execute(skill_id, user_input)
        success = result.get("success", False)
        msg = str(result.get("result", result.get("error", "")))[:200]
        write_log(sid, skill_id, success, msg)
    except Exception as e:
        write_log(sid, skill_id, False, f"例外：{str(e)[:200]}")


async def main_loop():
    skill_dir = str(PROJECT_ROOT / "skills")
    registry = SkillRegistry(skill_dir)
    executor = Executor(registry, skill_dir)
    logger.info(f"[Scheduler] 排程引擎啟動，載入 {len(registry.skills)} 個 Skill")
    last_fired: dict[str, datetime] = {}
    while True:
        schedules = load_schedules()
        now = datetime.now()
        for s in schedules:
            if not s.get("enabled", True):
                continue
            sid = s["id"]
            cron_expr = s.get("cron", "")
            if not cron_expr:
                continue
            try:
                it = croniter(cron_expr, now)
                prev_time = it.get_prev(datetime)
            except Exception as e:
                logger.warning(f"排程 [{sid}] cron 解析失敗：{e}")
                continue
            last = last_fired.get(sid)
            if last is None or last < prev_time:
                last_fired[sid] = now
                await run_schedule(executor, s)
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArkBot 排程引擎")
    parser.add_argument("--dry-run", action="store_true", help="列出排程，不實際執行")
    args = parser.parse_args()
    if args.dry_run:
        dry_run()
    else:
        asyncio.run(main_loop())
'''
