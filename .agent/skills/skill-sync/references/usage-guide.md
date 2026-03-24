# skill-sync 使用指南

## 預設行為

不帶任何參數時，同步 5 個核心技能：

```bash
py .kiro/skills/skill-sync/scripts/sync_skills.py
```

預設清單：
1. `arkbot-agent-generator`
2. `gemini-canvas-dashboard`
3. `skill-creator`
4. `skill-spec-writer`
5. `software-spec-writer`

輸出：
```
🔄 技能同步開始（.kiro/skills → .agent/skills）— 預設 5 個核心技能

  ✅ arkbot-agent-generator → .agent/skills/arkbot-agent-generator
  ✅ gemini-canvas-dashboard → .agent/skills/gemini-canvas-dashboard
  ✅ skill-creator → .agent/skills/skill-creator
  ✅ skill-spec-writer → .agent/skills/skill-spec-writer
  ✅ software-spec-writer → .agent/skills/software-spec-writer
────────────────────────────────────────
📊 同步完成：成功 5 / 跳過 0 / 失敗 0
```

## 全量同步

```bash
py .kiro/skills/skill-sync/scripts/sync_skills.py --all
```

掃描 `.kiro/skills/` 下所有目錄並同步。

## 指定技能

```bash
py .kiro/skills/skill-sync/scripts/sync_skills.py --skills env-smoke-test game-copywriting
```

覆蓋預設清單，僅同步指定的技能。

## 預覽模式

```bash
py .kiro/skills/skill-sync/scripts/sync_skills.py --dry-run
```

僅顯示將要執行的操作，不實際複製檔案。

## 反向還原

```bash
py .kiro/skills/skill-sync/scripts/sync_skills.py --reverse --skills skill-creator
```

從 `.agent/skills` 還原到 `.kiro/skills`。

## 參數一覽

| 參數 | 縮寫 | 說明 | 預設 |
|------|------|------|------|
| `--skills` | `-s` | 指定技能名稱（空格分隔） | 5 個核心技能 |
| `--all` | `-a` | 全量同步所有技能 | 否 |
| `--reverse` | `-r` | 反向同步 `.agent → .kiro` | 否 |
| `--dry-run` | `-d` | 預覽模式，不實際複製 | 否 |

## 優先順序

`--skills` 指定 > `--all` 全量掃描 > 預設 5 個核心技能
