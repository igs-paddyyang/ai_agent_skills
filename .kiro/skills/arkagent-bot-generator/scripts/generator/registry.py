"""Module Registry — 模組名 → 生成函式的映射表"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Generator

from templates import (
    # ── Spec DSL ──
    SKILL_SCHEMA_JSON, AGENT_SCHEMA_JSON, RUNTIME_SCHEMA_JSON,
    SKILL_EXAMPLE_YAML, AGENT_EXAMPLE_YAML, RUNTIME_YAML,
    VALIDATE_SPECS_PY, ARCH_REVIEWER_PROMPT, REVIEW_ARCHITECTURE_PY,
    # ── Kernel ──
    AGENT_BASE_PY, KERNEL_CONFIG_PY, KERNEL_LOGGER_PY,
    SPEC_LOADER_PY, KERNEL_INIT_PY,
    # ── Memory ──
    SHORT_TERM_PY, LONG_TERM_PY, MEMORY_INIT_PY,
    # ── Tools ──
    GATEWAY_PY, GEMINI_TOOL_PY, TELEGRAM_TOOL_PY, WEB_TOOL_PY, TOOLS_INIT_PY,
    # ── Intent ──
    INTENT_ROUTER_PY, HYBRID_ROUTER_PY,
    # ── Runtime ──
    EXECUTOR_PY, SCHEDULER_PY,
    RUNTIME_ADAPTER_INIT_PY, RUNTIME_ADAPTER_BASE_PY,
    PYTHON_ADAPTER_PY, MCP_ADAPTER_PY, AI_ADAPTER_PY, COMPOSITE_ADAPTER_PY,
    # ── Decision ──
    SKILL_REGISTRY_PY, SKILL_RESOLVER_PY, SKILL_PROMPT_PY,
    # ── Core ──
    CORE_PY, CORE_LITE_PY, GEMINI_CANVAS_SKILL_PY, DASHBOARD_SKILL_PY, CRAWLER_SKILL_PY, FORMAT_UTILS_PY,
    # ── Entry ──
    BOT_MAIN_PY, TELEGRAM_ENTRY_PY, WEB_SERVER_PY, WEB_ENTRY_PY, WEB_INDEX_HTML, CLI_ENTRY_PY, DASHBOARD_HUB_HTML, MAIN_PY,
    # ── Skills ──
    SKILL_PKG_CRAWLER_PY,
    SKILL_PKG_CHAT_PY,
    SKILL_PKG_DASHBOARD_PY,
    # ── Skills YAML ──
    SKILL_PKG_CRAWLER_YAML, SKILL_PKG_CHAT_YAML, SKILL_PKG_DASHBOARD_YAML,
    SKILL_PKG_NOTIFY_YAML, SKILL_PKG_NOTIFY_PY, SKILL_PKG_NOTIFY_LITE_PY,
    SKILL_PKG_CANVAS_YAML, SKILL_PKG_CANVAS_PY,
    SKILL_PKG_DAILY_REPORT_YAML,
    # AIBI Skill Package（MCP / AI / Composite）
    SKILL_PKG_SQL_QUERY_YAML, SKILL_PKG_BIGQUERY_QUERY_YAML,
    SKILL_PKG_MSSQL_QUERY_YAML,
    SKILL_PKG_KPI_ANALYZER_YAML, SKILL_PKG_KPI_ANALYZER_PROMPT,
    SKILL_PKG_ANOMALY_REPORT_YAML,
    # ── Lite Skill Templates ──
    SKILL_PKG_DASHBOARD_LITE_PY,
    # ── TG 通報樣板 ──
    TG_FORMATTER_PY, TG_REVENUE_TEMPLATE, TG_GAME_TEMPLATE,
    # ── Sample Data ──
    SAMPLE_REVENUE_JSON, SAMPLE_SLOTS_JSON, SAMPLE_FISH_JSON,
    # ── Tests ──
    TEST_BASIC_PY, TEST_SKILL_REGISTRY_PY, TEST_SKILL_RESOLVER_PY, TEST_EXECUTOR_PY,
    TEST_KERNEL_PY, TEST_MEMORY_PY, TEST_TOOLS_PY, TEST_SPECS_PY,
    TEST_DOMAIN_CONTROLLER_PY, TEST_SYSTEM_CONTROLLER_PY,
    TEST_PYTHON_CONTROLLER_PY, TEST_MCP_CONTROLLER_PY,
    TEST_PLANNER_PY, TEST_GATEWAY_PY,
    # ── Config ──
    START_BAT, SCHEDULES_JSON, ENV_EXAMPLE, REQUIREMENTS_TXT,
    ARKAGENT_START_BAT, ARKAGENT_ENV_EXAMPLE, ARKAGENT_REQUIREMENTS_TXT,
    LITE_REQUIREMENTS_TXT,
    TELEGRAM_CONFIG_JSON,
    INIT_DB_PY, BOT_TEST_GUIDE,
    # ── Domain Controller ──
    MCP_CONFIG_JSON, CONTROLLER_INIT_PY, DOMAIN_CONTROLLER_PY,
    SYSTEM_CONTROLLER_PY, PYTHON_CONTROLLER_PY, MCP_CONTROLLER_PY,
    # ── Skill Planner ──
    PLANNER_INIT_PY, EXECUTION_PLAN_PY, SKILL_PLANNER_PY,
    # ── API Gateway ──
    GATEWAY_INIT_PY, GATEWAY_AUTH_PY, GATEWAY_RATE_LIMITER_PY,
    GATEWAY_WEBSOCKET_PY, GATEWAY_APP_PY,
)


# ═══ 輔助：取得 assets/index.html ═══

def _get_index_html() -> str:
    """嘗試從 assets/ 讀取完整版 index.html，失敗則用模板"""
    skill_dir = Path(__file__).resolve().parent.parent.parent
    index_html_src = skill_dir / "assets" / "index.html"
    if index_html_src.exists():
        return index_html_src.read_text(encoding="utf-8")
    return WEB_INDEX_HTML


def _get_notify_skill() -> str:
    """從 assets/ 讀取 notify_skill.py 完整實作"""
    skill_dir = Path(__file__).resolve().parent.parent.parent
    src = skill_dir / "assets" / "notify_skill.py"
    if src.exists():
        return src.read_text(encoding="utf-8")
    return '"""Notify Skill — 請從 assets/notify_skill.py 取得完整實作"""\n'


def _skill_md(name: str, desc: str) -> str:
    """產出 SKILL.md 模板"""
    return f"""---
name: {name}
description: "{desc}"
---

# {name}

{desc}
"""


def _readme_md(name: str, runtime: str, desc: str) -> str:
    """產出 README.md 模板"""
    return f"""# {name}

| 項目 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| Runtime | {runtime} |
| 最後更新 | 2026-03-25 |

## 說明
{desc}

## 變更紀錄
- 0.1.0 — 初始版本（由 arkagent-bot-generator lite 產出）
"""


def _compat_dir(g: "Generator") -> str:
    """取得相容層目錄名：arkagent 用 compat/，arkbot 用 src/"""
    return "compat" if g.manifest["features"].get("compat") else "src"


def _replace_compat(template: str, compat: str) -> str:
    """替換模板中的 __COMPAT_DIR__ 佔位符"""
    return template.replace("__COMPAT_DIR__", compat)


# ═══ Lite 模式專用模組 ═══

def gen_src_lite(g: "Generator"):
    """Lite src/ — 精簡版核心模組（無 hybrid_router / skill_resolver / skill_prompt / gemini_canvas）"""
    r = g.root
    g.create_file(r / "src" / "arkbot_core.py", CORE_LITE_PY)
    g.create_file(r / "src" / "intent_router.py", INTENT_ROUTER_PY)
    g.create_file(r / "src" / "crawler_skill.py", CRAWLER_SKILL_PY)
    g.create_file(r / "src" / "format_utils.py", FORMAT_UTILS_PY)
    g.create_file(r / "src" / "skill_registry.py", SKILL_REGISTRY_PY)
    g.create_file(r / "src" / "executor.py", EXECUTOR_PY)
    g.create_file(r / "src" / "scheduler.py", _replace_compat(SCHEDULER_PY, "src"))
    g.create_file(r / "src" / "notify_skill.py", _get_notify_skill())


def gen_skills_lite(g: "Generator"):
    """Lite skills/ — 4 個基礎 skill（chat / crawler / dashboard / notify）
    統一目錄結構：config/skill.yaml + scripts/skill.py + SKILL.md + README.md + references/.gitkeep
    notify 額外產出 assets/（tg_formatter.py + tg_revenue_template.txt + tg_game_template.txt）
    """
    r = g.root
    cd = _compat_dir(g)

    # ── chat ──
    g.create_file(r / "skills" / "chat" / "config" / "skill.yaml", SKILL_PKG_CHAT_YAML)
    g.create_file(r / "skills" / "chat" / "scripts" / "skill.py", SKILL_PKG_CHAT_PY)
    g.create_file(r / "skills" / "chat" / "references" / ".gitkeep", "\n")
    g.create_file(r / "skills" / "chat" / "SKILL.md", _skill_md("chat", "Gemini AI chat"))
    g.create_file(r / "skills" / "chat" / "README.md", _readme_md("chat", "python", "Gemini AI chat"))

    # ── crawler ──
    g.create_file(r / "skills" / "crawler" / "config" / "skill.yaml", SKILL_PKG_CRAWLER_YAML)
    g.create_file(r / "skills" / "crawler" / "scripts" / "skill.py", SKILL_PKG_CRAWLER_PY)
    g.create_file(r / "skills" / "crawler" / "references" / ".gitkeep", "\n")
    g.create_file(r / "skills" / "crawler" / "SKILL.md", _skill_md("crawler", "Web crawler + summary"))
    g.create_file(r / "skills" / "crawler" / "README.md", _readme_md("crawler", "python", "Web crawler + summary"))

    # ── dashboard ──
    g.create_file(r / "skills" / "dashboard" / "config" / "skill.yaml", SKILL_PKG_DASHBOARD_YAML)
    g.create_file(r / "skills" / "dashboard" / "scripts" / "skill.py", SKILL_PKG_DASHBOARD_LITE_PY)
    g.create_file(r / "skills" / "dashboard" / "references" / ".gitkeep", "\n")
    g.create_file(r / "skills" / "dashboard" / "SKILL.md", _skill_md("dashboard", "Gemini dashboard generator"))
    g.create_file(r / "skills" / "dashboard" / "README.md", _readme_md("dashboard", "python", "Gemini dashboard generator"))

    # ── notify（含 assets/tg_formatter + templates）──
    g.create_file(r / "skills" / "notify" / "config" / "skill.yaml", SKILL_PKG_NOTIFY_YAML)
    g.create_file(r / "skills" / "notify" / "scripts" / "skill.py", _replace_compat(SKILL_PKG_NOTIFY_LITE_PY, cd))
    g.create_file(r / "skills" / "notify" / "references" / ".gitkeep", "\n")
    g.create_file(r / "skills" / "notify" / "SKILL.md", _skill_md("notify", "TG notification sender"))
    g.create_file(r / "skills" / "notify" / "README.md", _readme_md("notify", "python", "TG notification sender"))
    g.create_file(r / "skills" / "notify" / "assets" / "tg_formatter.py", TG_FORMATTER_PY)
    g.create_file(r / "skills" / "notify" / "assets" / "tg_revenue_template.txt", TG_REVENUE_TEMPLATE)
    g.create_file(r / "skills" / "notify" / "assets" / "tg_game_template.txt", TG_GAME_TEMPLATE)


def gen_config_mcp_lite(g: "Generator"):
    """Lite config/ — 只有 sqlite-server（無 bigquery / mssql）"""
    r = g.root
    lite_mcp = '''{
    "mcpServers": {
        "sqlite-server": {
            "command": "uvx",
            "args": ["mcp-server-sqlite", "--db-path", "data/brain.db"],
            "disabled": false
        }
    }
}'''
    g.create_file(r / "config" / "mcp.json", lite_mcp)
    g.create_file(r / "config" / "telegram.json", TELEGRAM_CONFIG_JSON)


# ═══ Standard（ArkBot）專用模組 ═══

def gen_src(g: "Generator"):
    """ArkBot src/ — 核心模組（11 個，入口由 gen_entry 負責）"""
    r = g.root
    g.create_file(r / "src" / "arkbot_core.py", CORE_PY)
    g.create_file(r / "src" / "intent_router.py", INTENT_ROUTER_PY)
    g.create_file(r / "src" / "crawler_skill.py", CRAWLER_SKILL_PY)
    g.create_file(r / "src" / "gemini_canvas_skill.py", GEMINI_CANVAS_SKILL_PY)
    g.create_file(r / "src" / "dashboard_skill.py", DASHBOARD_SKILL_PY)
    g.create_file(r / "src" / "format_utils.py", FORMAT_UTILS_PY)
    g.create_file(r / "src" / "skill_registry.py", SKILL_REGISTRY_PY)
    g.create_file(r / "src" / "skill_prompt.py", SKILL_PROMPT_PY)
    g.create_file(r / "src" / "skill_resolver.py", SKILL_RESOLVER_PY)
    g.create_file(r / "src" / "hybrid_router.py", HYBRID_ROUTER_PY)
    g.create_file(r / "src" / "executor.py", EXECUTOR_PY)
    g.create_file(r / "src" / "scheduler.py", _replace_compat(SCHEDULER_PY, "src"))
    g.create_file(r / "src" / "notify_skill.py", _get_notify_skill())


def gen_tests_basic(g: "Generator"):
    """ArkBot tests/ — 4 個基礎測試"""
    r = g.root
    g.create_file(r / "tests" / "test_basic.py", TEST_BASIC_PY)
    g.create_file(r / "tests" / "test_skill_registry.py", TEST_SKILL_REGISTRY_PY)
    g.create_file(r / "tests" / "test_skill_resolver.py", TEST_SKILL_RESOLVER_PY)
    g.create_file(r / "tests" / "test_executor.py", TEST_EXECUTOR_PY)


# ═══ ArkAgent OS 模組 ═══

def gen_specs(g: "Generator"):
    """specs/ — Spec DSL（JSON Schema + 範例 YAML）"""
    r = g.root
    g.create_file(r / "specs" / "schema" / "skill.schema.json", SKILL_SCHEMA_JSON)
    g.create_file(r / "specs" / "schema" / "agent.schema.json", AGENT_SCHEMA_JSON)
    g.create_file(r / "specs" / "schema" / "runtime.schema.json", RUNTIME_SCHEMA_JSON)
    g.create_file(r / "specs" / "runtime.yaml", RUNTIME_YAML)
    g.create_file(r / "specs" / "examples" / "skill-example.yaml", SKILL_EXAMPLE_YAML)
    g.create_file(r / "specs" / "examples" / "agent-example.yaml", AGENT_EXAMPLE_YAML)


def gen_kernel(g: "Generator"):
    """kernel/ — Agent Kernel（5 個檔案）"""
    r = g.root
    g.create_file(r / "kernel" / "__init__.py", KERNEL_INIT_PY)
    g.create_file(r / "kernel" / "agent_base.py", AGENT_BASE_PY)
    g.create_file(r / "kernel" / "config.py", KERNEL_CONFIG_PY)
    g.create_file(r / "kernel" / "logger.py", KERNEL_LOGGER_PY)
    g.create_file(r / "kernel" / "spec_loader.py", SPEC_LOADER_PY)


def gen_intent(g: "Generator"):
    """intent/ — Intent Engine"""
    r = g.root
    g.create_file(r / "intent" / "__init__.py", '"""ArkAgent Intent Engine"""')
    g.create_file(r / "intent" / "classifier.py", INTENT_ROUTER_PY)
    g.create_file(r / "intent" / "router.py", HYBRID_ROUTER_PY)


def gen_runtime(g: "Generator"):
    """runtime/ — Skill Runtime"""
    r = g.root
    cd = _compat_dir(g)
    g.create_file(r / "runtime" / "__init__.py", '"""ArkAgent Skill Runtime"""')
    g.create_file(r / "runtime" / "registry.py", SKILL_REGISTRY_PY)
    g.create_file(r / "runtime" / "resolver.py", SKILL_RESOLVER_PY)
    g.create_file(r / "runtime" / "prompt.py", SKILL_PROMPT_PY)
    g.create_file(r / "runtime" / "executor.py", EXECUTOR_PY)
    g.create_file(r / "runtime" / "scheduler.py", _replace_compat(SCHEDULER_PY, cd))


def gen_memory(g: "Generator"):
    """memory/ — Memory System"""
    r = g.root
    g.create_file(r / "memory" / "__init__.py", MEMORY_INIT_PY)
    g.create_file(r / "memory" / "short_term.py", SHORT_TERM_PY)
    g.create_file(r / "memory" / "long_term.py", LONG_TERM_PY)


def gen_tools(g: "Generator"):
    """tools/ — Tool Gateway"""
    r = g.root
    g.create_file(r / "tools" / "__init__.py", TOOLS_INIT_PY)
    g.create_file(r / "tools" / "gateway.py", GATEWAY_PY)
    g.create_file(r / "tools" / "gemini_tool.py", GEMINI_TOOL_PY)
    g.create_file(r / "tools" / "telegram_tool.py", TELEGRAM_TOOL_PY)
    g.create_file(r / "tools" / "web_tool.py", WEB_TOOL_PY)


def gen_agents(g: "Generator"):
    """agents/ — Agent 定義"""
    r = g.root
    g.create_file(r / "agents" / "default" / "agent.yaml", AGENT_EXAMPLE_YAML)


def gen_entry(g: "Generator"):
    """entry/ — 入口層（Telegram + Web + CLI），自動適配 src/ 或 compat/ 路徑"""
    r = g.root
    cd = _compat_dir(g)
    g.create_file(r / "entry" / "telegram_entry.py", _replace_compat(TELEGRAM_ENTRY_PY, cd))
    # Lite 模式：web_entry 從 arkbot_core 匯入 registry（不依賴 hybrid_router）
    web_entry = _replace_compat(WEB_ENTRY_PY, cd)
    is_lite = g.manifest["name"] == "lite"
    if is_lite:
        web_entry = web_entry.replace(
            "from hybrid_router import registry",
            "from arkbot_core import registry"
        )
    g.create_file(r / "entry" / "web_entry.py", web_entry)
    g.create_file(r / "entry" / "cli_entry.py", _replace_compat(CLI_ENTRY_PY, cd))


def gen_controller(g: "Generator"):
    """controller/ — Domain Controller（5 個檔案）"""
    r = g.root
    g.create_file(r / "controller" / "__init__.py", CONTROLLER_INIT_PY)
    g.create_file(r / "controller" / "domain_controller.py", DOMAIN_CONTROLLER_PY)
    g.create_file(r / "controller" / "system_controller.py", SYSTEM_CONTROLLER_PY)
    g.create_file(r / "controller" / "python_controller.py", PYTHON_CONTROLLER_PY)
    g.create_file(r / "controller" / "mcp_controller.py", MCP_CONTROLLER_PY)


def gen_planner(g: "Generator"):
    """planner/ — Skill Planner"""
    r = g.root
    g.create_file(r / "planner" / "__init__.py", PLANNER_INIT_PY)
    g.create_file(r / "planner" / "planner.py", SKILL_PLANNER_PY)
    g.create_file(r / "planner" / "execution_plan.py", EXECUTION_PLAN_PY)


def gen_api_gateway(g: "Generator"):
    """gateway/ — API Gateway"""
    r = g.root
    cd = _compat_dir(g)
    g.create_file(r / "gateway" / "__init__.py", GATEWAY_INIT_PY)
    g.create_file(r / "gateway" / "app.py", _replace_compat(GATEWAY_APP_PY, cd))
    g.create_file(r / "gateway" / "auth.py", GATEWAY_AUTH_PY)
    g.create_file(r / "gateway" / "rate_limiter.py", GATEWAY_RATE_LIMITER_PY)
    g.create_file(r / "gateway" / "websocket_handler.py", GATEWAY_WEBSOCKET_PY)


def gen_config_mcp(g: "Generator"):
    """config/ — MCP 設定 + Telegram 路由設定"""
    g.create_file(g.root / "config" / "mcp.json", MCP_CONFIG_JSON)
    g.create_file(g.root / "config" / "telegram.json", TELEGRAM_CONFIG_JSON)


def gen_compat(g: "Generator"):
    """compat/ 相容層 — ArkAgent 保留舊模組方便遷移（目錄名明確標示過渡性質）"""
    r = g.root
    g.create_file(r / "compat" / "arkbot_core.py", CORE_PY)
    g.create_file(r / "compat" / "gemini_canvas_skill.py", GEMINI_CANVAS_SKILL_PY)
    g.create_file(r / "compat" / "dashboard_skill.py", DASHBOARD_SKILL_PY)
    g.create_file(r / "compat" / "crawler_skill.py", CRAWLER_SKILL_PY)
    g.create_file(r / "compat" / "format_utils.py", FORMAT_UTILS_PY)
    g.create_file(r / "compat" / "intent_router.py", INTENT_ROUTER_PY)
    g.create_file(r / "compat" / "skill_registry.py", SKILL_REGISTRY_PY)
    g.create_file(r / "compat" / "skill_resolver.py", SKILL_RESOLVER_PY)
    g.create_file(r / "compat" / "skill_prompt.py", SKILL_PROMPT_PY)
    g.create_file(r / "compat" / "hybrid_router.py", HYBRID_ROUTER_PY)
    g.create_file(r / "compat" / "executor.py", EXECUTOR_PY)
    g.create_file(r / "compat" / "scheduler.py", SCHEDULER_PY)
    g.create_file(r / "compat" / "notify_skill.py", _get_notify_skill())


def gen_skills_yaml(g: "Generator"):
    """skills/ — skill.yaml 版（ArkAgent），含 notify + gemini-canvas + AIBI skills"""
    r = g.root
    cd = _compat_dir(g)
    g.create_file(r / "skills" / "crawler" / "skill.yaml", SKILL_PKG_CRAWLER_YAML)
    g.create_file(r / "skills" / "crawler" / "skill.py", SKILL_PKG_CRAWLER_PY)
    g.create_file(r / "skills" / "chat" / "skill.yaml", SKILL_PKG_CHAT_YAML)
    g.create_file(r / "skills" / "chat" / "skill.py", SKILL_PKG_CHAT_PY)
    g.create_file(r / "skills" / "dashboard" / "skill.yaml", SKILL_PKG_DASHBOARD_YAML)
    g.create_file(r / "skills" / "dashboard" / "skill.py", SKILL_PKG_DASHBOARD_PY)
    g.create_file(r / "skills" / "gemini-canvas" / "skill.yaml", SKILL_PKG_CANVAS_YAML)
    g.create_file(r / "skills" / "gemini-canvas" / "skill.py", SKILL_PKG_CANVAS_PY)
    g.create_file(r / "skills" / "notify" / "skill.yaml", SKILL_PKG_NOTIFY_YAML)
    g.create_file(r / "skills" / "notify" / "skill.py", _replace_compat(SKILL_PKG_NOTIFY_PY, cd))
    # AIBI Skills（MCP + AI）
    g.create_file(r / "skills" / "sql-query" / "skill.yaml", SKILL_PKG_SQL_QUERY_YAML)
    g.create_file(r / "skills" / "bigquery-query" / "skill.yaml", SKILL_PKG_BIGQUERY_QUERY_YAML)
    g.create_file(r / "skills" / "mssql-query" / "skill.yaml", SKILL_PKG_MSSQL_QUERY_YAML)
    g.create_file(r / "skills" / "kpi-analyzer" / "skill.yaml", SKILL_PKG_KPI_ANALYZER_YAML)
    g.create_file(r / "skills" / "kpi-analyzer" / "prompt.txt", SKILL_PKG_KPI_ANALYZER_PROMPT)


def gen_scripts_extra(g: "Generator"):
    """scripts/ — ArkAgent 額外腳本（validate_specs + review_architecture）"""
    r = g.root
    g.create_file(r / "scripts" / "validate_specs.py", VALIDATE_SPECS_PY)
    g.create_file(r / "scripts" / "review_architecture.py", REVIEW_ARCHITECTURE_PY)


def gen_tests_full(g: "Generator"):
    """tests/ — ArkAgent 完整 14 個測試"""
    r = g.root
    g.create_file(r / "tests" / "test_basic.py", TEST_BASIC_PY)
    g.create_file(r / "tests" / "test_skill_registry.py", TEST_SKILL_REGISTRY_PY)
    g.create_file(r / "tests" / "test_skill_resolver.py", TEST_SKILL_RESOLVER_PY)
    g.create_file(r / "tests" / "test_executor.py", TEST_EXECUTOR_PY)
    g.create_file(r / "tests" / "test_kernel.py", TEST_KERNEL_PY)
    g.create_file(r / "tests" / "test_memory.py", TEST_MEMORY_PY)
    g.create_file(r / "tests" / "test_tools.py", TEST_TOOLS_PY)
    g.create_file(r / "tests" / "test_specs.py", TEST_SPECS_PY)
    g.create_file(r / "tests" / "test_domain_controller.py", TEST_DOMAIN_CONTROLLER_PY)
    g.create_file(r / "tests" / "test_system_controller.py", TEST_SYSTEM_CONTROLLER_PY)
    g.create_file(r / "tests" / "test_python_controller.py", TEST_PYTHON_CONTROLLER_PY)
    g.create_file(r / "tests" / "test_mcp_controller.py", TEST_MCP_CONTROLLER_PY)
    g.create_file(r / "tests" / "test_planner.py", TEST_PLANNER_PY)
    g.create_file(r / "tests" / "test_gateway.py", TEST_GATEWAY_PY)


# ═══ Common（所有 profile 共用）═══

def gen_common(g: "Generator"):
    """共用模組：web / data / docs / config files"""
    r = g.root
    config = g.manifest.get("config", {})

    # 設定檔（根據 manifest 選擇模板）
    _config_map = {
        "ENV_EXAMPLE": ENV_EXAMPLE,
        "ARKAGENT_ENV_EXAMPLE": ARKAGENT_ENV_EXAMPLE,
        "REQUIREMENTS_TXT": REQUIREMENTS_TXT,
        "ARKAGENT_REQUIREMENTS_TXT": ARKAGENT_REQUIREMENTS_TXT,
        "LITE_REQUIREMENTS_TXT": LITE_REQUIREMENTS_TXT,
        "START_BAT": START_BAT,
        "ARKAGENT_START_BAT": ARKAGENT_START_BAT,
    }
    env_tpl = config.get("env_template", "ENV_EXAMPLE")
    req_tpl = config.get("requirements_template", "REQUIREMENTS_TXT")
    bat_tpl = config.get("start_bat_template", "START_BAT")

    g.create_file(r / ".env.example", _config_map.get(env_tpl, ENV_EXAMPLE))
    g.create_file(r / "requirements.txt", _config_map.get(req_tpl, REQUIREMENTS_TXT))
    g.create_file(r / "start.bat", _replace_compat(
        _config_map.get(bat_tpl, START_BAT), _compat_dir(g)))

    # scripts/
    g.create_file(r / "scripts" / "init_db.py", INIT_DB_PY)

    # main.py（統一入口）
    g.create_file(r / "main.py", MAIN_PY)

    # web/
    g.create_file(r / "web" / "index.html", _get_index_html())
    g.create_file(r / "web" / "dashboard_hub.html", DASHBOARD_HUB_HTML)

    # data/
    g.create_file(r / "data" / ".gitkeep", "")
    g.create_file(r / "data" / "dashboard" / ".gitkeep", "")
    g.create_file(r / "data" / "dashboard" / "sample" / "revenue.json", SAMPLE_REVENUE_JSON)
    g.create_file(r / "data" / "dashboard" / "sample" / "slots.json", SAMPLE_SLOTS_JSON)
    g.create_file(r / "data" / "dashboard" / "sample" / "fish.json", SAMPLE_FISH_JSON)
    g.create_file(r / "data" / "schedules.json", SCHEDULES_JSON)

    # docs/
    g.create_file(r / "docs" / "bot_test_guide.md", BOT_TEST_GUIDE)


def gen_dashboard_engine(g: "Generator"):
    """src/dashboard_engine/ — 三層架構儀表板引擎（從 assets/ 複製）"""
    r = g.root
    skill_dir = Path(__file__).resolve().parent.parent.parent
    engine_src = skill_dir / "assets" / "dashboard_engine"

    # 複製 engine 核心檔案
    for filename in ["engine.py", "__init__.py"]:
        src_file = engine_src / filename
        if src_file.exists():
            g.create_file(r / "src" / "dashboard_engine" / filename,
                          src_file.read_text(encoding="utf-8"))

    # 複製 assets（base_template.html, dsl_prompt.txt）
    assets_src = engine_src / "assets"
    if assets_src.exists():
        for asset_file in assets_src.iterdir():
            if asset_file.is_file():
                g.create_file(r / "src" / "dashboard_engine" / "assets" / asset_file.name,
                              asset_file.read_text(encoding="utf-8"))


def gen_runtime_adapters(g: "Generator"):
    """src/runtime/ — Runtime Adapter 模組（6 個檔案）"""
    r = g.root
    g.create_file(r / "src" / "runtime" / "__init__.py", RUNTIME_ADAPTER_INIT_PY)
    g.create_file(r / "src" / "runtime" / "base.py", RUNTIME_ADAPTER_BASE_PY)
    g.create_file(r / "src" / "runtime" / "python_adapter.py", PYTHON_ADAPTER_PY)
    g.create_file(r / "src" / "runtime" / "mcp_adapter.py", MCP_ADAPTER_PY)
    g.create_file(r / "src" / "runtime" / "ai_adapter.py", AI_ADAPTER_PY)
    g.create_file(r / "src" / "runtime" / "composite_adapter.py", COMPOSITE_ADAPTER_PY)


def gen_workflow_skills(g: "Generator"):
    """skills/workflows/ — Composite Workflow Skill 範例"""
    r = g.root
    g.create_file(r / "skills" / "workflows" / "daily-report" / "skill.yaml", SKILL_PKG_DAILY_REPORT_YAML)
    g.create_file(r / "skills" / "workflows" / "anomaly-report" / "skill.yaml", SKILL_PKG_ANOMALY_REPORT_YAML)


# ═══ Module Registry ═══

MODULE_REGISTRY: dict[str, callable] = {
    # Lite 模式
    "src_lite":         gen_src_lite,
    "skills_lite":      gen_skills_lite,
    "config_mcp_lite":  gen_config_mcp_lite,
    # Standard（ArkBot）專用
    "src":              gen_src,
    "dashboard_engine": gen_dashboard_engine,
    "runtime_adapters": gen_runtime_adapters,
    "workflow_skills":  gen_workflow_skills,
    "tests_basic":      gen_tests_basic,
    # ArkAgent OS 模組
    "specs":          gen_specs,
    "kernel":         gen_kernel,
    "intent":         gen_intent,
    "runtime":        gen_runtime,
    "memory":         gen_memory,
    "tools":          gen_tools,
    "agents":         gen_agents,
    "entry":          gen_entry,
    "controller":     gen_controller,
    "planner":        gen_planner,
    "api_gateway":    gen_api_gateway,
    "config_mcp":     gen_config_mcp,
    "compat":         gen_compat,
    "skills_yaml":    gen_skills_yaml,
    "scripts_extra":  gen_scripts_extra,
    "tests_full":     gen_tests_full,
}
