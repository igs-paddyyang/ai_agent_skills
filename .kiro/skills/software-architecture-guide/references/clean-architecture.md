# Clean Architecture 詳細指南

本文件深入說明 Clean Architecture 的分層原則，提供完整的 Python 專案結構範例。

## 目錄結構範例

```
project/
├── domain/                    # Entities（核心層）
│   ├── models.py              # 領域物件（dataclass）
│   ├── value_objects.py       # 值物件
│   └── exceptions.py          # 領域例外
├── use_cases/                 # Use Cases（應用層）
│   ├── create_order.py        # 建立訂單用例
│   ├── cancel_order.py        # 取消訂單用例
│   └── interfaces.py          # Repository 介面定義
├── adapters/                  # Interface Adapters（轉接層）
│   ├── repositories/
│   │   ├── sqlite_order_repo.py
│   │   └── memory_order_repo.py
│   ├── controllers/
│   │   └── order_controller.py
│   └── presenters/
│       └── order_presenter.py
└── frameworks/                # Frameworks（最外層）
    ├── web/
    │   └── fastapi_app.py
    ├── db/
    │   └── sqlite_connection.py
    └── bot/
        └── telegram_bot.py
```

## 各層詳細說明

### Domain（Entities）

領域層是整個系統的核心，只包含業務規則，不依賴任何外部套件。

```python
# domain/models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

@dataclass
class OrderItem:
    product_name: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price

@dataclass
class Order:
    id: str
    customer_id: str
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def confirm(self):
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"無法確認狀態為 {self.status.value} 的訂單")
        self.status = OrderStatus.CONFIRMED

    def cancel(self):
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("訂單已取消")
        self.status = OrderStatus.CANCELLED
```

```python
# domain/exceptions.py
class DomainError(Exception):
    """領域層基礎例外"""

class OrderNotFoundError(DomainError):
    def __init__(self, order_id: str):
        super().__init__(f"找不到訂單: {order_id}")

class InsufficientStockError(DomainError):
    def __init__(self, product: str):
        super().__init__(f"庫存不足: {product}")
```

### Use Cases（應用層）

應用層編排領域物件的操作，定義「系統能做什麼」。

```python
# use_cases/interfaces.py
from typing import Protocol
from domain.models import Order

class OrderRepository(Protocol):
    """Repository 介面 — 定義在應用層，實作在轉接層"""
    def save(self, order: Order) -> None: ...
    def find_by_id(self, order_id: str) -> Order | None: ...
    def find_by_customer(self, customer_id: str) -> list[Order]: ...

class NotificationService(Protocol):
    """通知服務介面"""
    def notify(self, customer_id: str, message: str) -> None: ...
```

```python
# use_cases/create_order.py
from domain.models import Order, OrderItem
from use_cases.interfaces import OrderRepository, NotificationService

class CreateOrderUseCase:
    def __init__(self, order_repo: OrderRepository, notifier: NotificationService):
        self.order_repo = order_repo
        self.notifier = notifier

    def execute(self, customer_id: str, items: list[dict]) -> Order:
        order_items = [
            OrderItem(
                product_name=item["product"],
                quantity=item["quantity"],
                unit_price=item["price"],
            )
            for item in items
        ]
        order = Order(
            id=generate_id(),
            customer_id=customer_id,
            items=order_items,
        )
        self.order_repo.save(order)
        self.notifier.notify(customer_id, f"訂單 {order.id} 已建立，金額 {order.total}")
        return order
```

### Adapters（轉接層）

轉接層實作應用層定義的介面，負責資料格式轉換。

```python
# adapters/repositories/sqlite_order_repo.py
import sqlite3
from domain.models import Order, OrderItem, OrderStatus

class SQLiteOrderRepository:
    """實作 OrderRepository 介面"""
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save(self, order: Order) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (id, customer_id, status) VALUES (?, ?, ?)",
            (order.id, order.customer_id, order.status.value),
        )
        for item in order.items:
            cursor.execute(
                "INSERT INTO order_items (order_id, product, qty, price) VALUES (?, ?, ?, ?)",
                (order.id, item.product_name, item.quantity, item.unit_price),
            )
        conn.commit()
        conn.close()

    def find_by_id(self, order_id: str) -> Order | None:
        # 查詢實作...
        pass
```

```python
# adapters/repositories/memory_order_repo.py
from domain.models import Order

class InMemoryOrderRepository:
    """記憶體實作 — 用於測試"""
    def __init__(self):
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.id] = order

    def find_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def find_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]
```

## 測試策略

Clean Architecture 的最大好處：核心邏輯可以不依賴任何外部資源來測試。

```python
# tests/test_create_order.py
from use_cases.create_order import CreateOrderUseCase
from adapters.repositories.memory_order_repo import InMemoryOrderRepository

class FakeNotifier:
    def __init__(self):
        self.messages = []
    def notify(self, customer_id, message):
        self.messages.append((customer_id, message))

def test_create_order():
    repo = InMemoryOrderRepository()
    notifier = FakeNotifier()
    use_case = CreateOrderUseCase(repo, notifier)

    order = use_case.execute("customer-1", [
        {"product": "Widget", "quantity": 2, "price": 10.0},
    ])

    assert order.total == 20.0
    assert repo.find_by_id(order.id) is not None
    assert len(notifier.messages) == 1
```

## 常見違規與修正

| 違規 | 問題 | 修正 |
|------|------|------|
| Use Case 直接 import SQLite | 核心邏輯綁死資料庫 | 定義 Repository Protocol，注入實作 |
| Entity 裡呼叫 API | 領域物件依賴外部服務 | 把 API 呼叫移到 Use Case 或 Adapter |
| Controller 包含業務邏輯 | 邏輯散落在框架層 | 提取到 Use Case |
| 跨層直接存取 | 外層直接操作 Entity 內部狀態 | 透過 Entity 方法操作 |
