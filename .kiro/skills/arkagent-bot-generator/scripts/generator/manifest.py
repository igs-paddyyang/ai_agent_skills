"""Manifest 定義與載入 — 純 Python dict，無外部依賴

三種產出模式：
  lite     — 簡易版（4 Skills，~40 檔）
  standard — 完整版（11 Skills，~75 檔）
  agent    — 進階版（11+ Skills，~117 檔，ArkAgent OS）
"""

from pathlib import Path

# ═══ Manifest 定義 ═══

MANIFESTS = {
    "lite": {
        "name": "lite",
        "description": "Lite Bot 簡易版（4 Skills，~40 檔）",
        "default_project_name": "my-bot",
        "modules": [
            "src_lite",
            "runtime_adapters",
            "entry",
            "config_mcp_lite",
            "skills_lite",
        ],
        "features": {
            "compat": False,
            "spec_dsl": False,
            "yaml_skills": True,
            "dashboard_engine": False,
            "controller": False,
            "memory": False,
            "planner": False,
        },
        "config": {
            "env_template": "ARKAGENT_ENV_EXAMPLE",
            "requirements_template": "LITE_REQUIREMENTS_TXT",
            "start_bat_template": "ARKAGENT_START_BAT",
        },
        "post_steps": [
            "cp {root}/.env.example {root}/.env  # 填入金鑰",
            "pip install -r {root}/requirements.txt",
            "python {root}/scripts/init_db.py",
            "python {root}/main.py                # 一鍵啟動",
        ],
    },
    "standard": {
        "name": "standard",
        "description": "Standard Bot 完整版（11 Skills，~75 檔）",
        "default_project_name": "arkbot",
        "modules": [
            "src",
            "dashboard_engine",
            "runtime_adapters",
            "workflow_skills",
            "entry",
            "memory",
            "controller",
            "planner",
            "agents",
            "config_mcp",
            "skills_yaml",
            "tests_basic",
        ],
        "features": {
            "compat": False,
            "spec_dsl": False,
            "yaml_skills": True,
            "dashboard_engine": True,
            "controller": True,
            "memory": True,
            "planner": True,
        },
        "config": {
            "env_template": "ARKAGENT_ENV_EXAMPLE",
            "requirements_template": "ARKAGENT_REQUIREMENTS_TXT",
            "start_bat_template": "ARKAGENT_START_BAT",
        },
        "post_steps": [
            "cp {root}/.env.example {root}/.env  # 填入金鑰",
            "pip install -r {root}/requirements.txt",
            "python {root}/scripts/init_db.py",
            "python {root}/main.py                # 一鍵啟動",
        ],
    },
    "agent": {
        "name": "agent",
        "description": "ArkAgent OS 進階版（11+ Skills，~117 檔）",
        "default_project_name": "arkagent",
        "modules": [
            "specs",
            "kernel",
            "intent",
            "runtime",
            "memory",
            "tools",
            "agents",
            "entry",
            "dashboard_engine",
            "runtime_adapters",
            "workflow_skills",
            "controller",
            "planner",
            "api_gateway",
            "config_mcp",
            "compat",
            "skills_yaml",
            "scripts_extra",
            "tests_full",
        ],
        "features": {
            "compat": True,
            "spec_dsl": True,
            "yaml_skills": True,
            "dashboard_engine": True,
            "controller": True,
            "memory": True,
            "planner": True,
        },
        "config": {
            "env_template": "ARKAGENT_ENV_EXAMPLE",
            "requirements_template": "ARKAGENT_REQUIREMENTS_TXT",
            "start_bat_template": "ARKAGENT_START_BAT",
        },
        "post_steps": [
            "cp {root}/.env.example {root}/.env  # 填入金鑰",
            "pip install -r {root}/requirements.txt",
            "python {root}/scripts/init_db.py",
            "python {root}/scripts/validate_specs.py  # 驗證 Spec",
            "python {root}/main.py                # 一鍵啟動",
        ],
    },
}

# 向後相容 alias
MANIFESTS["arkbot"] = MANIFESTS["standard"]
MANIFESTS["arkagent"] = MANIFESTS["agent"]


def load_manifest(profile: str) -> dict:
    """載入指定 profile 的 manifest"""
    if profile not in MANIFESTS:
        available = ", ".join(k for k in MANIFESTS if k not in ("arkbot", "arkagent"))
        raise ValueError(f"未知的 profile：'{profile}'。可用：{available}（alias: arkbot=standard, arkagent=agent）")
    return MANIFESTS[profile]


def list_profiles() -> list[dict]:
    """列出所有可用 profiles（不含 alias）"""
    seen = set()
    result = []
    for m in MANIFESTS.values():
        if m["name"] not in seen:
            seen.add(m["name"])
            result.append({"name": m["name"], "description": m["description"]})
    return result
