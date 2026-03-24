"""Spec DSL 模板 — JSON Schema + 範例 YAML + 驗證腳本"""

# ── skill.schema.json ──
SKILL_SCHEMA_JSON = '''{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ArkAgent Skill Spec",
  "type": "object",
  "required": ["type", "name", "execution"],
  "properties": {
    "type": { "enum": ["skill"] },
    "name": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
    "version": { "type": "string", "pattern": "^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$" },
    "description": { "type": "string" },
    "intent": { "type": "array", "items": { "type": "string" } },
    "examples": { "type": "array", "items": { "type": "string" } },
    "input": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "required": { "type": "boolean" },
          "default": {}
        }
      }
    },
    "output": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "schema": { "type": "object" }
      }
    },
    "execution": {
      "type": "object",
      "required": ["mode", "entry"],
      "properties": {
        "mode": { "enum": ["async", "subprocess"] },
        "entry": { "type": "string" },
        "timeout": { "type": "number", "default": 30 }
      }
    },
    "tags": { "type": "array", "items": { "type": "string" } },
    "priority": { "type": "number", "default": 0 },
    "enabled": { "type": "boolean", "default": true },
    "response_type": { "type": "string", "default": "text" }
  }
}'''

# ── agent.schema.json ──
AGENT_SCHEMA_JSON = '''{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ArkAgent Agent Spec",
  "type": "object",
  "required": ["type", "name", "skills"],
  "properties": {
    "type": { "enum": ["agent"] },
    "name": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
    "version": { "type": "string" },
    "description": { "type": "string" },
    "intents": { "type": "array", "items": { "type": "string" } },
    "skills": { "type": "array", "items": { "type": "string" } },
    "memory": {
      "type": "object",
      "properties": {
        "short_term": {
          "type": "object",
          "properties": {
            "max_turns": { "type": "number", "default": 20 }
          }
        },
        "long_term": {
          "type": "object",
          "properties": {
            "backend": { "type": "string", "default": "sqlite" },
            "path": { "type": "string" }
          }
        }
      }
    },
    "tools": { "type": "array", "items": { "type": "string" } },
    "entry_points": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": { "type": "string" },
          "token_env": { "type": "string" },
          "port_env": { "type": "string" }
        }
      }
    }
  }
}'''

# ── runtime.schema.json ──
RUNTIME_SCHEMA_JSON = '''{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ArkAgent Runtime Spec",
  "type": "object",
  "required": ["type"],
  "properties": {
    "type": { "enum": ["runtime"] },
    "execution": {
      "type": "object",
      "properties": {
        "concurrency": { "type": "number", "default": 10 },
        "default_timeout": { "type": "number", "default": 30 }
      }
    },
    "scheduler": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": false },
        "config": { "type": "string" }
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "api_key_env": { "type": "string" }
      }
    },
    "logging": {
      "type": "object",
      "properties": {
        "level": { "type": "string", "default": "INFO" },
        "format": { "type": "string" }
      }
    }
  }
}'''


# ── 範例 skill.yaml ──
SKILL_EXAMPLE_YAML = '''type: skill
name: web-scraper
version: 1.0.0
description: "爬取指定網頁並產出結構化摘要，支援多種網站格式"
intent:
  - RESEARCH
examples:
  - "幫我爬取這個網頁"
  - "摘要這篇文章"
  - "擷取這個網站的資料"
input:
  url:
    type: string
    required: true
  format:
    type: string
    required: false
    default: markdown
output:
  type: json
  schema:
    summary: string
    content: string
execution:
  mode: subprocess
  entry: skill.py
  timeout: 30
tags:
  - scrape
  - 爬取
  - 網頁
  - 摘要
priority: 80
enabled: true
'''

# ── 範例 agent.yaml ──
AGENT_EXAMPLE_YAML = '''type: agent
name: default-agent
version: 1.0.0
description: "預設 Agent — 智庫助理，支援爬蟲研究、儀表板產生與閒聊"
intents:
  - DASHBOARD
  - DASHBOARD_CANVAS
  - RESEARCH
  - CASUAL
skills:
  - dashboard
  - gemini-canvas
  - crawler
  - chat
memory:
  short_term:
    max_turns: 20
  long_term:
    backend: sqlite
    path: data/memory.db
tools:
  - gemini
  - telegram
entry_points:
  - type: telegram
    token_env: TELEGRAM_TOKEN
  - type: web
    port_env: WEB_PORT
  - type: cli
'''

# ── runtime.yaml ──
RUNTIME_YAML = '''type: runtime
execution:
  concurrency: 10
  default_timeout: 30
scheduler:
  enabled: true
  config: data/schedules.json
security:
  api_key_env: SKILL_API_KEY
logging:
  level: INFO
  format: "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
'''

# ── validate_specs.py 腳本模板 ──
VALIDATE_SPECS_PY = r'''#!/usr/bin/env python3
"""Spec Schema 驗證腳本 — 驗證 specs/ 下的 YAML 是否符合 JSON Schema"""
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ 需要安裝 PyYAML：pip install pyyaml")
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("❌ 需要安裝 jsonschema：pip install jsonschema")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "specs" / "schema"
SPECS_DIR = PROJECT_ROOT / "specs"

# Schema 對應表
SCHEMA_MAP = {
    "skill": "skill.schema.json",
    "agent": "agent.schema.json",
    "runtime": "runtime.schema.json",
}


def load_schema(spec_type: str) -> dict:
    schema_file = SCHEMA_DIR / SCHEMA_MAP[spec_type]
    with open(schema_file, encoding="utf-8") as f:
        return json.load(f)


def validate_file(yaml_path: Path) -> tuple[bool, str]:
    """驗證單一 YAML 檔案，回傳 (通過, 訊息)"""
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        return False, "YAML 內容不是 dict"

    spec_type = data.get("type")
    if spec_type not in SCHEMA_MAP:
        return False, f"未知的 type: {spec_type}（支援：{list(SCHEMA_MAP.keys())}）"

    schema = load_schema(spec_type)
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, "驗證通過"
    except jsonschema.ValidationError as e:
        return False, f"驗證失敗：{e.message}"


def main():
    yaml_files = list(SPECS_DIR.glob("*.yaml")) + list(SPECS_DIR.glob("*.yml"))
    # 也掃描 examples/
    examples_dir = SPECS_DIR / "examples"
    if examples_dir.exists():
        yaml_files += list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
    # 也掃描 agents/
    agents_dir = PROJECT_ROOT / "agents"
    if agents_dir.exists():
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                yaml_files += list(agent_dir.glob("*.yaml"))
    # 也掃描 skills/
    skills_dir = PROJECT_ROOT / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                yaml_files += list(skill_dir.glob("*.yaml"))

    if not yaml_files:
        print("📭 未找到任何 YAML 檔案")
        return

    print(f"📋 驗證 {len(yaml_files)} 個 Spec 檔案\n")
    passed = 0
    failed = 0
    for yf in sorted(yaml_files):
        ok, msg = validate_file(yf)
        status = "✅" if ok else "❌"
        print(f"  {status} {yf.relative_to(PROJECT_ROOT)} — {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'🎉' if failed == 0 else '⚠️'} 結果：{passed} 通過，{failed} 失敗")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
'''


# ── Architecture Reviewer Prompt 模板 ──
ARCH_REVIEWER_PROMPT = '''"""Architecture Reviewer — 架構審查 Prompt + 評分腳本"""

REVIEW_PROMPT = """你是一位 Principal Architect，負責審查 AI Agent 系統架構。

請針對輸入的專案結構與 Spec 進行以下 5 維度分析：

# 1. Layering（層級一致性，0-20 分）
- Factory Layer（技能生成）是否與 Runtime Layer（執行）混用
- 是否有邏輯跨層

# 2. Decoupling（解耦程度，0-20 分）
- Intent Router / Skill Resolver 是否職責重疊
- 是否有 God Object

# 3. Scalability（擴展性，0-20 分）
- 新增 Skill 是否需要修改多處
- 是否有 Plugin / Registry 設計

# 4. Maintainability（可維護性，0-20 分）
- 是否有統一的 Spec Schema
- 是否有版本管理

# 5. Spec Integrity（規格一致性，0-20 分）
- Spec 格式是否統一
- 是否有 Schema 驗證
- 是否有重複或衝突

---

# 輸出格式（JSON）

```json
{
  "scores": {
    "layering": 0,
    "decoupling": 0,
    "scalability": 0,
    "maintainability": 0,
    "spec_integrity": 0,
    "total": 0
  },
  "grade": "Production Ready | Strong | Risky | Needs Redesign",
  "critical_issues": [
    {"issue": "...", "impact": "...", "suggestion": "..."}
  ],
  "warnings": [
    {"issue": "...", "suggestion": "..."}
  ],
  "improvements": [
    {"suggestion": "..."}
  ],
  "summary": "一句話結論"
}
```

Grade 標準：
- 90-100: Production Ready
- 75-89: Strong but improvable
- 60-74: Risky architecture
- <60: Needs redesign
"""
'''

# ── scripts/review_architecture.py 模板 ──
REVIEW_ARCHITECTURE_PY = r'''#!/usr/bin/env python3
"""Architecture Reviewer — 對專案進行架構審查與評分"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REVIEW_PROMPT = """你是一位 Principal Architect，負責審查 AI Agent 系統架構。

請針對以下專案結構進行 5 維度分析（每項 0-20 分，滿分 100）：
1. Layering（層級一致性）
2. Decoupling（解耦程度）
3. Scalability（擴展性）
4. Maintainability（可維護性）
5. Spec Integrity（規格一致性）

只回傳 JSON，格式：
{
  "scores": {"layering": N, "decoupling": N, "scalability": N, "maintainability": N, "spec_integrity": N, "total": N},
  "grade": "Production Ready | Strong | Risky | Needs Redesign",
  "critical_issues": [{"issue": "...", "impact": "...", "suggestion": "..."}],
  "warnings": [{"issue": "...", "suggestion": "..."}],
  "improvements": [{"suggestion": "..."}],
  "summary": "一句話結論"
}

專案結構：
"""


def get_tree(root: Path, max_depth: int = 3) -> str:
    """產生目錄樹字串"""
    lines = []
    def walk(path, prefix, depth):
        if depth > max_depth:
            return
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        for i, entry in enumerate(entries):
            if entry.name.startswith(('.', '__pycache__')):
                continue
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                ext = "    " if i == len(entries) - 1 else "│   "
                walk(entry, prefix + ext, depth + 1)
    walk(root, "", 0)
    return "\n".join(lines)


def review(project_dir: str = None):
    """執行架構審查"""
    root = Path(project_dir) if project_dir else PROJECT_ROOT
    tree = get_tree(root)

    # 收集 Spec 檔案內容
    specs_content = ""
    specs_dir = root / "specs"
    if specs_dir.exists():
        for f in specs_dir.rglob("*.yaml"):
            specs_content += f"\n--- {f.relative_to(root)} ---\n"
            specs_content += f.read_text(encoding="utf-8")[:500]

    prompt = REVIEW_PROMPT + tree + "\n\nSpec 內容：\n" + specs_content

    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    resp = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
    )

    text = resp.text.strip()
    # 提取 JSON
    if "```" in text:
        import re
        match = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    try:
        result = json.loads(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    except json.JSONDecodeError:
        print(text)
        return {"error": "無法解析 JSON", "raw": text}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    review(target)
'''
