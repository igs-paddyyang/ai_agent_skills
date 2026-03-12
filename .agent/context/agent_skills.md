# 🧩 AI Agent 技能歸類標準 (Skill Classification Standards)

**目標：** 定義 AI Agent 技能的歸類邏輯與目錄存放準則，確保一致性。

---

## 1. 技能存放目錄架構

| 目錄層次 | 路徑 | 存放內容 |
|:---|:---|:---|
| **技能定義層** | `.agent/skills/{name}/SKILL.md` | 技能的角色定義、產出規範、品質標準 |
| **參考資料** | `.agent/skills/{name}/references/` | 設計模式、Prompt 模板等參考文件 |
| **輔助腳本** | `.agent/skills/{name}/scripts/` | 技能相關的工具腳本 |
| **範例** | `.agent/skills/{name}/examples/` | 產出範例 |

---

## 2. 技能清單（13 個）

| 技能名稱 | 有 SKILL.md | 有 references/ | 用途 |
|:---|:---|:---|:---|
| `character-creator` | ✅ | ✅ boss-design-patterns.md | Boss 角色設計 |
| `level-designer` | ✅ | ✅ design-patterns.md | 關卡環境設計 |
| `skill-creator` | ✅ | ✅ output-patterns.md, workflows.md | 建立新技能的工具 |
| `document-summarizer` | ✅ | ✅ prompt-templates.md | 文件摘要 |
| `email-writer` | ✅ | ✅ prompt-templates.md | 郵件撰寫 |
| `marketing-copywriter` | ✅ | ✅ prompt-templates.md | 行銷文案 |
| `meeting-minutes-writer` | ✅ | ✅ prompt-templates.md | 會議紀錄 |
| `presentation-writer` | ✅ | ✅ prompt-templates.md | 簡報撰寫 |
| `customer-support-agent` | ✅ | — | 客服回覆 |
| `market-analyzer` | ✅ | — | 市場分析 |
| `social-media-writer` | ✅ | — | 社群媒體內容 |
| `sop-writer` | ✅ | — | 標準作業程序 |
| `task-planner` | ✅ | — | 任務規劃 |

---

## 3. GDD 生成器使用的技能鏈

```
Step 1: @level-designer → 環境設計（氛圍 + 危險要素 + 玩家目標）
Step 2: @character-creator → Boss 設計（名稱 + 技能 + 動機，對齊 Step 1 的環境）
Step 3: 組裝 → reports/GDD_{主題}_{日期}.md
```

---

## 4. 新增技能標準流程

1. 在 `.agent/skills/` 建立 `{skill-name}/` 目錄
2. 撰寫 `SKILL.md`，定義角色、產出規範、格式要求
3. 可選：加入 `references/`（參考資料）、`scripts/`（輔助腳本）
4. 在 Python 腳本中用 `load_skill("{skill-name}")` 載入
5. 更新本文件的技能清單

---
*最後更新日期: 2026-03-12*
