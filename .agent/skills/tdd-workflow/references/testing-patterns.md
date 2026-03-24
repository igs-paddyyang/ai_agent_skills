# 測試設計模式詳解

本文件提供測試設計模式的深入指引，涵蓋測試層級、Mock 進階策略與 Fixture 組織。

## 測試層級金字塔

```
        ╱ E2E 測試 ╲          少量、慢、高信心
       ╱─────────────╲
      ╱  整合測試      ╲       適量、中速
     ╱─────────────────╲
    ╱    單元測試        ╲     大量、快、低成本
   ╱─────────────────────╲
```

### 單元測試

測試單一函式或方法的行為，不依賴外部資源。

特徵：
- 執行速度快（毫秒級）
- 不碰資料庫、網路、檔案系統
- 一個測試只驗證一個行為
- 失敗時能精確定位問題

```python
# 好的單元測試
def test_calculate_discount_for_vip():
    """VIP 會員應享有 20% 折扣"""
    result = calculate_discount(price=100, membership="vip")
    assert result == 80

# 壞的單元測試（測太多東西）
def test_everything():
    user = create_user("test")        # 建立使用者
    order = place_order(user, items)  # 下單
    assert order.total == 80          # 驗證金額
    assert user.points == 10          # 驗證點數
```

### 整合測試

測試多個元件協作的行為。

適用場景：
- 資料庫存取層（Repository）
- API 端點（FastAPI TestClient）
- 外部服務整合

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_create_user_endpoint(client):
    response = client.post("/users", json={"name": "Test", "email": "test@example.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
```

### E2E 測試

測試完整的使用者流程，從入口到出口。

特徵：
- 最接近真實使用情境
- 執行速度慢
- 維護成本高
- 只測關鍵路徑

## Mock 進階策略

### 何時該用 Mock

| 情境 | 用 Mock | 原因 |
|------|---------|------|
| 外部 API | ✅ | 網路不可靠、速度慢、可能收費 |
| 資料庫 | 視情況 | 單元測試用 Mock，整合測試用真實 DB |
| 時間 | ✅ | `datetime.now()` 不可預測 |
| 隨機數 | ✅ | `random` 不可重現 |
| 內部函式 | ❌ | Mock 內部實作 = 測試與實作耦合 |

### Mock 技巧

```python
from unittest.mock import patch, MagicMock

# 1. patch 外部 API
@patch("app.services.requests.get")
def test_fetch_weather(mock_get):
    mock_get.return_value.json.return_value = {"temp": 25}
    result = fetch_weather("Taipei")
    assert result["temp"] == 25

# 2. patch datetime
@patch("app.utils.datetime")
def test_is_business_hours(mock_dt):
    mock_dt.now.return_value = datetime(2026, 1, 1, 10, 0)
    assert is_business_hours() is True

# 3. 使用 fixture 提供 mock
@pytest.fixture
def mock_db():
    db = MagicMock()
    db.query.return_value = [{"id": 1, "name": "Test"}]
    return db
```

### Mock 反模式

1. Mock 太深：`mock.return_value.method.return_value.attr` → 重新設計介面
2. Mock 回傳值不真實：Mock 回傳 `{"data": "ok"}` 但真實 API 回傳 `{"result": {"data": "ok"}}` → 用真實回應建立 fixture
3. 每個測試都 Mock 同一個東西：提取到 conftest.py 的 fixture

## Fixture 組織策略

### 層級結構

```
tests/
├── conftest.py              # 全域 fixture（db_session、client）
├── unit/
│   ├── conftest.py          # 單元測試 fixture（mock_service）
│   └── test_calculator.py
├── integration/
│   ├── conftest.py          # 整合測試 fixture（test_db）
│   └── test_api.py
└── e2e/
    ├── conftest.py          # E2E fixture（browser、test_server）
    └── test_user_flow.py
```

### Fixture 最佳實踐

```python
# conftest.py — 全域共用

@pytest.fixture(scope="session")
def db_engine():
    """整個測試 session 共用一個 DB engine"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """每個測試獨立的 DB session，自動 rollback"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_users():
    """可重用的測試資料"""
    return [
        {"name": "Alice", "role": "admin"},
        {"name": "Bob", "role": "user"},
    ]
```

## 測試命名慣例

格式：`test_<被測行為>_<情境>_<預期結果>`

```python
# 好的命名
def test_validate_email_with_empty_string_returns_error():
def test_calculate_tax_for_zero_amount_returns_zero():
def test_login_with_expired_token_raises_unauthorized():

# 壞的命名
def test_email():          # 太模糊
def test_case_1():         # 無意義
def test_it_works():       # 不知道測什麼
```
