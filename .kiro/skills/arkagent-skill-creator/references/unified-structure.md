# 統一目錄結構說明

Agent Skill Package 採用與 Kiro Skill 統一的目錄結構（方案 A：skill.yaml + SKILL.md 共存）。

## 結構對照

```
Kiro Skill（.kiro/skills/）          Agent Skill Package（{project}/skills/）
├── SKILL.md（AI 指令）              ├── SKILL.md（AI 指令）              ← 相同
├── README.md（人類說明）            ├── README.md（人類說明）            ← 相同
├── references/                      ├── references/                      ← 相同
├── scripts/                         ├── scripts/
│   └── *.py（工具腳本）             │   └── skill.py（執行入口）         ← 對應
├── assets/                          ├── assets/
│   └── *.html（範本）               │   └── prompt.txt（AI prompt）      ← 對應
│                                    └── config/
│                                        └── skill.yaml（runtime metadata）← 新增
```

## 各檔案職責

| 檔案 | 消費者 | 用途 | 必要性 |
|------|--------|------|--------|
| SKILL.md | AI（Gemini / Kiro） | 自然語言指令：技能做什麼、怎麼用、邊界案例 | 建議 |
| README.md | 人類開發者 | 版本資訊、使用方式、變更紀錄 | 建議 |
| config/skill.yaml | SkillRegistry / Executor | runtime metadata：skill_id / intent / runtime / mcp 設定 | 必要 |
| scripts/skill.py | PythonAdapter | 執行入口（python runtime） | python 必要 |
| assets/prompt.txt | AIAdapter | LLM 推理 prompt（ai runtime） | ai 必要 |
| references/ | AI 按需載入 | 詳細指南、schema 說明 | 選用 |

## 向後相容策略

現有的 Agent Skill（根目錄 skill.yaml + skill.py）完全相容，不需要任何修改。

### SkillRegistry 掃描優先順序
1. `{skill_dir}/skill.yaml`（根目錄，現有格式）
2. `{skill_dir}/config/skill.yaml`（新格式）
3. `{skill_dir}/skill.json`（舊 JSON 格式）
4. `{skill_dir}/SKILL.md` 前置資料（Kiro 格式 fallback）

### Executor 入口檔案優先順序
1. `{skill_dir}/skill.py`（根目錄，現有格式）
2. `{skill_dir}/scripts/skill.py`（新格式）

### AIAdapter prompt 優先順序
1. `{skill_dir}/prompt.txt`（根目錄，現有格式）
2. `{skill_dir}/assets/prompt.txt`（新格式）

## 遷移路徑

現有 Skill 不需要立即遷移。新建 Skill 使用新結構，舊 Skill 可在需要時逐步遷移：

```bash
# 遷移範例：將 mssql-query 從舊結構遷移到新結構
mkdir skills/mssql-query/config
mv skills/mssql-query/skill.yaml skills/mssql-query/config/
# 新增 SKILL.md + README.md（選用）
```
