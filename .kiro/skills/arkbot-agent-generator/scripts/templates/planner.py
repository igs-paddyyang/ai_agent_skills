"""Skill Planner 模板 — SkillPlanner + ExecutionPlan"""

# ── planner/__init__.py ──
PLANNER_INIT_PY = '''"""ArkAgent Skill Planner — LLM 驅動多步驟規劃"""
from .planner import SkillPlanner
from .execution_plan import ExecutionPlan

__all__ = ["SkillPlanner", "ExecutionPlan"]
'''

# ── planner/execution_plan.py ──
EXECUTION_PLAN_PY = '''"""ExecutionPlan — 多步驟執行計畫（DAG 結構）"""
import uuid
from dataclasses import dataclass, field


@dataclass
class PlanStep:
    """單一執行步驟"""
    step: int
    skill_id: str = ""
    input: str = ""
    controller: str = ""
    action: str = ""
    params: dict = field(default_factory=dict)
    depends_on: list[int] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """多步驟執行計畫"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    steps: list[PlanStep] = field(default_factory=list)
    strategy: str = "sequential"  # sequential | parallel | mixed
    is_simple: bool = False       # True = 不需拆解，直接選 Skill

    @classmethod
    def simple(cls, skill_id: str, user_input: str) -> "ExecutionPlan":
        """建立單步驟 Plan（簡單請求不需拆解）"""
        plan = cls(is_simple=True)
        plan.steps = [PlanStep(step=1, skill_id=skill_id, input=user_input)]
        return plan

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionPlan":
        """從 dict 建立 Plan（LLM 回傳格式）"""
        plan = cls(
            plan_id=data.get("plan_id", str(uuid.uuid4())[:8]),
            strategy=data.get("strategy", "sequential"),
        )
        for s in data.get("steps", []):
            plan.steps.append(PlanStep(
                step=s.get("step", 0),
                skill_id=s.get("skill_id", ""),
                input=s.get("input", ""),
                controller=s.get("controller", ""),
                action=s.get("action", ""),
                params=s.get("params", {}),
                depends_on=s.get("depends_on", []),
            ))
        return plan

    def get_ready_steps(self, completed: set[int]) -> list[PlanStep]:
        """取得所有前置步驟已完成的步驟"""
        ready = []
        for step in self.steps:
            if step.step in completed:
                continue
            if all(dep in completed for dep in step.depends_on):
                ready.append(step)
        return ready
'''


# ── planner/planner.py ──
SKILL_PLANNER_PY = '''"""Skill Planner — LLM 驅動多步驟規劃器

流程：
1. 接收使用者輸入 + 可用 Skill 清單
2. 判斷是否需要多步驟拆解
3. 簡單請求 → 直接選 1 個 Skill（ExecutionPlan.simple）
4. 複雜請求 → LLM 拆解為 ExecutionPlan（多步驟 DAG）
"""
import json
import os
import re
import logging
from pathlib import Path
from google import genai
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from .execution_plan import ExecutionPlan

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Few-shot 範例 ──
FEW_SHOT_EXAMPLES = """
範例 1（簡單請求 → 不拆解）：
使用者：「你好」
回應：{"is_simple": true, "skill_id": "chat", "reason": "閒聊不需拆解"}

範例 2（單一 Skill）：
使用者：「幫我爬取 https://example.com」
回應：{"is_simple": true, "skill_id": "crawler", "reason": "單一爬蟲任務"}

範例 3（多步驟）：
使用者：「產生營收儀表板並排程每日早上 9 點執行」
回應：{
    "is_simple": false,
    "plan": {
        "steps": [
            {"step": 1, "skill_id": "dashboard", "input": "產生營收儀表板"},
            {"step": 2, "controller": "system", "action": "scheduler.add",
             "params": {"id": "daily-dashboard", "skill_id": "dashboard", "cron": "0 9 * * *", "input": "產生營收儀表板"},
             "depends_on": [1]}
        ],
        "strategy": "sequential"
    },
    "reason": "需要先產生儀表板，再設定排程"
}
"""

PLANNER_PROMPT = """你是 ArkAgent 的 Skill Planner。根據使用者輸入和可用 Skill 清單，判斷是否需要多步驟拆解。

可用 Skill：
{skills_desc}

可用 System Controller 操作：
- scheduler.add（新增排程）、scheduler.remove（移除排程）、scheduler.list（列出排程）
- skill.list（列出 Skill）、skill.reload（重新掃描）
- admin.status（系統狀態）

{few_shot}

規則：
1. 閒聊、簡單問答 → is_simple=true，選最適合的 skill_id
2. 需要多個 Skill 或 Controller 操作 → is_simple=false，拆解為 steps
3. 每個 step 必須有 step 編號，depends_on 標記前置步驟
4. 只回傳 JSON，不要其他文字

對話 context：
{context}

使用者輸入：{user_input}

回傳 JSON："""


class SkillPlanner:
    """LLM 驅動的多步驟規劃器"""

    def __init__(self):
        pass

    async def analyze(self, user_input: str, available_skills: dict, context: str = "") -> ExecutionPlan:
        """分析使用者輸入，決定執行計畫

        Args:
            user_input: 使用者輸入
            available_skills: {skill_id: {description, intent, ...}}
            context: 對話 context（最近 N 輪）

        Returns:
            ExecutionPlan
        """
        # 建立 Skill 描述
        skills_desc = "\\n".join(
            f"- {sid}: {meta.get('description', '（無描述）')} [intent={meta.get('intent', 'UNKNOWN')}]"
            for sid, meta in available_skills.items()
            if meta.get("enabled", True)
        )

        prompt = PLANNER_PROMPT.format(
            skills_desc=skills_desc,
            few_shot=FEW_SHOT_EXAMPLES,
            context=context or "（無）",
            user_input=user_input,
        )

        try:
            response = client.models.generate_content(model=MODEL, contents=prompt)
            text = response.text.strip()

            # 清理 markdown code block
            if text.startswith("```"):
                text = re.sub(r"^```\\w*\\n?", "", text)
                text = re.sub(r"\\n?```$", "", text)

            data = json.loads(text)
            logger.info(f"Planner 分析結果: is_simple={data.get('is_simple')}, reason={data.get('reason')}")

            if data.get("is_simple", True):
                skill_id = data.get("skill_id", "chat")
                return ExecutionPlan.simple(skill_id, user_input)
            else:
                plan_data = data.get("plan", {})
                return ExecutionPlan.from_dict(plan_data)

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Planner LLM 回傳解析失敗: {e}，fallback 到 chat")
            return ExecutionPlan.simple("chat", user_input)
        except Exception as e:
            logger.error(f"Planner 分析失敗: {e}，fallback 到 chat")
            return ExecutionPlan.simple("chat", user_input)
'''
