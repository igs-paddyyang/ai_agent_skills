#!/usr/bin/env python3
"""Agent Skill 初始化器 — 在 ArkBot/ArkAgent 專案內建立 Skill Package

用法：
    py scripts/init_agent_skill.py <project_path> <skill_id> [--runtime python|mcp|ai|composite]
    py scripts/init_agent_skill.py <project_path> --list

範例：
    py scripts/init_agent_skill.py tiger-bot player-query
    py scripts/init_agent_skill.py tiger-bot revenue-query --runtime mcp
    py scripts/init_agent_skill.py tiger-bot --list
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def detect_compat_dir(project_path: Path) -> str:
    """偵測專案類型：有 compat/ → arkagent，否則 → arkbot（src）"""
    return "compat" if (project_path / "compat").is_dir() else "src"


def to_upper_snake(skill_id: str) -> str:
    """kebab-case → UPPER_SNAKE_CASE"""
    return skill_id.replace("-", "_").upper()


def to_title(skill_id: str) -> str:
    """kebab-case → Title Case"""
    return " ".join(w.capitalize() for w in skill_id.split("-"))


def list_skills(project_path: Path):
    """列出專案內所有 Skills"""
    skills_dir = project_path / "skills"
    if not skills_dir.exists():
        print(f"[ERROR] skills/ 目錄不存在：{skills_dir}")
        return

    skills = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        meta = _load_meta(child)
        if meta:
            skills.append(meta)
        else:
            # 二層子目錄（如 workflows/）
            for grandchild in sorted(child.iterdir()):
                if grandchild.is_dir():
                    meta = _load_meta(grandchild)
                    if meta:
                        skills.append(meta)

    if not skills:
        print("[INFO] 沒有找到任何 Skill")
        return

    # 表格輸出
    print(f"\n{'skill_id':<25} {'runtime':<12} {'intent':<20} {'enabled':<8} {'version'}")
    print("-" * 80)
    for s in skills:
        intent = s.get("intent", "")
        if isinstance(intent, list):
            intent = intent[0] if intent else ""
        print(f"{s.get('skill_id', '?'):<25} {s.get('runtime', 'python'):<12} {intent:<20} {str(s.get('enabled', True)):<8} {s.get('version', '?')}")
    print(f"\n共 {len(skills)} 個 Skill")


def _load_meta(skill_dir: Path) -> dict | None:
    """載入 skill metadata（支援多種路徑）"""
    for yaml_path in [skill_dir / "skill.yaml", skill_dir / "config" / "skill.yaml"]:
        if yaml_path.exists() and HAS_YAML:
            with open(yaml_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
    json_path = skill_dir / "skill.json"
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def create_skill(project_path: Path, skill_id: str, runtime: str = "python",
                 description: str = "", mcp_server: str = "", mcp_tool: str = ""):
    """建立新 Skill Package"""
    compat_dir = detect_compat_dir(project_path)
    intent = to_upper_snake(skill_id)
    title = to_title(skill_id)
    today = date.today().strftime("%Y-%m-%d")

    # 決定目錄位置
    if runtime == "composite":
        skill_dir = project_path / "skills" / "workflows" / skill_id
    else:
        skill_dir = project_path / "skills" / skill_id

    if skill_dir.exists():
        print(f"[ERROR] Skill 目錄已存在：{skill_dir}")
        return None

    # 建立目錄結構
    skill_dir.mkdir(parents=True)
    (skill_dir / "config").mkdir()
    (skill_dir / "references").mkdir()

    if not description:
        description = f"[待完成：說明 {title} 的功能]"

    # 1. config/skill.yaml
    yaml_content = _build_skill_yaml(skill_id, runtime, intent, description, mcp_server, mcp_tool)
    (skill_dir / "config" / "skill.yaml").write_text(yaml_content, encoding="utf-8")
    print(f"  [OK] config/skill.yaml (runtime={runtime})")

    # 2. SKILL.md
    skill_md = _build_skill_md(skill_id, title, description)
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    print(f"  [OK] SKILL.md")

    # 3. README.md
    readme = _build_readme(skill_id, title, today, runtime)
    (skill_dir / "README.md").write_text(readme, encoding="utf-8")
    print(f"  [OK] README.md (v1.0.0)")

    # 4. Runtime-specific files
    if runtime == "python":
        (skill_dir / "scripts").mkdir()
        skill_py = _build_skill_py(skill_id, title, description, compat_dir)
        # 根目錄（向後相容）+ scripts/（新結構）
        (skill_dir / "skill.py").write_text(skill_py, encoding="utf-8")
        (skill_dir / "scripts" / "skill.py").write_text(skill_py, encoding="utf-8")
        print(f"  [OK] skill.py + scripts/skill.py")

    elif runtime == "ai":
        (skill_dir / "assets").mkdir()
        prompt = f"你是 {title} 專家。根據以下資料進行分析：\n\n{{user_input}}\n\n請提供結構化的分析結果。\n"
        (skill_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (skill_dir / "assets" / "prompt.txt").write_text(prompt, encoding="utf-8")
        print(f"  [OK] prompt.txt + assets/prompt.txt")

    print(f"\n[DONE] Skill '{skill_id}' 已建立於 {skill_dir}")
    print(f"\n[NEXT] 後續步驟：")
    print(f"  1. 編輯 config/skill.yaml 完善 description 和 examples")
    print(f"  2. 編輯 SKILL.md 補充技能指令")
    if runtime == "python":
        print(f"  3. 實作 scripts/skill.py 的 run() / run_async()")
    print(f"  4. 執行 py scripts/update_agent_yaml.py {project_path} 更新 agent.yaml")
    if runtime == "mcp":
        print(f"  5. 確認 config/mcp.json 有 '{mcp_server}' server 設定")

    return skill_dir


def _build_skill_yaml(skill_id, runtime, intent, description, mcp_server="", mcp_tool=""):
    lines = [
        f"type: skill",
        f"name: {skill_id}",
        f"version: 1.0.0",
        f"skill_id: {skill_id}",
        f"runtime: {runtime}",
        f"intent:",
        f"  - {intent}",
        f'description: "{description}"',
        f"examples:",
        f'  - "[待完成：觸發範例 1]"',
        f'  - "[待完成：觸發範例 2]"',
    ]
    if runtime == "python":
        lines += ["execution:", "  mode: async", "  entry: skill.py", "  timeout: 30"]
    elif runtime == "mcp":
        lines += [f"mcp:", f"  server: {mcp_server or '[待填入]'}", f"  tool: {mcp_tool or '[待填入]'}", "  param_mapping:", '    query: "{user_input}"']
    elif runtime == "ai":
        lines += ["ai:", "  model: gemini-2.5-flash", "  prompt_file: prompt.txt", "  fallback_skill: chat"]
    elif runtime == "composite":
        lines += ["steps:", "  - skill_id: '[待填入]'", '    input: "{user_input}"', "  - skill_id: '[待填入]'", '    input: "{prev.result}"']
    lines += [f"tags:", f"  - {skill_id.split('-')[0]}", "priority: 5", "enabled: true", "response_type: text"]
    return "\n".join(lines) + "\n"


def _build_skill_md(skill_id, title, description):
    return f"""---
name: {skill_id}
description: "{description}"
---

# {title}

## 概述

{description}

## 使用方式

在 Agent 對話中輸入：
- "[待完成：觸發範例 1]"
- "[待完成：觸發範例 2]"

## 行為說明

[待完成：描述處理邏輯、輸入輸出格式]

## 邊界案例

- 不支援：[待完成]
- 錯誤處理：[待完成]
"""


def _build_readme(skill_id, title, today, runtime):
    return f"""# {title}

> [待完成：一句話描述]

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 1.0.0 |
| 作者 | paddyyang |
| 建立日期 | {today} |
| 最後更新 | {today} |
| Runtime | {runtime} |

## 功能說明

[待完成]

## 檔案結構

```
{skill_id}/
├── SKILL.md
├── README.md
├── config/
│   └── skill.yaml
├── scripts/
├── assets/
└── references/
```

## 變更紀錄

### v1.0.0（{today}）
- 初始版本
"""


def _build_skill_py(skill_id, title, description, compat_dir):
    return f'''"""{title} — {description}"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "{compat_dir}"))
sys.path.insert(0, str(PROJECT_ROOT))


def run(user_input: str) -> str:
    """同步入口"""
    # TODO: 實作
    return f"[{skill_id}] 收到: {{user_input}}"


async def run_async(user_input: str) -> dict:
    """非同步入口"""
    result = run(user_input)
    return {{"success": True, "result": result}}
'''


def main():
    parser = argparse.ArgumentParser(description="Agent Skill 初始化器")
    parser.add_argument("project_path", help="ArkBot/ArkAgent 專案路徑")
    parser.add_argument("skill_id", nargs="?", help="Skill ID（kebab-case）")
    parser.add_argument("--runtime", default="python", choices=["python", "mcp", "ai", "composite"])
    parser.add_argument("--list", action="store_true", help="列出所有 Skills")
    parser.add_argument("--description", default="", help="技能描述")
    parser.add_argument("--mcp-server", default="", help="MCP server name")
    parser.add_argument("--mcp-tool", default="", help="MCP tool name")
    args = parser.parse_args()

    project = Path(args.project_path)
    if not project.exists():
        print(f"[ERROR] 專案路徑不存在：{project}")
        sys.exit(1)

    if args.list:
        list_skills(project)
        return

    if not args.skill_id:
        print("[ERROR] 請提供 skill_id")
        parser.print_help()
        sys.exit(1)

    print(f"\n[INIT] 建立 Agent Skill: {args.skill_id} (runtime={args.runtime})")
    print(f"  專案：{project}")
    print(f"  類型：{detect_compat_dir(project)}\n")

    create_skill(project, args.skill_id, args.runtime, args.description, args.mcp_server, args.mcp_tool)


if __name__ == "__main__":
    main()
