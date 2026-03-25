"""決策引擎模板 — SKILL_REGISTRY_PY, SKILL_RESOLVER_PY, SKILL_PROMPT_PY, HYBRID_ROUTER_PY"""

# skill_registry.py 模板（支援 skill.json + skill.yaml + intent list 正規化 + 二層子目錄掃描 + runtime 預設）
SKILL_REGISTRY_PY = '''"""Skill Registry — 掃描 skills/ 目錄，載入 skill.json 或 skill.yaml metadata"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# skill.json 必填欄位
JSON_REQUIRED = ["skill_id", "intent", "description", "examples", "required_params"]
# skill.yaml 必填欄位（較寬鬆）
YAML_REQUIRED = ["skill_id", "intent", "description"]


class SkillRegistry:
    def __init__(self, skill_dir: str | None = None):
        """掃描 skill_dir 下所有子目錄的 skill.json / skill.yaml"""
        self.skills: dict[str, dict] = {}
        if skill_dir:
            self._load_all(skill_dir)

    def _load_all(self, skill_dir: str):
        """遍歷子目錄，優先載入 skill.json，fallback 到 skill.yaml"""
        base = Path(skill_dir)
        if not base.exists():
            logger.warning(f"Skill 目錄不存在：{base}")
            return

        # 收集所有可能的 skill 目錄（含子目錄，如 workflows/daily-report/）
        skill_dirs = []
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            # 直接子目錄有 skill.json / skill.yaml → 視為 skill
            if (child / "skill.json").exists() or (child / "skill.yaml").exists():
                skill_dirs.append(child)
            else:
                # 掃描二層子目錄（如 workflows/daily-report/）
                for grandchild in sorted(child.iterdir()):
                    if grandchild.is_dir() and (
                        (grandchild / "skill.json").exists() or (grandchild / "skill.yaml").exists()
                    ):
                        skill_dirs.append(grandchild)

        for child in skill_dirs:
            meta = None
            source = None

            # 優先 skill.json
            json_path = child / "skill.json"
            if json_path.exists():
                meta = self._load_json(json_path)
                source = "json"

            # fallback skill.yaml
            if meta is None:
                yaml_path = child / "skill.yaml"
                if yaml_path.exists():
                    meta = self._load_yaml(yaml_path)
                    source = "yaml"

            if meta is None:
                continue

            # 驗證必填欄位
            required = JSON_REQUIRED if source == "json" else YAML_REQUIRED
            missing = [k for k in required if k not in meta]
            if missing:
                logger.warning(f"缺少必填欄位 {missing}，跳過 {child.name}")
                continue

            sid = meta["skill_id"]
            if sid in self.skills:
                logger.error(f"skill_id 重複：{sid}，保留第一個")
                continue

            # intent 正規化：list → 第一個值（相容 skill.yaml 的 list 格式）
            intent_val = meta.get("intent", "")
            if isinstance(intent_val, list):
                meta["_intents"] = intent_val  # 保留完整 list
                meta["intent"] = intent_val[0] if intent_val else ""
            else:
                meta["_intents"] = [intent_val]

            # 預設值
            meta.setdefault("examples", [])
            meta.setdefault("required_params", [])
            meta.setdefault("optional_params", [])
            meta.setdefault("tags", [])
            meta.setdefault("priority", 0)
            meta.setdefault("enabled", True)
            meta.setdefault("runtime", "python")  # v2: 預設 python runtime
            meta.setdefault("mode", meta.get("execution", {}).get("mode", "subprocess"))
            meta.setdefault("response_type", "text")
            meta["_path"] = str(child)
            meta["_source"] = source

            self.skills[sid] = meta
            logger.info(f"載入 Skill：{sid} (intent={meta[\'intent\']}, source={source})")

    def _load_json(self, path: Path) -> dict | None:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失敗，跳過 {path}：{e}")
            return None

    def _load_yaml(self, path: Path) -> dict | None:
        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            logger.warning(f"pyyaml 未安裝，無法載入 {path}")
            return None
        except Exception as e:
            logger.warning(f"YAML 解析失敗，跳過 {path}：{e}")
            return None

    def filter_by_intent(self, intent: str) -> list[dict]:
        """回傳 intent 匹配且 enabled=True 的 Skill 列表（支援多 intent）"""
        return [
            s for s in self.skills.values()
            if intent in s.get("_intents", [s.get("intent", "")])
            and s.get("enabled", True)
        ]

    def get_skill(self, skill_id: str) -> dict | None:
        """依 skill_id 取得 metadata"""
        return self.skills.get(skill_id)
'''


# skill_prompt.py 模板
SKILL_PROMPT_PY = '''"""Skill Prompt 建構 — 為 LLM 選擇 Skill 建構 Prompt"""


def build_prompt(user_input: str, candidates: list[dict]) -> str:
    """建構 LLM 選擇 Prompt，候選 > 10 個時截斷"""
    trimmed = candidates[:10]

    skill_list = ""
    for i, s in enumerate(trimmed, 1):
        examples = ", ".join(s.get("examples", [])[:3])
        skill_list += (
            f"\\n{i}. skill_id: {s['skill_id']}"
            f"\\n   description: {s['description']}"
            f"\\n   examples: [{examples}]"
        )

    return f"""你是 Skill 選擇器。從以下候選 Skill 中選出最適合回應使用者問題的一個。
只回傳 JSON，不要其他文字。

使用者輸入：{user_input}

候選 Skill：{skill_list}

回傳格式：{{"skill_id": "選中的 skill_id", "reason": "選擇原因"}}

如果沒有任何候選適合，回傳：{{"skill_id": null, "reason": "無適合的 Skill"}}"""
'''


# skill_resolver.py 模板
SKILL_RESOLVER_PY = r'''"""Skill Resolver — 三階段決策引擎（Rule → LLM → Fallback）"""
import json
import re
import logging
from skill_registry import SkillRegistry
from skill_prompt import build_prompt

logger = logging.getLogger(__name__)


class SkillResolver:
    def __init__(self, registry: SkillRegistry, llm_client=None):
        self.registry = registry
        self.llm_client = llm_client

    async def resolve(self, user_input: str, intent: str, state=None) -> dict | None:
        """主流程：取候選 → Rule Match → LLM Select → Fallback"""
        candidates = self.registry.filter_by_intent(intent)
        if not candidates:
            return None

        # 階段 1：Rule Match
        result = self._rule_match(user_input, candidates)
        if result:
            return {
                "skill_id": result["skill_id"],
                "reason": f"tag 命中：{result.get('_matched_tag', '')}",
                "method": "rule",
            }

        # 階段 2：LLM Select
        result = await self._llm_select(user_input, candidates)
        if result:
            return result

        # 階段 3：Fallback
        fallback = sorted(
            candidates, key=lambda s: s.get("priority", 0), reverse=True
        )[0]
        return {
            "skill_id": fallback["skill_id"],
            "reason": "fallback (priority)",
            "method": "fallback",
        }

    def _rule_match(self, text: str, candidates: list[dict]) -> dict | None:
        """遍歷候選 Skill 的 tags，case-insensitive 比對使用者輸入"""
        lower_text = text.lower()
        for skill in candidates:
            for tag in skill.get("tags", []):
                if tag.lower() in lower_text:
                    skill["_matched_tag"] = tag
                    return skill
        return None

    async def _llm_select(self, user_input: str, candidates: list[dict]) -> dict | None:
        """呼叫 LLM 精選，解析 JSON，驗證 skill_id 存在於候選中"""
        if not self.llm_client:
            return None

        prompt = build_prompt(user_input, candidates)
        try:
            resp = self.llm_client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            text = resp.text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            result = json.loads(text)

            sid = result.get("skill_id")
            if not sid:
                return None

            # 驗證 skill_id 存在於候選中
            valid_ids = {s["skill_id"] for s in candidates}
            if sid not in valid_ids:
                logger.warning(f"LLM 回傳的 skill_id '{sid}' 不在候選中")
                return None

            return {
                "skill_id": sid,
                "reason": result.get("reason", "LLM 選擇"),
                "method": "llm",
            }
        except Exception as e:
            logger.warning(f"LLM Select 失敗：{e}")
            return None
'''


# hybrid_router.py 模板
HYBRID_ROUTER_PY = '''"""Hybrid Router — Intent Router + Skill Resolver 整合"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from intent_router import ArkBrain
from skill_registry import SkillRegistry
from skill_resolver import SkillResolver

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

# 延遲初始化元件（首次呼叫 route 時才建立）
brain = ArkBrain()
_skill_dir = str(PROJECT_ROOT / "skills")
registry = SkillRegistry(_skill_dir)
_resolver = None


def _get_resolver():
    global _resolver
    if _resolver is None:
        from google import genai
        _llm_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        _resolver = SkillResolver(registry, llm_client=_llm_client)
        logger.info(f"Hybrid Router 初始化完成，載入 {len(registry.skills)} 個 Skill")
    return _resolver


async def route(user_input: str) -> dict:
    """
    完整路由流程：
    1. Intent Router 粗分類
    2. CASUAL → 直接回傳 fast_path
    3. 其餘 → SkillResolver.resolve()
    4. 無結果 → 回傳 None
    """
    intent_result = brain.classify_intent(user_input)
    intent = intent_result.get("intent", "CASUAL")

    # CASUAL 快速路徑
    if intent == "CASUAL":
        return {
            "intent": intent,
            "intent_result": intent_result,
            "skill_id": None,
            "method": "fast_path",
            "reason": "CASUAL 快速路徑，不經 Resolver",
        }

    # 嘗試 Skill Resolver
    resolved = await _get_resolver().resolve(user_input, intent)

    return {
        "intent": intent,
        "intent_result": intent_result,
        "skill_id": resolved["skill_id"] if resolved else None,
        "method": resolved["method"] if resolved else None,
        "reason": resolved["reason"] if resolved else "無匹配 Skill",
    }
'''
