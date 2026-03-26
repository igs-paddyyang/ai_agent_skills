# ArkAgent Skill Creator

> 在 ArkBot / ArkAgent OS 專案內建立和管理 Skill Package，採用與 Kiro Skill 統一的目錄結構。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-25 |
| 最後更新 | 2026-03-25 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

支援 6 種操作：

- create — 建立新 Skill Package（4 種 runtime：python / mcp / ai / composite）
- list — 列出專案內所有 Skills
- validate — 驗證 Skill 結構與依賴
- toggle — 啟用/停用 Skill
- info — 顯示 Skill 完整資訊
- update-registry — 掃描 skills/ 自動更新 agent.yaml

產出的 Skill Package 採用與 Kiro Skill 統一的目錄結構：
```
skills/{skill_id}/
├── SKILL.md              # 技能指令（給 AI 讀）
├── README.md             # 說明文件（給人讀）
├── config/
│   └── skill.yaml        # runtime metadata（給 SkillRegistry 讀）
├── scripts/              # 可執行腳本
├── assets/               # 範本、prompt
└── references/           # 按需載入的指南
```

## 使用方式

觸發此技能的方式：
```
「在 tiger-bot 建立一個查詢玩家資料的 python skill」
「在 ninja-bot 建立一個用 mssql-server 查詢營收的 mcp skill」
「列出 tiger-bot 的所有 skills」
「驗證 tiger-bot 的 mssql-query skill」
「建立 Agent Skill」
「新增 Bot 技能」
```

### CLI 用法

```bash
# 建立 python skill
py .kiro/skills/arkagent-skill-creator/scripts/init_agent_skill.py tiger-bot player-query

# 建立 mcp skill
py .kiro/skills/arkagent-skill-creator/scripts/init_agent_skill.py tiger-bot revenue-query --runtime mcp --mcp-server mssql-server --mcp-tool execute_sql

# 列出所有 skills
py .kiro/skills/arkagent-skill-creator/scripts/init_agent_skill.py tiger-bot --list

# 驗證 skill
py .kiro/skills/arkagent-skill-creator/scripts/validate_agent_skill.py tiger-bot/skills/mssql-query

# 更新 agent.yaml
py .kiro/skills/arkagent-skill-creator/scripts/update_agent_yaml.py tiger-bot
```

## 檔案結構

```
arkagent-skill-creator/
├── SKILL.md                           # 技能指令（6 種操作 + 4 種 runtime）
├── README.md                          # 本文件
├── references/
│   ├── skill-yaml-schema.md           # skill.yaml 完整欄位規格
│   ├── runtime-guide.md               # 4 種 runtime 使用指南
│   └── unified-structure.md           # 統一目錄結構說明
└── scripts/
    ├── init_agent_skill.py            # 初始化 Skill 目錄（含 --list）
    ├── validate_agent_skill.py        # 驗證 Skill 結構與依賴
    └── update_agent_yaml.py           # 自動更新 agent.yaml
```

## 變更紀錄

### v0.1.0（2026-03-25）
- 初始版本
- 6 種操作：create / list / validate / toggle / info / update-registry
- 4 種 runtime 支援：python / mcp / ai / composite
- 統一目錄結構（SKILL.md + README.md + config/skill.yaml）
- 3 個 CLI 腳本：init_agent_skill.py / validate_agent_skill.py / update_agent_yaml.py
- 3 個 references：skill-yaml-schema / runtime-guide / unified-structure
