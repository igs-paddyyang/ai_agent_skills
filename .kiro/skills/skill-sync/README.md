# skill-sync

| 項目 | 說明 |
|------|------|
| 版本 | 0.3.0 |
| 建立日期 | 2026-03-18 |
| 最後更新 | 2026-03-19 |
| 作者 | paddyyang |
| 平台 | Kiro IDE |
| 語言 | 繁體中文 |

## 功能說明

將 `.kiro/skills/` 的指定技能同步備份到 `.agent/skills/`，確保開發區與正式區版本一致。預設全量同步所有技能，支援指定技能清單、反向還原、預覽模式。

## 使用方式

觸發語句範例：
- 「同步技能到備份區」（全量同步）
- 「幫我把 env-smoke-test 同步到 .agent/skills」（指定技能）
- 「從 .agent/skills 還原 skill-creator」
- 「用 dry-run 預覽同步結果」

## 檔案結構

```
skill-sync/
├── SKILL.md                  # 技能指令
├── README.md                 # 本文件
├── references/
│   └── usage-guide.md        # 詳細使用說明與範例
├── scripts/
│   └── sync_skills.py        # 同步腳本（Python 標準庫）
└── spec/
    └── skill-sync-spec.md    # Skill Spec
```

## 變更紀錄

### v0.3.0（2026-03-19）
- 預設行為改為全量同步（掃描來源目錄所有技能）
- 移除 `--all` 參數（已為預設行為）
- 移除 DEFAULT_SKILLS 常數

### v0.2.0（2026-03-18）
- 預設同步 5 個核心技能（不再全量掃描）
- 新增 `--all` 參數支援全量同步
- 預設清單：arkbot-agent-generator、gemini-canvas-dashboard、skill-creator、skill-spec-writer、software-spec-writer

### v0.1.0（2026-03-18）
- 初始版本
- 支援 `.kiro/skills` → `.agent/skills` 同步
- 支援 `--skills`、`--all`、`--reverse`、`--dry-run` 參數
- 支援全量同步與指定技能同步
