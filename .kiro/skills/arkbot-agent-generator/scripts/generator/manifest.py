"""Manifest 定義與載入 — 純 Python dict，無外部依賴"""

from pathlib import Path

# ═══ Manifest 定義 ═══

MANIFESTS = {
    "arkbot": {
        "name": "arkbot",
        "description": "ArkBot 完整架構（預設模式）",
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
            "python {root}/entry/web_entry.py     # Web 對話介面",
            "python {root}/entry/cli_entry.py     # CLI 互動模式",
            "或直接執行 {root}/start.bat          # 一鍵啟動（Windows）",
        ],
    },
    "arkagent": {
        "name": "arkagent",
        "description": "ArkAgent OS 平台級架構（進階模式）",
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
            "python {root}/entry/web_entry.py     # Web 對話介面",
            "python {root}/entry/cli_entry.py     # CLI 互動模式",
            "或直接執行 {root}/start.bat          # 一鍵啟動（Windows）",
        ],
    },
}


def load_manifest(profile: str) -> dict:
    """載入指定 profile 的 manifest"""
    if profile not in MANIFESTS:
        available = ", ".join(MANIFESTS.keys())
        raise ValueError(f"未知的 profile：'{profile}'。可用的 profiles：{available}")
    return MANIFESTS[profile]


def list_profiles() -> list[dict]:
    """列出所有可用 profiles"""
    return [
        {"name": m["name"], "description": m["description"]}
        for m in MANIFESTS.values()
    ]
