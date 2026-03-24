"""Agent Kernel 模板 — AGENT_BASE_PY, KERNEL_CONFIG_PY, KERNEL_LOGGER_PY, SPEC_LOADER_PY"""

# ── kernel/agent_base.py ──
AGENT_BASE_PY = '''"""Agent 基底類別 — lifecycle hooks + 統一訊息處理"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentBase:
    """
    所有 Agent 的基底類別。
    子類別可覆寫 lifecycle hooks 來自訂行為。
    """

    def __init__(self, agent_config: dict, project_root: Path):
        self.config = agent_config
        self.name = agent_config.get("name", "unnamed-agent")
        self.project_root = project_root
        self.skills = agent_config.get("skills", [])
        self.intents = agent_config.get("intents", [])
        self._running = False
        logger.info(f"Agent \\'{self.name}\\' 初始化完成")

    async def start(self):
        """啟動 Agent，呼叫 on_start hook"""
        logger.info(f"Agent \\'{self.name}\\' 啟動中...")
        self._running = True
        await self.on_start()
        logger.info(f"Agent \\'{self.name}\\' 已啟動（skills={self.skills}）")

    async def stop(self):
        """停止 Agent，呼叫 on_stop hook"""
        logger.info(f"Agent \\'{self.name}\\' 停止中...")
        self._running = False
        await self.on_stop()
        logger.info(f"Agent \\'{self.name}\\' 已停止")

    async def handle_message(self, user_input: str) -> dict:
        """
        統一訊息處理入口。
        子類別通常不需覆寫此方法，而是覆寫 on_message。
        """
        if not self._running:
            return {"type": "error", "content": f"Agent \\'{self.name}\\' 尚未啟動"}
        return await self.on_message(user_input)

    # ── Lifecycle Hooks（子類別覆寫）──

    async def on_start(self):
        """Agent 啟動時呼叫，可用於初始化資源"""
        pass

    async def on_message(self, user_input: str) -> dict:
        """處理使用者訊息，回傳 {"type": str, "content": str}"""
        return {"type": "reply", "content": f"[{self.name}] 收到：{user_input}"}

    async def on_stop(self):
        """Agent 停止時呼叫，可用於釋放資源"""
        pass
'''

# ── kernel/config.py ──
KERNEL_CONFIG_PY = '''"""統一配置載入 — .env + runtime.yaml + agent.yaml"""
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_config(project_root: Path) -> dict:
    """
    載入專案配置，優先順序：
    1. .env 環境變數
    2. specs/runtime.yaml
    3. 預設值
    """
    load_dotenv(project_root / ".env")

    config = {
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "telegram_token": os.getenv("TELEGRAM_TOKEN", ""),
        "web_port": int(os.getenv("WEB_PORT", "2141")),
        "database_path": os.getenv("DATABASE_PATH", "data/brain.db"),
        "skill_api_key": os.getenv("SKILL_API_KEY", ""),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    }

    # 載入 runtime.yaml（若存在）
    runtime_yaml = project_root / "specs" / "runtime.yaml"
    if HAS_YAML and runtime_yaml.exists():
        with open(runtime_yaml, encoding="utf-8") as f:
            runtime = yaml.safe_load(f) or {}
        config["runtime"] = runtime
        # 合併 runtime 設定
        execution = runtime.get("execution", {})
        config["concurrency"] = execution.get("concurrency", 10)
        config["default_timeout"] = execution.get("default_timeout", 30)
        scheduler = runtime.get("scheduler", {})
        config["scheduler_enabled"] = scheduler.get("enabled", False)
        config["scheduler_config"] = scheduler.get("config", "data/schedules.json")
        logging_cfg = runtime.get("logging", {})
        config["log_level"] = logging_cfg.get("level", "INFO")
    else:
        config["runtime"] = {}
        config["concurrency"] = 10
        config["default_timeout"] = 30
        config["scheduler_enabled"] = False
        config["log_level"] = "INFO"

    return config
'''

# ── kernel/logger.py ──
KERNEL_LOGGER_PY = '''"""結構化日誌 — 統一日誌格式"""
import logging
import sys


def setup_logger(name: str = "arkagent", level: str = "INFO") -> logging.Logger:
    """建立結構化日誌，回傳 logger 實例"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # 避免重複 handler
    if not logger.handlers:
        logger.addHandler(handler)

    return logger
'''

# ── kernel/spec_loader.py ──
SPEC_LOADER_PY = r'''"""Spec DSL 載入器 — YAML 載入 + JSON Schema 驗證"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.warning("PyYAML 未安裝，Spec DSL 功能受限（僅支援 JSON）")

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.warning("jsonschema 未安裝，Schema 驗證功能停用")


class SpecValidationError(Exception):
    """Spec 驗證失敗"""
    pass


# Schema 對應表
SCHEMA_MAP = {
    "skill": "skill.schema.json",
    "agent": "agent.schema.json",
    "runtime": "runtime.schema.json",
}


def load_yaml(path: Path) -> dict:
    """載入 YAML 檔案，回傳 dict"""
    if not HAS_YAML:
        raise SpecValidationError("PyYAML 未安裝，無法載入 YAML")
    if not path.exists():
        raise SpecValidationError(f"檔案不存在：{path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SpecValidationError(f"YAML 內容不是 dict：{path}")
    return data


def load_json(path: Path) -> dict:
    """載入 JSON 檔案，回傳 dict"""
    if not path.exists():
        raise SpecValidationError(f"檔案不存在：{path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_spec(path: Path) -> dict:
    """自動偵測格式（YAML / JSON）並載入"""
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return load_yaml(path)
    elif suffix == ".json":
        return load_json(path)
    else:
        raise SpecValidationError(f"不支援的格式：{suffix}（支援 .yaml / .yml / .json）")


def validate_schema(data: dict, schema_dir: Path) -> tuple[bool, str]:
    """驗證 data 是否符合對應的 JSON Schema"""
    if not HAS_JSONSCHEMA:
        return True, "jsonschema 未安裝，跳過驗證"

    spec_type = data.get("type")
    if spec_type not in SCHEMA_MAP:
        return False, f"未知的 type: {spec_type}"

    schema_path = schema_dir / SCHEMA_MAP[spec_type]
    if not schema_path.exists():
        return False, f"Schema 檔案不存在：{schema_path}"

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, "驗證通過"
    except jsonschema.ValidationError as e:
        return False, f"驗證失敗：{e.message}"


def load_and_validate(path: Path, schema_dir: Path) -> dict:
    """載入 Spec 並驗證 Schema，失敗拋出 SpecValidationError"""
    data = load_spec(path)
    ok, msg = validate_schema(data, schema_dir)
    if not ok:
        raise SpecValidationError(msg)
    logger.info(f"Spec 載入成功：{path.name}（type={data.get('type')}）")
    return data


def load_all_skills(skills_dir: Path, schema_dir: Path = None) -> dict[str, dict]:
    """掃描 skills/ 目錄，載入所有 skill.yaml（向後相容 skill.json）"""
    skills = {}
    if not skills_dir.exists():
        logger.warning(f"Skills 目錄不存在：{skills_dir}")
        return skills

    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        # 優先 skill.yaml，fallback skill.json
        spec_path = child / "skill.yaml"
        if not spec_path.exists():
            spec_path = child / "skill.yml"
        if not spec_path.exists():
            spec_path = child / "skill.json"
        if not spec_path.exists():
            continue

        try:
            data = load_spec(spec_path)
            if schema_dir:
                ok, msg = validate_schema(data, schema_dir)
                if not ok:
                    logger.warning(f"Skill 驗證失敗，跳過 {spec_path}：{msg}")
                    continue
            # 相容 skill.json 的 skill_id 欄位
            sid = data.get("skill_id") or data.get("name", child.name)
            data["skill_id"] = sid
            data["_path"] = str(child)
            data.setdefault("enabled", True)
            data.setdefault("priority", 0)
            data.setdefault("tags", [])
            skills[sid] = data
            logger.info(f"載入 Skill：{sid}")
        except Exception as e:
            logger.warning(f"載入失敗，跳過 {spec_path}：{e}")

    return skills
'''

# ── kernel/__init__.py ──
KERNEL_INIT_PY = '''"""ArkAgent Kernel — Agent 核心模組"""
from .agent_base import AgentBase
from .config import load_config
from .logger import setup_logger
from .spec_loader import load_spec, load_and_validate, load_all_skills, SpecValidationError
'''
