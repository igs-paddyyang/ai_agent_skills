---
name: skill-sync
description: "將 .kiro/skills/ 的指定技能同步備份到 .agent/skills/，確保開發區與正式區版本一致。產出一個 Python 腳本，支援指定技能清單、全量同步、反向還原等功能。當使用者提到同步技能、備份技能、sync skills、複製技能到 .agent、技能備份、skill backup、skill sync、同步 .kiro 到 .agent、技能版本同步時，請務必使用此技能。"
---

# 技能同步工具（Skill Sync）

將 `.kiro/skills/` 的技能同步備份到 `.agent/skills/`，或反向還原。

## 使用時機

- 技能開發完成，需要備份到 `.agent/skills/`
- 需要從備份區還原技能到正式區
- 批次同步多個技能或全量同步
- 預覽同步操作而不實際執行

## 工作流程

### 步驟 1：確認同步需求

從使用者的描述中提取以下資訊：

| 項目 | 說明 | 預設值 |
|------|------|--------|
| 技能清單 | 要同步的技能名稱 | 5 個核心技能（見下方） |
| 同步方向 | `.kiro → .agent` 或反向 | `.kiro → .agent` |
| 執行模式 | 實際執行或僅預覽 | 實際執行 |

### 預設行為

不指定 `--skills` 時，預設全量同步：掃描來源目錄所有技能並同步。

### 步驟 2：執行同步腳本

使用 `scripts/sync_skills.py` 執行同步：

```bash
# 全量同步（預設）
py .kiro/skills/skill-sync/scripts/sync_skills.py

# 同步指定技能
py .kiro/skills/skill-sync/scripts/sync_skills.py --skills arkbot-agent-generator skill-creator

# 預覽模式（不實際複製）
py .kiro/skills/skill-sync/scripts/sync_skills.py --dry-run

# 反向還原（.agent → .kiro）
py .kiro/skills/skill-sync/scripts/sync_skills.py --reverse --skills skill-creator
```

### 步驟 3：確認結果

腳本執行後會輸出同步摘要，包含成功、跳過、失敗的數量。確認結果無誤後告知使用者。

## 參數說明

| 參數 | 說明 |
|------|------|
| `--skills` | 指定要同步的技能名稱（空格分隔），覆蓋預設全量同步 |
| `--reverse` | 反向同步：從 `.agent/skills` 還原到 `.kiro/skills` |
| `--dry-run` | 預覽模式，僅顯示將要執行的操作，不實際複製 |

## 注意事項

- 同步是完整覆蓋，目標目錄會先清除再複製
- 不修改任何技能內容，純粹的檔案複製操作
- 來源不存在的技能會跳過並警告，不中斷流程
- 僅使用 Python 標準庫，無額外依賴

詳細使用範例請參考 `references/usage-guide.md`。
