# skill-sync Skill Spec

**作者**: paddyyang
**日期**: 2026-03-18
**版本**: v0.1
**目標**: 作為 skill-creator 的輸入，產出 skill-sync 技能

---

## 1. 技能定義

- **名稱**: skill-sync
- **一句話描述**: 將 `.kiro/skills/` 的指定技能同步備份到 `.agent/skills/`，確保開發區與正式區版本一致
- **觸發描述（description 欄位草稿）**:
  > 將 .kiro/skills/ 的指定技能同步備份到 .agent/skills/，確保開發區與正式區版本一致。產出一個 Python 腳本，支援指定技能清單、全量同步、差異比對等功能。當使用者提到同步技能、備份技能、sync skills、複製技能到 .agent、技能備份、skill backup、skill sync、同步 .kiro 到 .agent、技能版本同步時，請務必使用此技能。

## 2. 行為規格

### 2.1 輸入

- **技能清單**（選用）：要同步的技能名稱列表，預設為 5 個核心技能
- **全量模式**（選用）：`--all` 掃描來源目錄全部技能
- **同步方向**（選用）：`.kiro → .agent`（預設）或 `.agent → .kiro`（反向還原）
- **專案路徑**（選用）：工作區根目錄，預設為當前目錄

### 2.2 預設技能清單

不指定 `--skills` 也不指定 `--all` 時，預設同步以下 5 個核心技能：

1. `arkbot-agent-generator`
2. `gemini-canvas-dashboard`
3. `skill-creator`
4. `skill-spec-writer`
5. `software-spec-writer`

### 2.3 處理邏輯

1. 決定技能清單：`--skills` 指定 > `--all` 全量掃描 > 預設 5 個核心技能
2. 對每個技能：
   a. 檢查來源目錄是否存在，不存在則跳過並警告
   b. 若目標目錄已存在，先清除再複製（避免殘留舊檔案）
   c. 使用 `shutil.copytree` 完整複製目錄
   d. 輸出同步結果（成功 / 跳過 / 失敗）
3. 產出同步摘要報告（成功數、跳過數、失敗數）

### 2.3 輸出格式

技能產出一個 Python 腳本 `scripts/sync_skills.py`，執行後的終端輸出格式：

```
🔄 技能同步開始（.kiro/skills → .agent/skills）
✅ arkbot-agent-generator → .agent/skills/arkbot-agent-generator
✅ gemini-canvas-dashboard → .agent/skills/gemini-canvas-dashboard
♻ skill-creator（已清除舊備份）→ .agent/skills/skill-creator
⚠ some-missing-skill — 來源不存在，跳過
──────────────────────────────
📊 同步完成：成功 3 / 跳過 1 / 失敗 0
```

### 2.4 邊界案例

- **來源不存在**：跳過並輸出警告，不中斷整體流程
- **目標已存在**：清除後重新複製，確保完全一致
- **未指定技能**：使用預設 5 個核心技能清單
- **`--all` 模式**：掃描 `.kiro/skills/` 全部目錄
- **反向同步**：支援 `--reverse` 參數，從 `.agent/skills` 還原到 `.kiro/skills`
- **不該做**：不修改任何技能內容，純粹的檔案複製操作

## 3. 資源需求

### scripts/

| 腳本 | 用途 |
|------|------|
| `sync_skills.py` | 主要同步腳本，支援 `--skills`、`--all`、`--reverse`、`--dry-run` 參數 |

### references/

| 文件 | 涵蓋範圍 |
|------|---------|
| `usage-guide.md` | 使用說明、參數說明、常見用法範例 |

### SKILL.md 預估

- 預估行數：80～120 行
- 是否需要拆分到 references/：否（核心指令簡潔，使用指南放 references/）

## 4. 測試案例

| # | 提示詞 | 預期輸出 | 驗證方式 |
|---|--------|---------|---------|
| 1 | 「幫我把 .kiro/skills 的 arkbot-agent-generator 和 skill-creator 同步到 .agent/skills」 | 產出 sync_skills.py 並執行，兩個技能成功複製 | 檢查 .agent/skills/ 下對應目錄存在且內容一致 |
| 2 | 「同步所有技能到備份區」 | 使用 `--all` 掃描 .kiro/skills/ 全部技能並同步 | 檢查 .agent/skills/ 下目錄數量與 .kiro/skills/ 一致 |
| 3 | 「用 dry-run 模式預覽同步結果」 | 輸出將要同步的技能清單，但不實際複製 | 確認 .agent/skills/ 無變化 |
| 4 | 「從 .agent/skills 還原 skill-creator 到 .kiro/skills」 | 反向複製 .agent → .kiro | 檢查 .kiro/skills/skill-creator 內容與 .agent 版本一致 |
| 5 | 「同步一個不存在的技能 fake-skill」 | 輸出警告訊息，不中斷 | 確認無錯誤拋出，摘要顯示跳過 1 |

## 5. 備註

- 此技能為工具型技能，核心產出物是一個可重複執行的 Python 腳本
- 腳本僅使用 Python 標準庫（`shutil`、`pathlib`、`argparse`），無額外依賴
- 預設同步方向為 `.kiro → .agent`（正式區 → 備份區），符合專案慣例
- 預設技能清單為 5 個核心技能，使用 `--all` 可全量掃描
- 未來可擴展：差異比對（`--diff`）、版本號檢查、自動 git commit
- 此技能的教學價值：展示如何用 Kiro Skill 包裝一個簡單的檔案操作腳本，適合作為入門範例
