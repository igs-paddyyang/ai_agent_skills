---
name: arkagent-skill-creator
description: "在 ArkBot 或 ArkAgent OS 專案內建立、驗證和管理 Skill Package。產出與 Kiro Skill 統一的目錄結構（SKILL.md + README.md + config/skill.yaml + scripts/ + references/ + assets/），支援 4 種 runtime（python / mcp / ai / composite）。當使用者提到建立 Agent Skill、新增 Bot 技能、管理 Agent skills、建立 skill package、新增 mcp skill、建立 workflow skill、arkagent skill、bot skill creator、agent-arkbot skill 時，請務必使用此技能。"
---

# ArkAgent Skill Creator

在 ArkBot / ArkAgent OS 專案內建立和管理 Skill Package，採用與 Kiro Skill 統一的目錄結構。

## 工作流程

### 階段 1：意圖釐清（20%）

確認以下資訊：
1. 目標專案路徑（哪個 Agent 專案）
2. 技能要做什麼（功能描述）
3. runtime 類型（python / mcp / ai / composite）
4. 如果是 mcp：server name / tool name / param_mapping

自動偵測專案類型：有 `compat/` 目錄 → arkagent（COMPAT_DIR=compat），否則 → arkbot（COMPAT_DIR=src）。

### 階段 2：產生 Skill Package（60%）

根據 runtime 類型產出對應的目錄結構。所有 runtime 共用相同的頂層結構：

```
skills/{skill_id}/
├── SKILL.md              # 技能指令（給 AI 讀）
├── README.md             # 說明文件（給人讀）
├── config/
│   └── skill.yaml        # runtime metadata（給 SkillRegistry 讀）
├── scripts/              # 可執行腳本
├── assets/               # 範本、prompt 等
└── references/           # 按需載入的指南
```

各 runtime 的差異在於 config/skill.yaml 的欄位和額外產出的檔案。

#### 推導規則
- skill_id：從使用者描述推導，kebab-case（如 `player-query`）
- intent：skill_id 轉 UPPER_SNAKE_CASE（如 `PLAYER_QUERY`）
- composite runtime 的 Skill 放在 `skills/workflows/{skill_id}/`

#### 產出後提醒
建立完成後提醒使用者：
1. 執行 `py scripts/update_agent_yaml.py {project_path}` 更新 agent.yaml
2. 如果是 mcp runtime，確認 config/mcp.json 有對應 server
3. 重啟 Agent 讓 SkillRegistry 重新掃描

### 階段 3：驗證（100%）

執行驗證腳本確認結構正確：
```bash
py scripts/validate_agent_skill.py {project_path}/skills/{skill_id}
```

---

## 操作類型

### create — 建立新 Skill

這是核心操作，按上述 3 階段工作流程執行。

### list — 列出所有 Skills

掃描目標專案的 `skills/` 目錄（含二層子目錄），顯示表格：
```
skill_id          | runtime    | intent         | enabled | version
------------------|------------|----------------|---------|--------
dashboard         | python     | DASHBOARD      | true    | 1.0.0
mssql-query       | mcp        | MSSQL_QUERY    | true    | 1.0.0
```

執行腳本：`py scripts/init_agent_skill.py {project_path} --list`

### validate — 驗證 Skill

驗證項目（詳見 `references/skill-yaml-schema.md`）：
1. config/skill.yaml 存在且必填欄位完整
2. runtime 對應的額外欄位存在
3. mcp runtime：server 在 config/mcp.json 中存在
4. python runtime：skill.py 存在且有 run() 或 run_async()
5. ai runtime：prompt.txt 存在
6. SKILL.md 存在且有 YAML 前置資料

### toggle — 啟用/停用 Skill

修改 config/skill.yaml 的 `enabled` 欄位。

### update-registry — 更新 agent.yaml

掃描 skills/ 所有 config/skill.yaml，自動更新 agents/default/agent.yaml 的 intents + skills 清單。

---

## 4 種 Runtime 指南

選擇 runtime 的決策樹：

```
Skill 需要什麼？
├── 自訂 Python 邏輯 → python（有 skill.py）
├── 呼叫外部 MCP Server → mcp（只需 skill.yaml）
├── LLM 推理（prompt 驅動）→ ai（有 prompt.txt）
└── 多步驟工作流程 → composite（串接其他 skills）
```

各 runtime 的 skill.yaml 欄位差異和完整範例，請參閱 `references/runtime-guide.md`。
skill.yaml 的完整 schema 定義，請參閱 `references/skill-yaml-schema.md`。

---

## 向後相容

現有的 Agent Skill（根目錄 skill.yaml + skill.py）不需要修改。SkillRegistry 掃描優先順序：
1. `skill.yaml`（根目錄，現有格式）
2. `config/skill.yaml`（新格式）
3. `skill.json`（舊格式）
4. `SKILL.md` 前置資料（Kiro 格式 fallback）

Executor 入口檔案優先順序：
1. `skill.py`（根目錄，現有格式）
2. `scripts/skill.py`（新格式）

---

## 附帶資源

### scripts/
- `scripts/init_agent_skill.py` — 初始化 Skill 目錄（自動偵測 src/compat，支援 --list）
- `scripts/validate_agent_skill.py` — 驗證 skill.yaml + SKILL.md + 依賴檢查
- `scripts/update_agent_yaml.py` — 掃描 skills/ 自動更新 agent.yaml
- `scripts/test_agent_skill.py` — 簡易 Executor 執行測試

### references/
- `references/skill-yaml-schema.md` — skill.yaml 完整欄位規格（4 種 runtime）
- `references/runtime-guide.md` — 4 種 runtime 使用場景、範例、注意事項
- `references/unified-structure.md` — 統一目錄結構說明、與 Kiro Skill 對應關係

### assets/
- `assets/templates/` — 4 種 runtime 的 skill.yaml + SKILL.md + README.md + skill.py 範本
