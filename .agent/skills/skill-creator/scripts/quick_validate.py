#!/usr/bin/env python3
"""
技能快速驗證腳本 — 整合版

合併官方版的屬性白名單檢查與社群版的 yaml fallback。

用法：
    python scripts/quick_validate.py <skill_directory>

範例：
    python scripts/quick_validate.py .kiro/skills/my-skill
"""

import sys
import re
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# 允許的前置資料屬性（來自官方版）
ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}


def validate_skill(skill_path):
    """驗證技能結構與內容。"""
    skill_path = Path(skill_path)

    # 檢查 SKILL.md 是否存在
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "❌ 找不到 SKILL.md"

    # 讀取並驗證前置資料
    content = skill_md.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return False, "❌ 找不到 YAML 前置資料"

    # 擷取前置資料
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "❌ 前置資料格式無效"

    frontmatter_text = match.group(1)

    # 解析 YAML 前置資料
    if HAS_YAML:
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                return False, "❌ 前置資料必須是 YAML 字典"
        except yaml.YAMLError as e:
            return False, f"❌ 前置資料中的 YAML 無效：{e}"
    else:
        # 無 yaml 模組時的簡易解析（fallback）
        frontmatter = {}
        for line in frontmatter_text.strip().split('\n'):
            if ':' in line:
                key, _, val = line.partition(':')
                frontmatter[key.strip()] = val.strip().strip('"').strip("'")

    # 檢查非預期的屬性
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"❌ SKILL.md 前置資料中有非預期的屬性：{', '.join(sorted(unexpected_keys))}。"
            f"允許的屬性為：{', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # 檢查必要欄位
    if 'name' not in frontmatter:
        return False, "❌ 前置資料中缺少 'name'"
    if 'description' not in frontmatter:
        return False, "❌ 前置資料中缺少 'description'"

    # 驗證名稱格式
    name = str(frontmatter.get('name', '')).strip()
    if name:
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"❌ 名稱 '{name}' 應為 kebab-case（僅限小寫字母、數字與連字號）"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"❌ 名稱 '{name}' 不能以連字號開頭/結尾，也不能包含連續連字號"
        if len(name) > 64:
            return False, f"❌ 名稱過長（{len(name)} 字元），上限為 64 字元"

    # 驗證描述
    description = str(frontmatter.get('description', '')).strip()
    if description:
        if '<' in description or '>' in description:
            return False, "❌ 描述不能包含角括號（< 或 >）"
        if len(description) > 1024:
            return False, f"❌ 描述過長（{len(description)} 字元），上限為 1024 字元"

    # 驗證 compatibility 欄位（選用）
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"❌ compatibility 必須是字串，得到 {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"❌ compatibility 過長（{len(compatibility)} 字元），上限為 500 字元"

    return True, "✅ 技能驗證通過！"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python scripts/quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
