#!/usr/bin/env python3
"""Agent Skill 驗證器 — 檢查 Skill Package 結構與依賴

用法：
    py scripts/validate_agent_skill.py <skill_path>
    py scripts/validate_agent_skill.py tiger-bot/skills/mssql-query

驗證項目：
1. config/skill.yaml 或 skill.yaml 存在且必填欄位完整
2. runtime 對應的額外欄位存在
3. mcp runtime：server 在 config/mcp.json 中存在
4. python runtime：skill.py 存在且有 run() 或 run_async()
5. ai runtime：prompt.txt 存在
6. SKILL.md 存在且有 YAML 前置資料
"""
import re
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REQUIRED_FIELDS = ["skill_id", "intent", "description", "runtime"]
VALID_RUNTIMES = ["python", "mcp", "ai", "composite"]


def validate(skill_path: Path) -> list[str]:
    """驗證 Skill Package，回傳錯誤列表（空 = 通過）"""
    errors = []
    skill_path = Path(skill_path)

    if not skill_path.is_dir():
        return [f"路徑不存在或不是目錄：{skill_path}"]

    # 1. 載入 skill.yaml
    meta = None
    yaml_path = None
    for candidate in [skill_path / "config" / "skill.yaml", skill_path / "skill.yaml"]:
        if candidate.exists():
            yaml_path = candidate
            break

    if not yaml_path:
        errors.append("找不到 config/skill.yaml 或 skill.yaml")
        return errors

    if HAS_YAML:
        with open(yaml_path, encoding="utf-8") as f:
            meta = yaml.safe_load(f)
    else:
        errors.append("pyyaml 未安裝，無法驗證 skill.yaml")
        return errors

    if not isinstance(meta, dict):
        errors.append("skill.yaml 內容不是有效的 YAML dict")
        return errors

    # 2. 必填欄位
    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"缺少必填欄位：{field}")

    # 3. 欄位格式
    skill_id = meta.get("skill_id", "")
    if skill_id and not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", skill_id):
        errors.append(f"skill_id 格式錯誤（需 kebab-case）：{skill_id}")

    runtime = meta.get("runtime", "")
    if runtime and runtime not in VALID_RUNTIMES:
        errors.append(f"runtime 必須是 {VALID_RUNTIMES} 之一，得到：{runtime}")

    desc = meta.get("description", "")
    if desc and len(desc) > 1024:
        errors.append(f"description 過長（{len(desc)} 字元，上限 1024）")

    # 4. Runtime 特定檢查
    if runtime == "python":
        has_entry = (skill_path / "skill.py").exists() or (skill_path / "scripts" / "skill.py").exists()
        if not has_entry:
            errors.append("python runtime 需要 skill.py 或 scripts/skill.py")
        else:
            # 檢查有 run 或 run_async
            entry = skill_path / "skill.py" if (skill_path / "skill.py").exists() else skill_path / "scripts" / "skill.py"
            content = entry.read_text(encoding="utf-8")
            if "def run(" not in content and "async def run_async(" not in content:
                errors.append("skill.py 缺少 run() 或 run_async() 函式")

    elif runtime == "mcp":
        mcp = meta.get("mcp", {})
        if not mcp.get("server"):
            errors.append("mcp runtime 缺少 mcp.server 欄位")
        if not mcp.get("tool"):
            errors.append("mcp runtime 缺少 mcp.tool 欄位")
        # 檢查 mcp.json
        server_name = mcp.get("server", "")
        if server_name:
            project_root = _find_project_root(skill_path)
            if project_root:
                mcp_json = project_root / "config" / "mcp.json"
                if mcp_json.exists():
                    import json
                    with open(mcp_json, encoding="utf-8") as f:
                        mcp_config = json.load(f).get("mcpServers", {})
                    if server_name not in mcp_config:
                        errors.append(f"mcp.server '{server_name}' 不在 config/mcp.json 中")
                    elif mcp_config[server_name].get("disabled"):
                        errors.append(f"mcp.server '{server_name}' 在 config/mcp.json 中已 disabled")

    elif runtime == "ai":
        has_prompt = (skill_path / "prompt.txt").exists() or (skill_path / "assets" / "prompt.txt").exists()
        if not has_prompt:
            errors.append("ai runtime 需要 prompt.txt 或 assets/prompt.txt")

    elif runtime == "composite":
        steps = meta.get("steps", [])
        if not steps:
            # 也檢查 composite.steps（舊格式）
            steps = meta.get("composite", {}).get("steps", [])
        if not steps:
            errors.append("composite runtime 缺少 steps 欄位")

    # 5. SKILL.md 檢查（建議但非必要）
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append("SKILL.md 缺少 YAML 前置資料")

    return errors


def _find_project_root(skill_path: Path) -> Path | None:
    """從 skill 路徑往上找專案根目錄（有 config/ 的目錄）"""
    current = skill_path.parent
    for _ in range(5):
        if (current / "config").is_dir():
            return current
        current = current.parent
    return None


def main():
    if len(sys.argv) != 2:
        print("用法：py scripts/validate_agent_skill.py <skill_path>")
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    errors = validate(skill_path)

    if errors:
        print(f"\n[FAIL] {skill_path.name} 驗證失敗（{len(errors)} 個問題）：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"\n[PASS] {skill_path.name} 驗證通過")
        sys.exit(0)


if __name__ == "__main__":
    main()
