"""測試模板 — TEST_BASIC_PY, TEST_SKILL_REGISTRY_PY, TEST_SKILL_RESOLVER_PY, TEST_EXECUTOR_PY"""

# tests/test_basic.py 模板
TEST_BASIC_PY = '''"""ArkBot 基礎功能驗證"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_escape_markdown_v2():
    from format_utils import escape_markdown_v2
    result = escape_markdown_v2("Hello (world) v1.0!")
    assert "\\\\(" in result
    assert "\\\\." in result
    assert "\\\\!" in result
    print("✅ escape_markdown_v2 測試通過")


def test_db_init():
    import sqlite3
    import tempfile
    db_path = os.path.join(tempfile.gettempdir(), "test_brain.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_crawls (
            url TEXT UNIQUE NOT NULL,
            content_md TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO raw_crawls (url, content_md) VALUES (?, ?)", ("https://test.com", "# Test"))
    try:
        conn.execute("INSERT INTO raw_crawls (url, content_md) VALUES (?, ?)", ("https://test.com", "# Dup"))
        assert False, "UNIQUE 約束應該阻止重複插入"
    except sqlite3.IntegrityError:
        pass
    conn.close()
    os.remove(db_path)
    print("✅ 資料庫 UNIQUE 約束測試通過")


if __name__ == "__main__":
    test_escape_markdown_v2()
    test_db_init()
    print("\\n🎉 所有基礎測試通過！")
'''


# tests/test_skill_registry.py 模板
TEST_SKILL_REGISTRY_PY = '''"""Skill Registry 測試"""
import sys
import os
import json
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_registry import SkillRegistry


def _create_skill(base_dir, skill_id, intent="RESEARCH", enabled=True, extra=None):
    """建立測試用 skill.json"""
    skill_dir = os.path.join(base_dir, skill_id)
    os.makedirs(skill_dir, exist_ok=True)
    meta = {
        "skill_id": skill_id,
        "intent": intent,
        "description": f"Test skill {skill_id}",
        "examples": [f"test {skill_id}"],
        "required_params": ["query"],
        "tags": [skill_id],
        "priority": 50,
        "enabled": enabled,
    }
    if extra:
        meta.update(extra)
    with open(os.path.join(skill_dir, "skill.json"), "w") as f:
        json.dump(meta, f)


def test_load_skills():
    tmp = tempfile.mkdtemp()
    try:
        _create_skill(tmp, "skill_a", "RESEARCH")
        _create_skill(tmp, "skill_b", "RESEARCH")
        _create_skill(tmp, "skill_c", "DASHBOARD")

        reg = SkillRegistry(tmp)
        assert len(reg.skills) == 3
        print("✅ 載入 3 個 skill.json 通過")
    finally:
        shutil.rmtree(tmp)


def test_filter_by_intent():
    tmp = tempfile.mkdtemp()
    try:
        _create_skill(tmp, "res_a", "RESEARCH")
        _create_skill(tmp, "res_b", "RESEARCH")
        _create_skill(tmp, "dash_a", "DASHBOARD")

        reg = SkillRegistry(tmp)
        research = reg.filter_by_intent("RESEARCH")
        assert len(research) == 2
        print("✅ filter_by_intent 通過")
    finally:
        shutil.rmtree(tmp)


def test_enabled_filter():
    tmp = tempfile.mkdtemp()
    try:
        _create_skill(tmp, "active", "RESEARCH", enabled=True)
        _create_skill(tmp, "disabled", "RESEARCH", enabled=False)

        reg = SkillRegistry(tmp)
        research = reg.filter_by_intent("RESEARCH")
        assert len(research) == 1
        assert research[0]["skill_id"] == "active"
        print("✅ enabled 過濾通過")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_load_skills()
    test_filter_by_intent()
    test_enabled_filter()
    print("\\n🎉 Skill Registry 所有測試通過！")
'''


# tests/test_skill_resolver.py 模板
TEST_SKILL_RESOLVER_PY = '''"""Skill Resolver 測試"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_registry import SkillRegistry
from skill_resolver import SkillResolver


def _make_candidates():
    return [
        {"skill_id": "web_scraper", "intent": "RESEARCH", "description": "網頁爬取",
         "examples": ["爬取網頁"], "required_params": ["url"],
         "tags": ["scraper", "crawl", "爬取"], "priority": 80, "enabled": True},
        {"skill_id": "knowledge_qa", "intent": "RESEARCH", "description": "知識問答",
         "examples": ["查詢知識"], "required_params": ["query"],
         "tags": ["知識", "查詢"], "priority": 60, "enabled": True},
    ]


def test_rule_match_hit():
    reg = SkillRegistry()
    resolver = SkillResolver(reg)
    candidates = _make_candidates()
    result = resolver._rule_match("幫我爬取這個網頁", candidates)
    assert result is not None
    assert result["skill_id"] == "web_scraper"
    print("✅ Rule Match 命中通過")


def test_rule_match_miss():
    reg = SkillRegistry()
    resolver = SkillResolver(reg)
    candidates = _make_candidates()
    result = resolver._rule_match("分析活動影響", candidates)
    assert result is None
    print("✅ Rule Match 未命中通過")


def test_fallback():
    reg = SkillRegistry()
    for c in _make_candidates():
        reg.skills[c["skill_id"]] = c

    resolver = SkillResolver(reg, llm_client=None)
    result = asyncio.run(resolver.resolve("一些模糊的輸入", "RESEARCH"))
    assert result is not None
    assert result["method"] == "fallback"
    assert result["skill_id"] == "web_scraper"  # priority 80 > 60
    print("✅ Fallback 通過")


if __name__ == "__main__":
    test_rule_match_hit()
    test_rule_match_miss()
    test_fallback()
    print("\\n🎉 Skill Resolver 所有測試通過！")
'''


# tests/test_executor.py 模板
TEST_EXECUTOR_PY = '''"""Executor 測試"""
import sys
import os
import json
import asyncio
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_registry import SkillRegistry
from executor import Executor


def _setup_skill(base_dir, skill_id, code):
    """建立測試用 Skill（skill.json + skill.py）"""
    skill_dir = os.path.join(base_dir, skill_id)
    os.makedirs(skill_dir, exist_ok=True)
    meta = {
        "skill_id": skill_id,
        "intent": "RESEARCH",
        "description": f"Test {skill_id}",
        "examples": ["test"],
        "required_params": [],
    }
    with open(os.path.join(skill_dir, "skill.json"), "w") as f:
        json.dump(meta, f)
    with open(os.path.join(skill_dir, "skill.py"), "w") as f:
        f.write(code)


def test_execute_success():
    tmp = tempfile.mkdtemp()
    try:
        _setup_skill(tmp, "echo_skill", """
def run(user_input):
    return f"Echo: {user_input}"
""")
        reg = SkillRegistry(tmp)
        exe = Executor(reg, tmp)
        result = asyncio.run(exe.execute("echo_skill", "hello"))
        assert result["success"] is True
        assert "hello" in result["result"]
        print("✅ Executor 正常執行通過")
    finally:
        shutil.rmtree(tmp)


def test_execute_error():
    tmp = tempfile.mkdtemp()
    try:
        _setup_skill(tmp, "bad_skill", """
def run(user_input):
    raise ValueError("故意拋出錯誤")
""")
        reg = SkillRegistry(tmp)
        exe = Executor(reg, tmp)
        result = asyncio.run(exe.execute("bad_skill", "test"))
        assert result["success"] is False
        print("✅ Sandbox 隔離通過（錯誤被捕獲）")
    finally:
        shutil.rmtree(tmp)


def test_execute_no_skill():
    reg = SkillRegistry()
    exe = Executor(reg, "/nonexistent")
    result = asyncio.run(exe.execute("missing_skill", "test"))
    assert result["success"] is False
    assert "skill-creator" in result["error"]
    print("✅ 無 Skill 提示通過")


if __name__ == "__main__":
    test_execute_success()
    test_execute_error()
    test_execute_no_skill()
    print("\\n🎉 Executor 所有測試通過！")
'''


# ═══ ArkAgent OS 新增測試模板 ═══

# tests/test_kernel.py 模板
TEST_KERNEL_PY = '''"""Agent Kernel 測試"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kernel.agent_base import AgentBase
from pathlib import Path


def test_agent_lifecycle():
    """測試 Agent lifecycle hooks"""
    events = []

    class TestAgent(AgentBase):
        async def on_start(self):
            events.append("start")
        async def on_message(self, user_input):
            events.append(f"msg:{user_input}")
            return {"type": "reply", "content": f"echo: {user_input}"}
        async def on_stop(self):
            events.append("stop")

    config = {"name": "test-agent", "skills": ["chat"]}
    agent = TestAgent(config, Path("."))

    async def run():
        await agent.start()
        result = await agent.handle_message("hello")
        await agent.stop()
        return result

    result = asyncio.run(run())
    assert events == ["start", "msg:hello", "stop"]
    assert result["content"] == "echo: hello"
    print("✅ Agent lifecycle 測試通過")


def test_agent_not_started():
    """測試未啟動的 Agent"""
    config = {"name": "test-agent"}
    agent = AgentBase(config, Path("."))
    result = asyncio.run(agent.handle_message("hello"))
    assert result["type"] == "error"
    print("✅ Agent 未啟動錯誤處理通過")


if __name__ == "__main__":
    test_agent_lifecycle()
    test_agent_not_started()
    print("\\n🎉 Agent Kernel 所有測試通過！")
'''

# tests/test_memory.py 模板
TEST_MEMORY_PY = '''"""Memory System 測試"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory


def test_short_term_max_turns():
    """測試短期記憶 max_turns 限制"""
    mem = ShortTermMemory(max_turns=3)
    for i in range(5):
        mem.add("user", f"msg-{i}")
    history = mem.get_history()
    assert len(history) == 3
    assert history[0]["content"] == "msg-2"
    assert history[-1]["content"] == "msg-4"
    print("✅ ShortTermMemory max_turns 測試通過")


def test_short_term_context_string():
    """測試對話歷史格式化"""
    mem = ShortTermMemory()
    mem.add("user", "你好")
    mem.add("assistant", "嗨！")
    ctx = mem.get_context_string()
    assert "使用者：你好" in ctx
    assert "助理：嗨！" in ctx
    print("✅ ShortTermMemory context_string 測試通過")


def test_long_term_crud():
    """測試長期記憶 CRUD"""
    db_path = os.path.join(tempfile.gettempdir(), "test_memory.db")
    try:
        mem = LongTermMemory(db_path)
        # Create
        mid = mem.store("測試記憶", agent_name="test")
        assert mid > 0
        # Read
        results = mem.search("測試", agent_name="test")
        assert len(results) >= 1
        # Count
        assert mem.count(agent_name="test") >= 1
        # Delete
        assert mem.delete(mid) is True
        assert mem.count(agent_name="test") == 0
        print("✅ LongTermMemory CRUD 測試通過")
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_long_term_persistence():
    """測試長期記憶持久化"""
    db_path = os.path.join(tempfile.gettempdir(), "test_persist.db")
    try:
        mem1 = LongTermMemory(db_path)
        mem1.store("持久化測試", agent_name="test")
        # 重新建立實例（模擬重啟）
        mem2 = LongTermMemory(db_path)
        results = mem2.search("持久化", agent_name="test")
        assert len(results) >= 1
        print("✅ LongTermMemory 持久化測試通過")
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    test_short_term_max_turns()
    test_short_term_context_string()
    test_long_term_crud()
    test_long_term_persistence()
    print("\\n🎉 Memory System 所有測試通過！")
'''

# tests/test_tools.py 模板
TEST_TOOLS_PY = '''"""Tool Gateway 測試"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.gateway import BaseTool, ToolGateway


class MockTool(BaseTool):
    name = "mock"
    description = "測試用 mock 工具"

    async def call(self, **kwargs):
        return {"echo": kwargs}

    async def health_check(self):
        return True


def test_register_and_call():
    """測試工具註冊與呼叫"""
    gw = ToolGateway()
    gw.register(MockTool())

    result = asyncio.run(gw.call("mock", message="hello"))
    assert result["echo"]["message"] == "hello"
    print("✅ ToolGateway register + call 測試通過")


def test_list_tools():
    """測試列出工具"""
    gw = ToolGateway()
    gw.register(MockTool())
    tools = gw.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "mock"
    print("✅ ToolGateway list_tools 測試通過")


def test_unregister():
    """測試取消註冊"""
    gw = ToolGateway()
    gw.register(MockTool())
    assert gw.unregister("mock") is True
    assert gw.unregister("mock") is False
    assert len(gw.list_tools()) == 0
    print("✅ ToolGateway unregister 測試通過")


def test_call_unknown_tool():
    """測試呼叫未註冊工具"""
    gw = ToolGateway()
    try:
        asyncio.run(gw.call("nonexistent"))
        assert False, "應該拋出 ValueError"
    except ValueError as e:
        assert "nonexistent" in str(e)
    print("✅ ToolGateway 未知工具錯誤處理通過")


def test_health_check():
    """測試健康檢查"""
    gw = ToolGateway()
    gw.register(MockTool())
    results = asyncio.run(gw.health_check_all())
    assert results["mock"] is True
    print("✅ ToolGateway health_check 測試通過")


if __name__ == "__main__":
    test_register_and_call()
    test_list_tools()
    test_unregister()
    test_call_unknown_tool()
    test_health_check()
    print("\\n🎉 Tool Gateway 所有測試通過！")
'''

# tests/test_specs.py 模板
TEST_SPECS_PY = '''"""Spec DSL 測試"""
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kernel.spec_loader import load_spec, validate_schema, SpecValidationError

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def test_load_yaml():
    """測試 YAML 載入"""
    if not HAS_YAML:
        print("⏭️ PyYAML 未安裝，跳過")
        return
    tmp = tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False, encoding="utf-8")
    try:
        yaml.dump({"type": "skill", "name": "test", "execution": {"mode": "subprocess", "entry": "skill.py"}}, tmp)
        tmp.close()
        from pathlib import Path
        data = load_spec(Path(tmp.name))
        assert data["type"] == "skill"
        assert data["name"] == "test"
        print("✅ YAML 載入測試通過")
    finally:
        os.unlink(tmp.name)


def test_load_json():
    """測試 JSON 載入"""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8")
    try:
        json.dump({"type": "skill", "name": "test", "execution": {"mode": "async", "entry": "skill.py"}}, tmp)
        tmp.close()
        from pathlib import Path
        data = load_spec(Path(tmp.name))
        assert data["type"] == "skill"
        print("✅ JSON 載入測試通過")
    finally:
        os.unlink(tmp.name)


def test_schema_validation():
    """測試 Schema 驗證"""
    if not HAS_JSONSCHEMA:
        print("⏭️ jsonschema 未安裝，跳過")
        return
    from pathlib import Path
    schema_dir = Path(__file__).resolve().parent.parent / "specs" / "schema"
    if not schema_dir.exists():
        print("⏭️ Schema 目錄不存在，跳過")
        return

    # 合規資料
    valid = {"type": "skill", "name": "test-skill", "execution": {"mode": "subprocess", "entry": "skill.py"}}
    ok, msg = validate_schema(valid, schema_dir)
    assert ok, f"合規資料應通過：{msg}"
    print("✅ Schema 驗證（合規）通過")

    # 不合規資料（缺 name）
    invalid = {"type": "skill", "execution": {"mode": "subprocess", "entry": "skill.py"}}
    ok, msg = validate_schema(invalid, schema_dir)
    assert not ok
    print("✅ Schema 驗證（不合規）通過")


if __name__ == "__main__":
    test_load_yaml()
    test_load_json()
    test_schema_validation()
    print("\\n🎉 Spec DSL 所有測試通過！")
'''


# ═══ 平台級架構新增測試模板 ═══

# tests/test_domain_controller.py 模板
TEST_DOMAIN_CONTROLLER_PY = '''"""Domain Controller 路由測試"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from controller.domain_controller import DomainController


def test_route_to_system():
    """測試 Action 路由到 SystemController"""
    dc = DomainController(os.path.dirname(os.path.dirname(__file__)))
    action = {
        "type": "action",
        "controller": "system",
        "action": "scheduler.list",
        "params": {},
    }
    result = asyncio.run(dc.execute(action))
    assert result["success"] is True
    print("✅ 路由到 SystemController 通過")


def test_route_to_python():
    """測試 Action 路由到 PythonController"""
    dc = DomainController(os.path.dirname(os.path.dirname(__file__)))
    action = {
        "type": "action",
        "controller": "python",
        "action": "run_script",
        "params": {"script": "../../etc/passwd"},
    }
    result = asyncio.run(dc.execute(action))
    assert result["success"] is False  # 應被白名單拒絕
    print("✅ PythonController 白名單拒絕通過")


def test_route_to_mcp():
    """測試 Action 路由到 MCPController"""
    dc = DomainController(os.path.dirname(os.path.dirname(__file__)))
    action = {
        "type": "action",
        "controller": "mcp",
        "action": "list_tools",
        "params": {},
    }
    result = asyncio.run(dc.execute(action))
    assert result["success"] is True
    print("✅ 路由到 MCPController 通過")


def test_unknown_controller():
    """測試未知 Controller"""
    dc = DomainController(os.path.dirname(os.path.dirname(__file__)))
    action = {
        "type": "action",
        "controller": "unknown",
        "action": "test",
        "params": {},
    }
    result = asyncio.run(dc.execute(action))
    assert result["success"] is False
    assert "未知" in result["error"]
    print("✅ 未知 Controller 錯誤處理通過")


def test_is_action():
    """測試 Action 格式判斷"""
    dc = DomainController(os.path.dirname(os.path.dirname(__file__)))
    assert dc.is_action({"type": "action", "controller": "system", "action": "test"}) is True
    assert dc.is_action({"type": "reply", "content": "hello"}) is False
    assert dc.is_action("plain text") is False
    print("✅ is_action 判斷通過")


def test_missing_controller_field():
    """測試缺少 controller 欄位"""
    dc = DomainController(os.path.dirname(os.path.dirname(__file__)))
    action = {"type": "action", "action": "test", "params": {}}
    result = asyncio.run(dc.execute(action))
    assert result["success"] is False
    print("✅ 缺少 controller 欄位錯誤處理通過")


if __name__ == "__main__":
    test_route_to_system()
    test_route_to_python()
    test_route_to_mcp()
    test_unknown_controller()
    test_is_action()
    test_missing_controller_field()
    print("\\n🎉 Domain Controller 所有測試通過！")
'''

# tests/test_system_controller.py 模板
TEST_SYSTEM_CONTROLLER_PY = '''"""System Controller 測試"""
import sys
import os
import json
import asyncio
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from controller.system_controller import SystemController


def _make_controller():
    """建立測試用 SystemController"""
    tmp = tempfile.mkdtemp()
    data_dir = os.path.join(tmp, "data")
    os.makedirs(data_dir, exist_ok=True)
    # 初始化空排程
    with open(os.path.join(data_dir, "schedules.json"), "w") as f:
        json.dump({"schedules": []}, f)
    ctrl = SystemController(tmp)
    return ctrl, tmp


def test_scheduler_add_and_list():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("scheduler.add", {
            "id": "test-1", "skill_id": "dashboard", "cron": "0 9 * * *",
        }))
        assert result["success"] is True

        result = asyncio.run(ctrl.execute("scheduler.list", {}))
        assert result["success"] is True
        assert len(result["result"]) == 1
        assert result["result"][0]["id"] == "test-1"
        print("✅ scheduler.add + list 通過")
    finally:
        shutil.rmtree(tmp)


def test_scheduler_remove():
    ctrl, tmp = _make_controller()
    try:
        asyncio.run(ctrl.execute("scheduler.add", {
            "id": "rm-1", "skill_id": "chat", "cron": "0 * * * *",
        }))
        result = asyncio.run(ctrl.execute("scheduler.remove", {"schedule_id": "rm-1"}))
        assert result["success"] is True

        result = asyncio.run(ctrl.execute("scheduler.list", {}))
        assert len(result["result"]) == 0
        print("✅ scheduler.remove 通過")
    finally:
        shutil.rmtree(tmp)


def test_scheduler_toggle():
    ctrl, tmp = _make_controller()
    try:
        asyncio.run(ctrl.execute("scheduler.add", {
            "id": "tog-1", "skill_id": "chat", "cron": "0 * * * *",
        }))
        result = asyncio.run(ctrl.execute("scheduler.toggle", {"schedule_id": "tog-1", "enabled": False}))
        assert result["success"] is True
        assert "停用" in result["result"]
        print("✅ scheduler.toggle 通過")
    finally:
        shutil.rmtree(tmp)


def test_admin_status():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("admin.status", {}))
        assert result["success"] is True
        assert "uptime_seconds" in result["result"]
        assert "scheduler_count" in result["result"]
        print("✅ admin.status 通過")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_scheduler_add_and_list()
    test_scheduler_remove()
    test_scheduler_toggle()
    test_admin_status()
    print("\\n🎉 System Controller 所有測試通過！")
'''

# tests/test_python_controller.py 模板
TEST_PYTHON_CONTROLLER_PY = '''"""Python Controller 測試"""
import sys
import os
import asyncio
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from controller.python_controller import PythonController


def _make_controller():
    tmp = tempfile.mkdtemp()
    scripts_dir = os.path.join(tmp, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    # 建立測試腳本
    with open(os.path.join(scripts_dir, "hello.py"), "w") as f:
        f.write("print('Hello from script')")
    with open(os.path.join(scripts_dir, "add.py"), "w") as f:
        f.write("def add(a, b):\\n    return a + b")
    ctrl = PythonController(tmp)
    return ctrl, tmp


def test_run_script():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("run_script", {"script": "scripts/hello.py"}))
        assert result["success"] is True
        assert "Hello" in result["result"]
        print("✅ run_script 通過")
    finally:
        shutil.rmtree(tmp)


def test_whitelist_block():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("run_script", {"script": "../../etc/passwd"}))
        assert result["success"] is False
        print("✅ 白名單阻擋通過")
    finally:
        shutil.rmtree(tmp)


def test_run_function():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("run_function", {
            "module": "scripts/add.py",
            "function": "add",
            "args": [1, 2],
        }))
        assert result["success"] is True
        assert "3" in result["result"]
        print("✅ run_function 通過")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_run_script()
    test_whitelist_block()
    test_run_function()
    print("\\n🎉 Python Controller 所有測試通過！")
'''

# tests/test_mcp_controller.py 模板
TEST_MCP_CONTROLLER_PY = '''"""MCP Controller 測試"""
import sys
import os
import json
import asyncio
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from controller.mcp_controller import MCPController


def _make_controller():
    tmp = tempfile.mkdtemp()
    config_dir = os.path.join(tmp, "config")
    os.makedirs(config_dir, exist_ok=True)
    config = {
        "mcpServers": {
            "test-server": {
                "command": "echo",
                "args": ["test"],
                "disabled": False,
            }
        }
    }
    with open(os.path.join(config_dir, "mcp.json"), "w") as f:
        json.dump(config, f)
    ctrl = MCPController(tmp)
    return ctrl, tmp


def test_load_config():
    ctrl, tmp = _make_controller()
    try:
        assert "test-server" in ctrl.servers
        print("✅ MCP 設定載入通過")
    finally:
        shutil.rmtree(tmp)


def test_list_tools():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("list_tools", {}))
        assert result["success"] is True
        assert "test-server" in result["result"]
        print("✅ list_tools 通過")
    finally:
        shutil.rmtree(tmp)


def test_call_tool_not_connected():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("call_tool", {
            "server": "test-server",
            "tool": "some_tool",
        }))
        assert result["success"] is False
        assert "尚未連接" in result["error"]
        print("✅ 未連接時友善錯誤通過")
    finally:
        shutil.rmtree(tmp)


def test_call_tool_unknown_server():
    ctrl, tmp = _make_controller()
    try:
        result = asyncio.run(ctrl.execute("call_tool", {
            "server": "nonexistent",
            "tool": "test",
        }))
        assert result["success"] is False
        print("✅ 未知 Server 錯誤處理通過")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_load_config()
    test_list_tools()
    test_call_tool_not_connected()
    test_call_tool_unknown_server()
    print("\\n🎉 MCP Controller 所有測試通過！")
'''

# tests/test_planner.py 模板
TEST_PLANNER_PY = '''"""Skill Planner 測試"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from planner.execution_plan import ExecutionPlan, PlanStep


def test_simple_plan():
    """測試簡單 Plan"""
    plan = ExecutionPlan.simple("chat", "你好")
    assert plan.is_simple is True
    assert len(plan.steps) == 1
    assert plan.steps[0].skill_id == "chat"
    print("✅ 簡單 Plan 建立通過")


def test_from_dict():
    """測試從 dict 建立 Plan"""
    data = {
        "steps": [
            {"step": 1, "skill_id": "dashboard", "input": "產生儀表板"},
            {"step": 2, "controller": "system", "action": "scheduler.add",
             "params": {"id": "daily", "skill_id": "dashboard", "cron": "0 9 * * *"},
             "depends_on": [1]},
        ],
        "strategy": "sequential",
    }
    plan = ExecutionPlan.from_dict(data)
    assert len(plan.steps) == 2
    assert plan.strategy == "sequential"
    assert plan.steps[1].depends_on == [1]
    print("✅ from_dict 建立通過")


def test_get_ready_steps():
    """測試取得可執行步驟"""
    data = {
        "steps": [
            {"step": 1, "skill_id": "dashboard", "input": "test"},
            {"step": 2, "controller": "system", "action": "test", "depends_on": [1]},
            {"step": 3, "skill_id": "chat", "input": "test"},
        ],
    }
    plan = ExecutionPlan.from_dict(data)

    # 初始：step 1 和 3 可執行（無依賴）
    ready = plan.get_ready_steps(set())
    step_nums = [s.step for s in ready]
    assert 1 in step_nums
    assert 3 in step_nums
    assert 2 not in step_nums

    # step 1 完成後：step 2 可執行
    ready = plan.get_ready_steps({1, 3})
    assert len(ready) == 1
    assert ready[0].step == 2
    print("✅ get_ready_steps DAG 依賴通過")


if __name__ == "__main__":
    test_simple_plan()
    test_from_dict()
    test_get_ready_steps()
    print("\\n🎉 Skill Planner 所有測試通過！")
'''

# tests/test_gateway.py 模板
TEST_GATEWAY_PY = '''"""API Gateway 測試"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Gateway 測試需要 FastAPI TestClient
try:
    from fastapi.testclient import TestClient
    HAS_TESTCLIENT = True
except ImportError:
    HAS_TESTCLIENT = False


def test_auth_no_key():
    """測試無 API Key 呼叫 /api/ 路徑"""
    if not HAS_TESTCLIENT:
        print("⏭️ FastAPI TestClient 未安裝，跳過")
        return
    # 設定環境變數
    os.environ["SKILL_API_KEY"] = "test-key-123"
    try:
        from gateway.app import create_app
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/skills")
        assert resp.status_code == 401
        print("✅ 無 API Key → 401 通過")
    except ImportError:
        print("⏭️ Gateway 模組未安裝，跳過")
    finally:
        os.environ.pop("SKILL_API_KEY", None)


def test_auth_valid_key():
    """測試有效 API Key"""
    if not HAS_TESTCLIENT:
        print("⏭️ FastAPI TestClient 未安裝，跳過")
        return
    os.environ["SKILL_API_KEY"] = "test-key-123"
    try:
        from gateway.app import create_app
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/skills", headers={"x-api-key": "test-key-123"})
        assert resp.status_code == 200
        print("✅ 有效 API Key → 200 通過")
    except ImportError:
        print("⏭️ Gateway 模組未安裝，跳過")
    finally:
        os.environ.pop("SKILL_API_KEY", None)


def test_health_endpoint():
    """測試 /health 端點"""
    if not HAS_TESTCLIENT:
        print("⏭️ FastAPI TestClient 未安裝，跳過")
        return
    try:
        from gateway.app import create_app
        app = create_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print("✅ /health 端點通過")
    except ImportError:
        print("⏭️ Gateway 模組未安裝，跳過")


if __name__ == "__main__":
    test_auth_no_key()
    test_auth_valid_key()
    test_health_endpoint()
    print("\\n🎉 API Gateway 所有測試通過！")
'''
