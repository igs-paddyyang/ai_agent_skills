# 優秀 Description 範例集

本文件收集本專案中優秀的 SKILL.md description 範例，分析其結構並提供改善建議。

## 評分標準

| 維度 | 權重 | 說明 |
|------|------|------|
| 功能描述清晰度 | 30% | 讀完第一句就知道技能做什麼 |
| 觸發關鍵字覆蓋度 | 30% | 中英文、正式/口語、同義詞 |
| 長度適當性 | 20% | 200-800 字元最佳，≤1024 字元 |
| 格式正確性 | 20% | 雙引號包裹、無 YAML 特殊字元 |

## 範例分析

### ⭐⭐⭐⭐⭐ tdd-workflow

```yaml
description: "引導開發者遵循測試驅動開發（TDD）的 Red-Green-Refactor 循環，
在撰寫實作程式碼之前先寫測試。涵蓋 pytest 測試設計、邊界值分析、Mock 策略
與測試反模式。當使用者提到 TDD、測試驅動開發、先寫測試、test-driven 
development、寫測試、測試案例設計、pytest、單元測試、測試策略、
Red-Green-Refactor 時，請務必使用此技能。"
```

分析：
- ✅ 第一句明確說明功能（引導 TDD 循環）
- ✅ 補充涵蓋範圍（pytest、邊界值、Mock）
- ✅ 10 個觸發關鍵字，中英文混合
- ✅ 包含口語說法（「先寫測試」「寫測試」）
- ✅ 雙引號包裹

### ⭐⭐⭐⭐⭐ software-architecture-guide

```yaml
description: "提供軟體架構決策的結構化指引，涵蓋 Clean Architecture 分層原則、
SOLID 原則的 Python 實踐、常用設計模式與架構決策紀錄（ADR）。當使用者提到
軟體架構、架構設計、Clean Architecture、SOLID、設計模式、design pattern、
架構決策、ADR、分層架構、DDD、領域驅動設計、software architecture、
架構指引、系統設計時，請務必使用此技能。"
```

分析：
- ✅ 功能描述具體（架構決策指引）
- ✅ 列出核心涵蓋範圍（Clean Architecture、SOLID、ADR）
- ✅ 14 個觸發關鍵字
- ✅ 涵蓋相關領域（DDD、系統設計）

### ⭐⭐⭐ 需要改善的範例

```yaml
# 假設的壞範例
description: "幫助使用者進行軟體開發"
```

問題：
- ❌ 太模糊，幾乎任何開發問題都會觸發
- ❌ 沒有觸發關鍵字
- ❌ 無法區分與其他技能的差異

改善後：
```yaml
description: "幫助使用者進行 Python 程式碼重構，涵蓋函式提取、
命名改善、重複消除與設計模式應用。當使用者提到重構、refactor、
程式碼改善、code smell、提取函式、消除重複時，請務必使用此技能。"
```

## Description 撰寫模板

```yaml
description: "[一句話功能描述]，涵蓋 [核心能力 1]、[核心能力 2]、
[核心能力 3]。當使用者提到 [關鍵字 1]、[關鍵字 2]、[關鍵字 3]、
[英文關鍵字 1]、[英文關鍵字 2]、[口語說法 1]、[口語說法 2] 時，
請務必使用此技能。"
```

## 關鍵字設計策略

| 策略 | 範例 |
|------|------|
| 正式名稱 | 測試驅動開發、Clean Architecture |
| 英文術語 | TDD、test-driven development、SOLID |
| 口語說法 | 先寫測試、寫測試、幫我測試 |
| 縮寫 | ADR、DDD、MCP |
| 相關概念 | 單元測試、pytest、邊界值分析 |
| 動作導向 | 幫我做架構決策、檢查 SOLID 原則 |

建議每個 description 包含 8-15 個關鍵字，涵蓋以上至少 3 種策略。
