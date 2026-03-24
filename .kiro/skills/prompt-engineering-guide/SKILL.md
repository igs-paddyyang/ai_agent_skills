---
name: prompt-engineering-guide
description: "系統化的 prompt 設計方法論，涵蓋 SKILL.md description 撰寫公式、指令設計原則、常見反模式與修正方式。當使用者提到 prompt engineering、prompt 設計、提示工程、改善 description、優化 prompt、prompt 最佳實踐、指令設計、prompt 技巧、description 撰寫、觸發準確度、prompt optimization 時，請務必使用此技能。"
---

# Prompt 工程指引（Prompt Engineering Guide）

好的 prompt 讓 AI 做對的事。壞的 prompt 讓 AI 做很多事，但沒一件對。
這份指引幫你寫出精準、可靠的 prompt，特別是 Kiro Skill 的 description 和指令。

## 使用時機

- 撰寫或改善 SKILL.md 的 description
- 設計技能的核心指令
- 檢視 prompt 品質並提出改善建議
- 學習 prompt engineering 方法論
- 需要提升技能觸發準確度

## 核心原則

```
具體 > 模糊。範例 > 解釋。結構 > 散文。
```

AI 不會讀心。你越具體，它越準確。

## Description 撰寫公式

Kiro Skill 的 description 決定技能何時被觸發。好的 description 同時包含兩個部分：

```
[做什麼（功能描述）] + [什麼時候用（觸發情境關鍵字）]
```

### 公式拆解

| 部分 | 目的 | 範例 |
|------|------|------|
| 功能描述 | 讓 AI 理解技能能力 | 「引導開發者遵循 TDD 的 Red-Green-Refactor 循環」 |
| 觸發關鍵字 | 讓 AI 知道何時觸發 | 「當使用者提到 TDD、測試驅動開發、先寫測試...時」 |

### 好的 Description 範例

```yaml
# ✅ 好：功能清楚 + 觸發情境豐富
description: "引導開發者遵循測試驅動開發（TDD）的 Red-Green-Refactor 循環，
在撰寫實作程式碼之前先寫測試。涵蓋 pytest 測試設計、邊界值分析、Mock 策略
與測試反模式。當使用者提到 TDD、測試驅動開發、先寫測試、test-driven 
development、寫測試、測試案例設計、pytest、單元測試、測試策略、
Red-Green-Refactor 時，請務必使用此技能。"
```

### 壞的 Description 範例

```yaml
# ❌ 太模糊
description: "幫助使用者寫測試"

# ❌ 只有功能，沒有觸發情境
description: "提供完整的 TDD 工作流指引，包含 Red-Green-Refactor 循環"

# ❌ 只有關鍵字，沒有功能描述
description: "當使用者提到 TDD、測試、pytest 時使用"

# ❌ 超過 1024 字元（Kiro 平台限制）
description: "這是一個非常詳細的描述，包含了所有可能的使用情境..."
```

### Description 檢核清單

- [ ] 第一句話說明「這個技能做什麼」
- [ ] 包含 5-15 個觸發關鍵字（中英文混合）
- [ ] 關鍵字涵蓋：正式名稱、口語說法、英文術語
- [ ] 總長度 ≤ 1024 字元
- [ ] 使用雙引號包裹（避免 YAML 解析問題）

## 指令設計原則

### 1. 祈使句風格

直接告訴 AI 要做什麼，不要解釋為什麼。

```markdown
# ❌ 解釋式
測試驅動開發是一種軟體開發方法論，它強調在撰寫實作程式碼之前先寫測試...

# ✅ 祈使句
在寫實作程式碼之前先寫測試。看著測試失敗，再寫最少的程式碼讓它通過。
```

### 2. 漸進式揭露

不要一次給所有資訊。分層提供：

```
SKILL.md 本體（核心流程，<500 行）
  ↓ 需要更多細節時
references/（詳細指南，按需載入）
```

### 3. 結構化格式

用表格、清單、程式碼區塊取代長段落。

```markdown
# ❌ 散文
Mock 應該只在外部 API 呼叫、資料庫操作、時間相關邏輯和隨機數的情況下使用。
不要 Mock 太多東西，也不要 Mock 內部實作。

# ✅ 結構化
只在以下情況使用 Mock：
- 外部 API 呼叫（網路不可靠）
- 資料庫操作（測試速度）
- 時間相關邏輯（`datetime.now()`）
- 隨機數（`random`）
```

### 4. 具體範例

每個規則都附上「好」和「壞」的對比範例。

```markdown
# ❌ 只有規則
測試名稱要清楚描述行為。

# ✅ 規則 + 範例
測試名稱要清楚描述行為：
- ✅ `test_rejects_empty_email`
- ❌ `test_email`
- ❌ `test_case_1`
```

### 5. 限制與邊界

明確告訴 AI 什麼不要做。

```markdown
不要：
- 加額外功能
- 重構其他程式碼
- 「順便改善」超出測試範圍的東西
```

## 常見反模式與修正

| 反模式 | 問題 | 修正 |
|--------|------|------|
| 堆砌 MUST/SHALL | 讀起來像法律文件，AI 容易忽略 | 用祈使句，解釋為什麼重要 |
| 過度抽象 | 「確保程式碼品質」→ AI 不知道具體要做什麼 | 列出具體檢查項目 |
| 缺少範例 | AI 猜測你的期望 | 每個規則附上好/壞對比 |
| 一次給太多 | AI 容易遺漏後面的指令 | 分層揭露，核心放前面 |
| 矛盾指令 | 「要簡潔」但又「要詳細說明每個步驟」 | 明確優先順序 |
| 假設 AI 知道 | 「用我們的標準格式」→ AI 不知道你的標準 | 直接給出格式範例 |

## Prompt 品質自我檢核

對任何 prompt（不只是 SKILL.md），用這個清單檢查：

1. 目標明確嗎？（AI 讀完知道要做什麼？）
2. 有具體範例嗎？（至少一個輸入→輸出範例）
3. 有限制條件嗎？（什麼不要做？）
4. 格式清楚嗎？（期望的輸出格式是什麼？）
5. 可測試嗎？（怎麼判斷 AI 做對了？）

## SKILL.md 品質評分

| 分數 | 標準 |
|------|------|
| ⭐⭐⭐⭐⭐ | description 精準觸發 + 指令結構清晰 + 豐富範例 + 明確限制 |
| ⭐⭐⭐⭐ | description 觸發正確 + 指令清楚 + 有範例 |
| ⭐⭐⭐ | description 基本可用 + 指令可理解 |
| ⭐⭐ | description 模糊 + 指令缺少範例 |
| ⭐ | description 無法觸發 + 指令混亂 |

## 改善既有技能的流程

1. 讀取目標技能的 SKILL.md
2. 用 Description 檢核清單評估 description
3. 用品質評分表評估整體品質
4. 產出具體改善建議（含修改前/後對比）
5. 確認修改後仍符合 Kiro 規範（≤1024 字元、雙引號包裹）

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/anthropic-best-practices.md | Anthropic 官方 prompt 最佳實踐摘要 | 需要深入 prompt 理論時 |
| references/skill-description-examples.md | 優秀 description 範例集與分析 | 需要更多 description 撰寫靈感時 |
