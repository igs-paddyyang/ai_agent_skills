#!/usr/bin/env python3
"""Agent YAML 更新器 — 掃描 skills/ 自動更新 agent.yaml 的 intents + skills

用法：
    py scripts/update_agent_yaml.py <project_path>
    py scripts/update_agent_yaml.py tiger-bot
"""
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def scan_skills(project_path: Path) -> tuple[list[str], list[str]]:
    """掃描 skills/ 目錄，回傳 (intents, skill_ids)"""
    skills_dir = project_path / "skills"
    if not skills_dir.exists():
        return [], []

    intents = []
    skill_ids = []

    def _process_dir(d: Path):
        for candidate in [d / "config" / "skill.yaml", d / "skill.yaml"]:
            if candidate.exists() and HAS_YAML:
                with open(candidate, encoding="utf-8") as f:
                    meta = yaml.safe_load(f)
                if not isinstance(meta, dict):
                    continue
                if not meta.get("enabled", True):
                    continue
                sid = meta.get("skill_id", "")
                if sid:
                    skill_ids.append(sid)
                intent_val = meta.get("intent", [])
                if isinstance(intent_val, list):
                    intents.extend(intent_val)
                elif intent_val:
                    intents.append(intent_val)
                return

    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "skill.yaml").exists() or (child / "config" / "skill.yaml").exists():
            _process_dir(child)
        else:
            for grandchild in sorted(child.iterdir()):
                if grandchild.is_dir():
                    _process_dir(grandchild)

    return intents, skill_ids


def update_agent_yaml(project_path: Path):
    """更新 agents/default/agent.yaml"""
    if not HAS_YAML:
        print("[ERROR] pyyaml 未安裝")
        sys.exit(1)

    agent_yaml = project_path / "agents" / "default" / "agent.yaml"
    if not agent_yaml.exists():
        print(f"[ERROR] agent.yaml 不存在：{agent_yaml}")
        sys.exit(1)

    with open(agent_yaml, encoding="utf-8") as f:
        agent = yaml.safe_load(f)

    old_intents = set(agent.get("intents", []))
    old_skills = set(agent.get("skills", []))

    new_intents, new_skills = scan_skills(project_path)
    new_intents_set = set(new_intents)
    new_skills_set = set(new_skills)

    # Diff
    added_intents = new_intents_set - old_intents
    removed_intents = old_intents - new_intents_set
    added_skills = new_skills_set - old_skills
    removed_skills = old_skills - new_skills_set

    if not added_intents and not removed_intents and not added_skills and not removed_skills:
        print("[OK] agent.yaml 已是最新，無需更新")
        return

    # 更新
    agent["intents"] = sorted(new_intents_set)
    agent["skills"] = sorted(new_skills_set)

    with open(agent_yaml, "w", encoding="utf-8") as f:
        yaml.dump(agent, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[OK] agent.yaml 已更新")
    if added_intents:
        print(f"  + intents: {', '.join(sorted(added_intents))}")
    if removed_intents:
        print(f"  - intents: {', '.join(sorted(removed_intents))}")
    if added_skills:
        print(f"  + skills: {', '.join(sorted(added_skills))}")
    if removed_skills:
        print(f"  - skills: {', '.join(sorted(removed_skills))}")


def main():
    if len(sys.argv) != 2:
        print("用法：py scripts/update_agent_yaml.py <project_path>")
        sys.exit(1)

    project = Path(sys.argv[1])
    if not project.exists():
        print(f"[ERROR] 專案路徑不存在：{project}")
        sys.exit(1)

    update_agent_yaml(project)


if __name__ == "__main__":
    main()
