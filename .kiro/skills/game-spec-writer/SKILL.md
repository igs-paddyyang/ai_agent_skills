---
name: game-spec-writer
description: >
  根據遊戲機台類型（捕魚機、老虎機、棋牌等），產出完整的遊戲機台規格文件。
  涵蓋遊戲概述、核心玩法、符號/角色分值表、特殊功能、RTP 機率分析、
  硬體機台規格、營運參數等規格。支援完整規格文件和精簡版速查表兩種輸出模式。
  當使用者提到捕魚機、老虎機、棋牌、slot machine、fish game、遊戲機台規格、
  機台規格、RTP 分析、遊戲規格文件、機台企劃、設計遊戲機台、game spec、
  Ocean King、拉霸、角子機、百家樂規格、遊戲機設計時，請務必使用此技能。
---

# 遊戲機台規格撰寫師（Game Spec Writer）

根據使用者的遊戲機台需求，產出結構化的規格文件。支援多種遊戲類型，每種類型有專屬的參考指南。

## 支援的遊戲類型

| 類型 | 參考資源 | 典型產品 |
|------|---------|---------|
| 捕魚機 | `references/fish-game.md` | Ocean King、Sea King、Fish Hunter |
| 老虎機 | `references/slot-machine.md` | 經典三軸、五軸視頻、累進彩金 |
| 棋牌 | `references/card-game.md` | 百家樂、德州撲克、21 點 |

## 輸入

| 項目 | 必要 | 說明 |
|------|------|------|
| 遊戲名稱或構想 | 是 | 遊戲的名稱、主題或核心構想 |
| 遊戲類型 | 否 | 捕魚機 / 老虎機 / 棋牌（未指定時從構想推導） |
| 輸出模式 | 否 | `full`（完整規格，預設）或 `quickref`（精簡速查表） |
| 遊戲平台 | 否 | 街機機台 / 線上版 / 手機版 |
| 參考版本 | 否 | 以哪個經典版本為基礎 |

## 工作流程

### 步驟 1：類型判定與需求確認

從使用者輸入判定遊戲類型，並載入對應的參考資源：

- 捕魚機 → 讀取 `references/fish-game.md`
- 老虎機 → 讀取 `references/slot-machine.md`
- 棋牌 → 讀取 `references/card-game.md`

確認以下核心要素後才進入下一步：
- 遊戲名稱（暫定）
- 遊戲主題
- 目標平台（街機 / 線上 / 手機）
- 特殊需求（RTP 目標、法規合規要求等）

### 步驟 2：章節展開

根據遊戲類型和輸出模式，展開對應的章節結構。

**完整規格模式（full，預設）** — 通用 9 章節框架：

1. 遊戲概述（Overview）
2. 核心玩法（Core Gameplay）
3. 符號/角色與分值系統（Symbol/Character & Payout Table）
4. 特殊功能與獎勵機制（Special Features & Bonus）
5. 投注與倍率系統（Bet & Multiplier System）
6. RTP 與機率系統（Return to Player & Probability）
7. 機台硬體規格（Cabinet Specifications）
8. 營運與合規（Operations & Compliance）
9. 競品對比（Competitive Analysis）

各遊戲類型的章節側重不同，詳見對應的 references/ 文件。

**精簡速查表模式（quickref）** — 4 個區塊：

1. 基本資訊卡（一頁式）
2. 符號/角色分值速查表
3. 特殊功能一覽表
4. 投注/倍率對照表

### 步驟 3：數值與細節填充

為各章節提供具體數值。所有數值標註「建議值，需依實際設定調整」。
參考對應遊戲類型的 references/ 文件取得業界標準數值範圍。

### 步驟 4：產出與儲存

- Markdown 格式
- 預設路徑：`docs/{遊戲名稱}-spec.md`（full）或 `docs/{遊戲名稱}-quickref.md`（quickref）
- 末尾標註：`*本文件由 game-spec-writer 技能產出，版本 vX.Y.Z，日期 YYYY-MM-DD。數值需依實際設定調整。*`

## 輸出格式要求

- Markdown 格式，章節使用 `##` 標題
- 表格優先於長段落
- 繁體中文撰寫，遊戲術語保留英文（RTP、Payout、Multiplier）
- 數值用表格呈現，標註「建議值」
- 所有機率數值精確到小數點後 2-4 位

## 邊界案例

| 情境 | 處理方式 |
|------|---------|
| 輸入過於模糊 | 引導使用者提供遊戲類型、主題和目標平台 |
| 不支援的遊戲類型 | 引導使用 game-design-document-writer 通用 GDD 技能 |
| 要求精確合規數值 | 標註所有數值為建議值，需經監管機構審核 |
| 線上版與街機版差異 | 分別產出對應章節，標明差異 |

## 附帶資源

| 資源 | 用途 | 何時讀取 |
|------|------|---------|
| `references/fish-game.md` | 捕魚機規格指南（含海王系列參考、魚種資料庫） | 遊戲類型為捕魚機時 |
| `references/slot-machine.md` | 老虎機規格指南（含符號設計、賠付線、獎勵機制） | 遊戲類型為老虎機時 |
| `references/card-game.md` | 棋牌規格指南（含賠率表、莊家優勢、側注設計） | 遊戲類型為棋牌時 |
