"""執行層模板 — EXECUTOR_PY, SCHEDULER_PY, SKILL_REGISTRY_PY"""

# executor.py 模板（含 async + subprocess 雙模式 + Action 偵測 + Plan 執行）
EXECUTOR_PY = '''"""Skill 執行器 — Sandbox 隔離 + async in-process 雙模式 + Action 偵測 + Plan 執行"""
import importlib.util
import inspect
import json
import logging
import subprocess
import sys
from pathlib import Path
from skill_registry import SkillRegistry

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30


class Executor:
    def __init__(self, registry: SkillRegistry, skill_dir: str, domain_controller=None):
        self.registry = registry
        self.skill_dir = Path(skill_dir)
        self.domain_controller = domain_controller

    def set_domain_controller(self, controller):
        """延遲注入 DomainController（避免循環依賴）"""
        self.domain_controller = controller

    async def execute(self, skill_id: str, user_input: str) -> dict:
        """根據 skill.json 的 mode 欄位選擇執行方式，並偵測 Action 格式"""
        meta = self.registry.get_skill(skill_id)
        if not meta:
            return {
                "success": False,
                "error": f"目前沒有對應的 Skill（{skill_id}），請透過 skill-creator 建立",
            }

        skill_py = self.skill_dir / skill_id / "skill.py"
        if not skill_py.exists():
            return {
                "success": False,
                "error": f"Skill \\'{skill_id}\\' 缺少 skill.py 執行檔",
            }

        mode = meta.get("mode", "subprocess")
        if mode == "async":
            result = await self._execute_async(skill_id, skill_py, user_input)
        else:
            result = self._execute_subprocess(skill_id, skill_py, user_input)

        # ── Action 偵測：Skill 回傳 Action 格式 → 交給 DomainController ──
        if result.get("success") and self.domain_controller:
            raw = result.get("result")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    raw = None
            if isinstance(raw, dict) and self.domain_controller.is_action(raw):
                logger.info(f"Skill '{skill_id}' 回傳 Action，交給 DomainController")
                action_result = await self.domain_controller.execute(raw)
                if action_result.get("success"):
                    return action_result
                else:
                    # Action 執行失敗，回傳 fallback_text
                    fallback = raw.get("fallback_text", action_result.get("error", "操作失敗"))
                    return {"success": False, "error": fallback}

        return result

    async def execute_plan(self, plan) -> list[dict]:
        """執行 ExecutionPlan（多步驟）

        Args:
            plan: ExecutionPlan 物件

        Returns:
            list of step results
        """
        results = {}
        completed = set()

        while True:
            ready = plan.get_ready_steps(completed)
            if not ready:
                break

            for step in ready:
                if step.skill_id:
                    # Skill 執行
                    result = await self.execute(step.skill_id, step.input)
                elif step.controller and self.domain_controller:
                    # 直接 Controller 操作
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

                # 如果某步驟失敗，停止後續步驟
                if not result.get("success"):
                    logger.warning(f"Plan step {step.step} 失敗，中止後續步驟")
                    return list(results.values())

        return list(results.values())

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
    # 將 params 附加到 input（以 JSON 格式，用 ||| 分隔）
    if params:
        user_input = f"{user_input}|||{json.dumps(params, ensure_ascii=False)}"
    logger.info(f"排程觸發：[{sid}] → skill={skill_id}")
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
