---
inclusion: manual
# 📌 注入模式：手動引用
# 📋 用途：AI 協作 SOP、Steering 體系說明與維護指南
# 🎯 使用時機：新成員加入、複習協作流程、或需要決定「該改哪份文件」時閱讀
# ✏️ 維護：協作方式或 Steering 文件結構改變時更新
---

> 這份文件說明如何有效地與 AI 助理協作開發本專案，包含 Steering 體系全貌、操作 SOP 與維護指南。

---

## 📂 Steering 文件體系（6 檔全貌）

| 文件 | 注入模式 | 角色比喻 | 核心職責 |
|---|---|---|---|
| `claude.md` | always | 憲法 | AI 行為準則、Skill-First 思維、代碼風格、禁止事項 |
| `product.md` | always | 產品說明書 | 工作坊定位、三大教學模組、技能庫概述 |
| `tech.md` | always | 工具箱清單 | 套件版本、環境變數、常用指令 |
| `structure.md` | fileMatch | 施工藍圖 | 目錄結構、新增技能/模組的慣例 |
| `memory.md` | manual | 存檔點 | 當前進度、架構決策紀錄、上次對話摘要 |
| `ai_workflow.md` | manual | 新手教學 | 本文件。協作 SOP、文件維護指南、修剪規則 |

### 注入模式說明

- **always**：每次對話自動載入。目前 3 份（claude / product / tech）。
- **fileMatch**：編輯符合 pattern 的檔案時自動載入。`structure.md` 在編輯 `agent_skills/`、`clawdbot/`、`gemini_canvas/`、`.agent/` 時觸發。
- **manual**：需要時用 `#File` 手動餵入。`memory.md` 在開新對話時餵入；`ai_workflow.md` 在需要複習 SOP 時餵入。

---

## 🔀 文件分工邊界（唯一權威來源）

| 資訊類型 | 權威來源 | 不要放在 |
|---|---|---|
| AI 行為準則、禁止事項 | `claude.md` | 其他文件 |
| 代碼風格、命名規範 | `claude.md` | structure.md |
| 產品定位、教學模組、技能庫 | `product.md` | claude.md, memory.md |
| 套件版本、環境變數、常用指令 | `tech.md` | claude.md, structure.md |
| 目錄結構、新增技能/模組慣例 | `structure.md` | claude.md |
| 開發進度、已完成任務 | `memory.md` | 其他任何文件 |
| 架構決策紀錄（為什麼這樣做） | `memory.md` | claude.md |
| 協作流程本身 | `ai_workflow.md` | 其他文件 |

> 原則：如果你不確定該改哪份文件，問自己「這個資訊是**規則**、**產品**、**技術**、**結構**、還是**進度**？」

---

## 🔄 標準操作流程（SOP）

### 開始新對話時
1. always 三件套（claude / product / tech）自動載入
2. 用 `#File` 手動餵入 `memory.md`
3. 說明本次對話目標

### 開發過程中
- 完成任務 → 更新 `memory.md`
- 新增技能 → 更新 `structure.md`
- 新增套件或指令 → 更新 `tech.md`
- 新增教學模組 → 更新 `product.md` + `structure.md`
- 改了行為準則 → 更新 `claude.md`

### 結束對話前
1. 請 AI 總結本次做了什麼（1-3 句話）
2. 更新 `memory.md` 的「上次對話摘要」
3. 確認進行中任務是否正確

### 決策樹：該更新哪份文件？

```
我改了什麼？
├── AI 行為規則 / 禁止事項 → claude.md
├── 產品能力 / 教學模組 → product.md
├── 套件版本 / 環境變數 / 指令 → tech.md
├── 目錄結構 / 新增技能或模組 → structure.md
├── 完成了任務 / 做了架構決策 → memory.md
└── 協作流程本身改變了 → ai_workflow.md
```

---

## ✂️ 修剪指南

### memory.md（最常需要修剪）
- 已完成項目超過 20 行時，濃縮為摘要
- 「上次對話摘要」只保留最近一次
- 已解決的問題立即刪除

### always 文件（claude / product / tech）
- token 成本最高，每份控制在 80 行以內
- 刪除已成為常識的規則
- 範例只保留最關鍵的
