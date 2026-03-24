# 關聯索引格式規範

本文件定義 Skill Tapestry 的關聯索引格式與進階用法。

## JSON 格式（機器可讀）

```json
{
  "version": "1.0",
  "generated_at": "2026-03-24",
  "total_skills": 19,
  "skills": [
    {
      "name": "skill-creator",
      "category": "元技能",
      "description_short": "建立/測試/打包技能",
      "relations": {
        "depends_on": ["skill-spec-writer"],
        "complements": ["prompt-engineering-guide", "changelog-generator"],
        "extends": ["skill-seeker"],
        "replaces": []
      }
    }
  ],
  "categories": {
    "元技能": ["skill-creator", "skill-seeker", "skill-tapestry"],
    "規格": ["skill-spec-writer", "software-spec-writer"],
    "開發指引": ["tdd-workflow", "software-architecture-guide", "mcp-builder-guide", "prompt-engineering-guide"],
    "產生器": ["arkbot-agent-generator", "gemini-canvas-dashboard", "d3-visualization-guide"],
    "文件": ["document-summarizer", "websearch-summarizer", "changelog-generator", "game-design-document-writer"],
    "環境": ["env-setup-installer", "env-smoke-test"],
    "同步": ["skill-sync"]
  }
}
```

## Markdown 格式（人類可讀）

### 完整索引範本

```markdown
# Skill Tapestry — 技能關聯索引

**產生日期**: 2026-03-24
**技能總數**: 19

## 技能總覽

| # | 名稱 | 分類 | 版本 | 關聯數 |
|---|------|------|------|--------|
| 1 | skill-creator | 元技能 | 1.x | 4 |
| 2 | skill-spec-writer | 規格 | 1.x | 2 |
| ... | ... | ... | ... | ... |

## 關聯詳情

### skill-creator
- 依賴：skill-spec-writer（規格輸入）
- 互補：prompt-engineering-guide（改善 description）
- 互補：changelog-generator（版本管理）
- 延伸：skill-seeker（從文件建立技能）

### tdd-workflow
- 互補：software-architecture-guide（架構 + 測試）
- 互補：skill-creator（eval 測試框架）

（以此類推...）
```

## 進階用法

### 關聯強度

可選擇性標註關聯強度：

| 強度 | 說明 | 標記 |
|------|------|------|
| 強 | 幾乎總是一起使用 | ★★★ |
| 中 | 經常搭配使用 | ★★ |
| 弱 | 偶爾相關 | ★ |

```markdown
| 技能 A | 關聯 | 技能 B | 強度 |
|--------|------|--------|------|
| skill-spec-writer | → | skill-creator | ★★★ |
| tdd-workflow | ↔ | software-architecture-guide | ★★ |
| gemini-canvas-dashboard | ↔ | d3-visualization-guide | ★ |
```

### 工作流鏈

定義常見的技能使用鏈：

```markdown
## 工作流鏈

### 新技能開發鏈
skill-spec-writer → skill-creator → prompt-engineering-guide → changelog-generator → skill-sync

### ArkBot 開發鏈
software-spec-writer → arkbot-agent-generator → tdd-workflow → env-setup-installer → env-smoke-test

### 文件轉技能鏈
websearch-summarizer / document-summarizer → skill-seeker → skill-creator
```

### 差異追蹤

記錄索引的變更歷史：

```markdown
## 變更紀錄

### 2026-03-24
- 新增 7 個技能（tdd-workflow 等）
- 技能總數 12 → 19
- 新增「開發指引」分類
```

## 自動掃描腳本（未來規劃）

```python
# 概念性腳本，未來可實作
import os
import yaml

def scan_skills(skills_dir=".kiro/skills"):
    skills = []
    for name in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.exists(skill_md):
            with open(skill_md) as f:
                content = f.read()
                # 解析 YAML frontmatter
                # 提取 name, description
                skills.append({"name": name, "path": skill_md})
    return skills
```
