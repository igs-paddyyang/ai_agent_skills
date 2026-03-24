---
inclusion: manual
version: "1.0.0"
last_synced: "2026-03-24"
---

# AI 協作工作流程

> 使用時機：需要複習協作流程、或新成員加入時閱讀。

---

## Steering 文件總覽

| 檔案 | 注入模式 | 用途 |
|---|---|---|
| `claude.md` | always | 開發規範（Skill 開發 + ArkBot 開發） |
| `product.md` | always | 產品概述（Agent Skills Factory 定位） |
| `tech.md` | always | 技術棧與常用指令 |
| `structure.md` | always | 專案結構（Skills + ArkBot + docs） |
| `memory.md` | manual | 專案進度與決策紀錄 |
| `ai_workflow.md` | manual | 本文件，協作 SOP |

---

## 標準操作流程

### 開始新對話
1. `claude.md` / `product.md` / `tech.md` / `structure.md` 自動載入
2. 如需專案進度上下文，用 `#File` 手動餵入 `memory.md`
3. 說明本次對話目標

### 開發 Kiro Skill 時
- 建立新技能 → 使用 `skill-creator` 技能引導流程
- 技能必須包含 SKILL.md + README.md
- 完成後更新 `structure.md` 的技能清單
- 更新 `memory.md` 的「當前開發狀態」

### 修改現有 Skill 時
- 更新 SKILL.md 內容
- 同步更新 README.md 的版本號與變更紀錄
- 根據改動幅度選擇 MAJOR / MINOR / PATCH

### 開發 ArkBot 功能時
- 新增 Skill → 更新 `structure.md`
- 新增套件 → 更新 `tech.md` + `requirements.txt`
- 架構決策 → 記錄到 `memory.md`

### 撰寫設計文件時
- 使用 `software-spec-writer` 技能產出規格文件
- 設計文件放 `docs/`，規格文件以 `-spec.md` 結尾
- 重大設計決策記錄到 `memory.md`

### 結束對話前
1. 總結本次對話（1-3 句話）
2. 更新 `memory.md` 的「上次對話摘要」

---

## 決策樹：該更新哪份文件？

```
我改了什麼？
├── 新增 / 修改 Kiro Skill
│   → structure.md + memory.md
│   → 技能的 README.md（版本號 + 變更紀錄）
├── 新增 / 修改 ArkBot 功能
│   → structure.md
├── 新增套件或指令
│   → tech.md + requirements.txt
├── 架構決策或重大變更
│   → memory.md
├── 開發規範或代碼風格
│   → claude.md
├── 產品定位或功能描述
│   → product.md
├── 新增設計文件
│   → docs/ + memory.md
└── 完成任務 / 階段性進展
    → memory.md
```

---

## Memory 修剪指南

`memory.md` 超過 80 行時：
- 已完成的里程碑濃縮為一行摘要
- 超過 1 個月的決策紀錄只保留結論
- 上次對話摘要只保留最近一次
- 已解決的問題立即刪除

---

## 版本控管規則（Semantic Versioning）

所有 Steering 文件與 Skill 文件統一採用 `MAJOR.MINOR.PATCH` 格式。

### Steering 文件版本規則

適用範圍：`.kiro/steering/*.md` 的 YAML front-matter `version` 欄位。

| 版本位 | 何時遞增 | 範例場景 |
|--------|---------|---------|
| MAJOR | 文件定位或結構大幅重組 | 合併/拆分文件、章節架構重寫、適用範圍變更 |
| MINOR | 新增章節、新增規則、內容擴充 | 新增「版本控管規則」章節、新增決策樹分支 |
| PATCH | 修正錯字、調整措辭、更新數據 | 修正技能數量、更新日期、微調描述 |

規則：
- 所有 Steering 文件從 `1.0.0` 起算
- 修改任何 Steering 文件時，同步更新 `version` 和 `last_synced`
- MAJOR 遞增時 MINOR 和 PATCH 歸零（例：`1.2.3` → `2.0.0`）
- MINOR 遞增時 PATCH 歸零（例：`1.2.3` → `1.3.0`）

範例：
```
1.0.0 → 1.0.1  # 修正錯字
1.0.1 → 1.1.0  # 新增一個章節
1.1.0 → 2.0.0  # 文件結構大幅重組
```

### Skill 文件版本規則

適用範圍：每個技能的 `README.md` 版本資訊表格。

| 版本位 | 何時遞增 | 範例場景 |
|--------|---------|---------|
| MAJOR | 觸發條件大改、輸出格式變更、破壞性變更 | SKILL.md 指令重寫、輸入/輸出介面變更 |
| MINOR | 新增功能、擴充場景、新增 reference | 新增模板、支援新參數、新增腳本 |
| PATCH | 修正錯誤、調整措辭、微調模板 | 修正 bug、改善提示詞、更新範例 |

規則：
- 新建技能從 `0.1.0` 開始，經 eval 驗證穩定後升級為 `1.0.0`
- 修改技能時必須同步更新 README.md 的版本號與變更紀錄
- MAJOR 遞增時 MINOR 和 PATCH 歸零
- MINOR 遞增時 PATCH 歸零

範例：
```
0.1.0 → 0.1.1  # 修正模板錯字
0.1.1 → 0.2.0  # 新增一個 reference 文件
0.2.0 → 1.0.0  # eval 驗證通過，正式發布
1.0.0 → 1.1.0  # 新增 --dry-run 參數
1.1.0 → 2.0.0  # 輸出格式從 JSON 改為 YAML
```
