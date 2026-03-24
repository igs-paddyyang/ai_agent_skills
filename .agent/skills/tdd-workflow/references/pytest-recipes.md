# pytest 常用配方

本文件提供 pytest 進階用法，涵蓋 conftest.py 配置、自訂 marker、plugin 與 coverage 設定。

## conftest.py 配置

conftest.py 是 pytest 的自動載入機制，放在測試目錄中會自動被發現。

### 常用配置範例

```python
# tests/conftest.py
import pytest
import os

# 設定測試環境變數
@pytest.fixture(autouse=True, scope="session")
def setup_test_env():
    os.environ["ENV"] = "test"
    os.environ["LOG_LEVEL"] = "WARNING"
    yield
    # 清理（選用）

# 共用的 HTTP client
@pytest.fixture
def api_client():
    from app.main import create_app
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

# 臨時目錄
@pytest.fixture
def temp_dir(tmp_path):
    """提供一個預先建立好子目錄的臨時路徑"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
```

## 自訂 Marker

### 定義 marker

```ini
# pytest.ini 或 pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: 執行時間較長的測試",
    "integration: 整合測試（需要外部服務）",
    "e2e: 端對端測試",
]
```

### 使用 marker

```python
import pytest

@pytest.mark.slow
def test_large_data_processing():
    # 處理大量資料...
    pass

@pytest.mark.integration
def test_database_connection():
    # 連接真實資料庫...
    pass

# 條件式跳過
@pytest.mark.skipif(
    os.environ.get("CI") != "true",
    reason="只在 CI 環境執行"
)
def test_deployment_check():
    pass
```

### 執行特定 marker

```bash
# 只跑快速測試（排除 slow）
pytest -m "not slow"

# 只跑整合測試
pytest -m integration

# 組合條件
pytest -m "not slow and not e2e"
```

## 參數化測試進階

### 多參數組合

```python
@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, -100, 0),
])
def test_add(x, y, expected):
    assert add(x, y) == expected
```

### 參數化 + ID

```python
@pytest.mark.parametrize("input_data,expected", [
    pytest.param({"name": "Alice"}, True, id="valid-user"),
    pytest.param({}, False, id="empty-dict"),
    pytest.param(None, False, id="none-input"),
])
def test_validate_user(input_data, expected):
    assert validate_user(input_data) == expected
```

### 多層參數化（笛卡爾積）

```python
@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("path", ["/api/users", "/api/items"])
def test_auth_required(client, method, path):
    """所有 API 端點都需要認證"""
    response = getattr(client, method.lower())(path)
    assert response.status_code == 401
```

## 常用 Plugin

| Plugin | 用途 | 安裝 |
|--------|------|------|
| pytest-cov | 測試覆蓋率 | `pip install pytest-cov` |
| pytest-xdist | 平行執行測試 | `pip install pytest-xdist` |
| pytest-mock | 簡化 mock 語法 | `pip install pytest-mock` |
| pytest-asyncio | 測試 async 函式 | `pip install pytest-asyncio` |
| pytest-timeout | 設定測試超時 | `pip install pytest-timeout` |

### pytest-cov 使用

```bash
# 基本覆蓋率報告
pytest --cov=app tests/

# HTML 報告
pytest --cov=app --cov-report=html tests/

# 設定最低覆蓋率門檻
pytest --cov=app --cov-fail-under=80 tests/
```

### pytest-mock 使用

```python
def test_send_email(mocker):
    """mocker 是 pytest-mock 提供的 fixture"""
    mock_send = mocker.patch("app.services.send_email")
    mock_send.return_value = True

    result = notify_user("test@example.com", "Hello")
    
    assert result is True
    mock_send.assert_called_once_with("test@example.com", "Hello")
```

### pytest-asyncio 使用

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("https://api.example.com/data")
    assert result["status"] == "ok"
```

## pyproject.toml 完整配置範例

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: 執行時間較長的測試",
    "integration: 整合測試",
]

[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
show_missing = true
fail_under = 80
```

## 除錯技巧

```bash
# 顯示 print 輸出
pytest -s

# 遇到第一個失敗就停止
pytest -x

# 只跑上次失敗的測試
pytest --lf

# 先跑上次失敗的，再跑其他
pytest --ff

# 顯示最慢的 10 個測試
pytest --durations=10

# 進入 pdb 除錯器
pytest --pdb
```
