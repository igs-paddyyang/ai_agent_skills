# 常用設計模式詳解

本文件提供 Python 環境下常用設計模式的詳細說明與實作範例。

## Strategy 模式（策略模式）

將演算法封裝成可替換的物件，讓演算法可以獨立於使用它的客戶端而變化。

Python 的優勢：函式是一等公民，Strategy 可以直接用函式實作。

```python
# 方式一：用函式（推薦）
def sort_by_price(items):
    return sorted(items, key=lambda x: x["price"])

def sort_by_name(items):
    return sorted(items, key=lambda x: x["name"])

def display_products(items, sort_strategy=sort_by_price):
    sorted_items = sort_strategy(items)
    for item in sorted_items:
        print(f"{item['name']}: ${item['price']}")

# 使用
display_products(products, sort_strategy=sort_by_name)
```

```python
# 方式二：用 Protocol（需要狀態時）
from typing import Protocol

class PricingStrategy(Protocol):
    def calculate(self, base_price: float, quantity: int) -> float: ...

class RegularPricing:
    def calculate(self, base_price: float, quantity: int) -> float:
        return base_price * quantity

class BulkPricing:
    def __init__(self, threshold: int, discount: float):
        self.threshold = threshold
        self.discount = discount

    def calculate(self, base_price: float, quantity: int) -> float:
        if quantity >= self.threshold:
            return base_price * quantity * (1 - self.discount)
        return base_price * quantity

class OrderCalculator:
    def __init__(self, pricing: PricingStrategy):
        self.pricing = pricing

    def total(self, base_price: float, quantity: int) -> float:
        return self.pricing.calculate(base_price, quantity)
```

## Observer 模式（觀察者模式）

當一個物件狀態改變時，自動通知所有依賴它的物件。

```python
from typing import Callable

class EventBus:
    """簡單的事件匯流排"""
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event: str, handler: Callable):
        self._handlers.setdefault(event, []).append(handler)

    def publish(self, event: str, data=None):
        for handler in self._handlers.get(event, []):
            handler(data)

# 使用
bus = EventBus()

def on_order_created(order):
    print(f"發送確認信給 {order['customer']}")

def on_order_created_log(order):
    print(f"記錄訂單 {order['id']}")

bus.subscribe("order.created", on_order_created)
bus.subscribe("order.created", on_order_created_log)

# 觸發事件
bus.publish("order.created", {"id": "001", "customer": "Alice"})
```

## Factory 模式（工廠模式）

封裝物件建立邏輯，讓客戶端不需要知道具體類別。

```python
# 工廠函式（Python 最常用的方式）
def create_notifier(channel: str):
    notifiers = {
        "email": EmailNotifier,
        "sms": SMSNotifier,
        "telegram": TelegramNotifier,
    }
    notifier_class = notifiers.get(channel)
    if not notifier_class:
        raise ValueError(f"不支援的通知管道: {channel}")
    return notifier_class()

# classmethod 工廠
class DatabaseConnection:
    def __init__(self, engine, connection_string):
        self.engine = engine
        self.connection_string = connection_string

    @classmethod
    def sqlite(cls, path: str):
        return cls("sqlite", f"sqlite:///{path}")

    @classmethod
    def postgres(cls, host: str, db: str):
        return cls("postgres", f"postgresql://{host}/{db}")

# 使用
db = DatabaseConnection.sqlite("app.db")
```

## Repository 模式

抽象資料存取層，讓業務邏輯不依賴具體的資料庫實作。

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str

class UserRepository(Protocol):
    def save(self, user: User) -> None: ...
    def find_by_id(self, user_id: str) -> User | None: ...
    def find_all(self) -> list[User]: ...
    def delete(self, user_id: str) -> None: ...

# SQLite 實作
class SQLiteUserRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save(self, user: User) -> None:
        # INSERT OR REPLACE ...
        pass

    def find_by_id(self, user_id: str) -> User | None:
        # SELECT ... WHERE id = ?
        pass

# 記憶體實作（測試用）
class InMemoryUserRepository:
    def __init__(self):
        self._store: dict[str, User] = {}

    def save(self, user: User) -> None:
        self._store[user.id] = user

    def find_by_id(self, user_id: str) -> User | None:
        return self._store.get(user_id)

    def find_all(self) -> list[User]:
        return list(self._store.values())

    def delete(self, user_id: str) -> None:
        self._store.pop(user_id, None)
```

## Adapter 模式（轉接器模式）

將一個介面轉換成另一個介面，讓不相容的類別可以合作。

```python
# 舊的 API 回傳 XML 格式
class LegacyWeatherAPI:
    def get_weather_xml(self, city: str) -> str:
        return f"<weather><city>{city}</city><temp>25</temp></weather>"

# 新系統期望 dict 格式
class WeatherAdapter:
    def __init__(self, legacy_api: LegacyWeatherAPI):
        self.legacy_api = legacy_api

    def get_weather(self, city: str) -> dict:
        xml = self.legacy_api.get_weather_xml(city)
        # 解析 XML → dict
        return {"city": city, "temp": 25}

# 使用
adapter = WeatherAdapter(LegacyWeatherAPI())
weather = adapter.get_weather("Taipei")  # {"city": "Taipei", "temp": 25}
```

## 模式選擇指南

| 問題 | 推薦模式 |
|------|---------|
| 需要在執行時切換演算法 | Strategy |
| 需要在狀態改變時通知多個物件 | Observer |
| 需要封裝複雜的物件建立邏輯 | Factory |
| 需要抽象資料存取層 | Repository |
| 需要整合不相容的介面 | Adapter |
| 需要全域唯一的實例 | 模組級變數（Python 天然 Singleton） |
| 需要為物件動態加入行為 | Decorator（Python 內建 `@decorator`） |
