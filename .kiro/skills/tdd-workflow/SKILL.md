---
name: tdd-workflow
description: "引導開發者遵循測試驅動開發（TDD）的 Red-Green-Refactor 循環，在撰寫實作程式碼之前先寫測試。涵蓋 pytest 測試設計、邊界值分析、Mock 策略與測試反模式。當使用者提到 TDD、測試驅動開發、先寫測試、test-driven development、寫測試、測試案例設計、pytest、單元測試、測試策略、Red-Green-Refactor 時，請務必使用此技能。"
---

# 測試驅動開發工作流（TDD Workflow）

在寫實作程式碼之前先寫測試。看著測試失敗，再寫最少的程式碼讓它通過。
這不是教條，而是最務實的開發方式——因為你永遠知道程式碼是否正確。

## 使用時機

- 實作新功能前
- 修復 Bug 前（先寫重現 Bug 的測試）
- 重構程式碼時（確保行為不變）
- 設計測試案例時
- 需要測試策略建議時

## 核心原則：鐵律

```
沒有失敗的測試，就不寫產品程式碼
```

先寫了程式碼再補測試？刪掉重來。不要保留當「參考」，不要「改寫」成測試。
測試後補的問題：測試立刻通過，你無法證明它真的在測什麼。

## Red-Green-Refactor 循環

### RED — 寫一個失敗的測試

寫一個最小的測試，描述「應該發生什麼」。

要求：
- 一個測試只測一個行為
- 測試名稱清楚描述行為（名稱裡有「and」？拆開）
- 用真實程式碼，除非不得已才用 Mock

```python
def test_rejects_empty_email():
    """空白 email 應該被拒絕"""
    result = validate_email("")
    assert result.is_valid is False
    assert "必填" in result.error
```

### 驗證 RED — 看著它失敗

執行測試，確認：
- 測試「失敗」（不是「錯誤」）
- 失敗原因是功能尚未實作（不是拼字錯誤）
- 失敗訊息符合預期

```bash
pytest tests/test_validator.py::test_rejects_empty_email -v
```

測試通過了？你在測已有的行為，修改測試。
測試報錯了？修正錯誤，重跑直到正確失敗。

### GREEN — 寫最少的程式碼讓測試通過

只寫剛好讓測試通過的程式碼，不多不少。

```python
def validate_email(email: str) -> ValidationResult:
    if not email.strip():
        return ValidationResult(is_valid=False, error="Email 為必填欄位")
    return ValidationResult(is_valid=True, error=None)
```

不要：加額外功能、重構其他程式碼、「順便改善」超出測試範圍的東西。

### 驗證 GREEN — 看著它通過

```bash
pytest tests/test_validator.py -v
```

確認：新測試通過、其他測試也通過、輸出乾淨無警告。

### REFACTOR — 清理

只在 GREEN 之後才重構：
- 移除重複
- 改善命名
- 提取輔助函式

保持測試全綠。不要在重構時加新行為。

### 重複

下一個失敗測試，下一個功能。

## 測試設計模式

### 邊界值分析

| 類型 | 範例 |
|------|------|
| 空值 | `None`、`""`、`[]`、`{}` |
| 邊界 | 0、1、-1、最大值、最小值 |
| 型別 | 字串 vs 數字、整數 vs 浮點數 |
| 格式 | 有/無空白、大小寫、特殊字元 |

### 等價類劃分

將輸入分成「應該有相同行為」的群組，每組取一個代表值測試：
- 有效輸入群組（正常路徑）
- 無效輸入群組（錯誤路徑）
- 邊界值群組

### Mock 策略

只在以下情況使用 Mock：
- 外部 API 呼叫（網路不可靠）
- 資料庫操作（測試速度）
- 時間相關邏輯（`datetime.now()`）
- 隨機數（`random`）

Mock 的反模式：
- Mock 太多 → 測試只在測 Mock，不是測程式碼
- Mock 內部實作 → 重構就壞
- Mock 回傳值不真實 → 測試通過但實際會失敗

## pytest 快速參考

```bash
# 執行單一測試
pytest tests/test_foo.py::test_bar -v

# 執行整個目錄
pytest tests/ -v

# 只跑上次失敗的
pytest --lf

# 顯示 print 輸出
pytest -s

# 參數化測試
pytest tests/test_foo.py -v -k "email"
```

### 參數化測試

```python
import pytest

@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("", False),
    ("no-at-sign", False),
    ("@no-local", False),
])
def test_email_validation(email, expected):
    result = validate_email(email)
    assert result.is_valid == expected
```

### Fixture 管理

```python
@pytest.fixture
def sample_user():
    return {"name": "Test User", "email": "test@example.com"}

@pytest.fixture
def db_session():
    session = create_test_session()
    yield session
    session.rollback()
```

## 常見藉口與現實

| 藉口 | 現實 |
|------|------|
| 「太簡單不用測」 | 簡單的程式碼也會壞。測試只要 30 秒 |
| 「之後再補測試」 | 後補的測試立刻通過，證明不了什麼 |
| 「手動測過了」 | 手動測試無法重複、無法記錄、下次改動又要重測 |
| 「TDD 太慢了」 | TDD 比 debug 快。務實 = 先寫測試 |
| 「先探索再說」 | 可以。探索完刪掉，用 TDD 重寫 |
| 「測試難寫 = 設計有問題」 | 沒錯。難測試 = 難使用。聽測試的話，改設計 |

## Bug 修復流程

1. 寫一個重現 Bug 的失敗測試
2. 看著它失敗（確認測試真的抓到 Bug）
3. 修復 Bug
4. 看著測試通過
5. 測試永遠留著，防止回歸

永遠不要不寫測試就修 Bug。

## 完成前檢查清單

- [ ] 每個新函式/方法都有測試
- [ ] 每個測試都先看過失敗
- [ ] 每個失敗原因都是「功能缺失」而非「拼字錯誤」
- [ ] 寫了最少的程式碼讓測試通過
- [ ] 所有測試通過
- [ ] 輸出乾淨（無錯誤、無警告）
- [ ] 邊界案例和錯誤處理都有覆蓋

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/testing-patterns.md | 測試設計模式詳解：單元/整合/E2E、Mock 進階策略、Fixture 組織 | 需要深入測試設計時 |
| references/pytest-recipes.md | pytest 常用配方：conftest.py、plugin、自訂 marker、coverage | 需要 pytest 進階用法時 |
