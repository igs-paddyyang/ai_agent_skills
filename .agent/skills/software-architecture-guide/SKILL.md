---
name: software-architecture-guide
description: "提供軟體架構決策的結構化指引，涵蓋 Clean Architecture 分層原則、SOLID 原則的 Python 實踐、常用設計模式與架構決策紀錄（ADR）。當使用者提到軟體架構、架構設計、Clean Architecture、SOLID、設計模式、design pattern、架構決策、ADR、分層架構、DDD、領域驅動設計、software architecture、架構指引、系統設計、怎麼分層時，請務必使用此技能。"
---

# 軟體架構指引（Software Architecture Guide）

好的架構讓改動便宜。壞的架構讓每次改動都像在拆炸彈。
這份指引幫你做出有根據的架構決策，而不是憑直覺。

## 使用時機

- 新專案需要選擇架構模式
- 既有專案需要重構或分層
- 需要記錄架構決策（ADR）
- 評估設計模式的適用性
- 檢視程式碼是否符合 SOLID 原則

## 核心原則：依賴方向

```
外層依賴內層，內層不知道外層的存在。
```

所有架構模式的共同點：業務邏輯不依賴框架、資料庫、UI。
違反這條規則，你的程式碼就被框架綁架了。

## Clean Architecture 分層

```
┌─────────────────────────────────────┐
│  Framework & Drivers（最外層）       │  FastAPI、SQLAlchemy、Telegram SDK
│  ┌─────────────────────────────┐    │
│  │  Interface Adapters          │    │  Controllers、Presenters、Gateways
│  │  ┌─────────────────────┐    │    │
│  │  │  Use Cases           │    │    │  應用邏輯、業務流程編排
│  │  │  ┌─────────────┐    │    │    │
│  │  │  │  Entities    │    │    │    │  核心業務規則、領域物件
│  │  │  └─────────────┘    │    │    │
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### 各層職責

| 層級 | 職責 | Python 對應 | 依賴方向 |
|------|------|------------|---------|
| Entities | 核心業務規則 | dataclass、純 Python 類別 | 不依賴任何外層 |
| Use Cases | 應用邏輯 | 函式或類別，編排 Entity 操作 | 只依賴 Entity |
| Interface Adapters | 轉換資料格式 | Repository 實作、API Controller | 依賴 Use Case |
| Frameworks | 外部工具 | FastAPI、SQLAlchemy、Bot SDK | 依賴 Adapter |

### Python 範例

```python
# === Entities（核心層）===
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str

    def is_valid_email(self) -> bool:
        return "@" in self.email and "." in self.email

# === Use Cases（應用層）===
class CreateUserUseCase:
    def __init__(self, user_repo):  # 依賴注入，不直接依賴實作
        self.user_repo = user_repo

    def execute(self, name: str, email: str) -> User:
        user = User(id=generate_id(), name=name, email=email)
        if not user.is_valid_email():
            raise ValueError("無效的 email 格式")
        self.user_repo.save(user)
        return user

# === Interface Adapters（轉接層）===
class SQLiteUserRepository:
    """實作 user_repo 介面"""
    def save(self, user: User):
        # SQLite 操作...
        pass

# === Frameworks（最外層）===
from fastapi import FastAPI
app = FastAPI()

@app.post("/users")
def create_user(name: str, email: str):
    repo = SQLiteUserRepository()
    use_case = CreateUserUseCase(repo)
    return use_case.execute(name, email)
```

## SOLID 原則

### S — 單一職責（Single Responsibility）

一個模組只有一個改變的理由。

```python
# ❌ 混合職責
class UserService:
    def create_user(self, data): ...
    def send_welcome_email(self, user): ...
    def generate_report(self, users): ...

# ✅ 分離職責
class UserService:
    def create_user(self, data): ...

class EmailService:
    def send_welcome_email(self, user): ...

class ReportGenerator:
    def generate_report(self, users): ...
```

### O — 開放封閉（Open/Closed）

對擴展開放，對修改封閉。用多型取代 if-else 鏈。

```python
# ❌ 每加一種通知就要改這個函式
def notify(user, channel):
    if channel == "email":
        send_email(user)
    elif channel == "sms":
        send_sms(user)
    elif channel == "telegram":
        send_telegram(user)

# ✅ 新增通知管道不需要改既有程式碼
class Notifier:
    def notify(self, user): ...

class EmailNotifier(Notifier):
    def notify(self, user): send_email(user)

class TelegramNotifier(Notifier):
    def notify(self, user): send_telegram(user)
```

### L — 里氏替換（Liskov Substitution）

子類別必須能替換父類別，不改變程式行為。

### I — 介面隔離（Interface Segregation）

不要強迫實作用不到的方法。Python 用 Protocol 或 ABC。

```python
from typing import Protocol

class Readable(Protocol):
    def read(self) -> str: ...

class Writable(Protocol):
    def write(self, data: str) -> None: ...

# 只需要讀取的地方，只要求 Readable
def process_input(source: Readable):
    data = source.read()
    # ...
```

### D — 依賴反轉（Dependency Inversion）

高層模組不依賴低層模組，兩者都依賴抽象。

```python
# ❌ 直接依賴具體實作
class OrderService:
    def __init__(self):
        self.db = SQLiteDatabase()  # 綁死 SQLite

# ✅ 依賴抽象
class OrderService:
    def __init__(self, db):  # 注入任何實作
        self.db = db
```

## 架構決策紀錄（ADR）

當你做了一個重要的架構決策，寫下來。未來的你（或隊友）會感謝你。

### ADR 格式

```markdown
# ADR-001: 選擇 FastAPI 作為 Web 框架

## 狀態
已採用

## 背景
需要一個支援 async 的 Python Web 框架，用於 ArkBot 的 Web 對話介面。

## 決策
選擇 FastAPI。

## 理由
- 原生支援 async/await
- 自動產生 OpenAPI 文件
- 型別提示驅動的參數驗證
- 效能優於 Flask

## 替代方案
- Flask：生態系成熟但不原生支援 async
- Django：功能太重，不適合輕量 API

## 後果
- 團隊需要學習 Pydantic 和 async 模式
- 部署需要 ASGI 伺服器（uvicorn）
```

## 常用設計模式速查

| 模式 | 用途 | Python 實作方式 |
|------|------|----------------|
| Strategy | 可替換的演算法 | 傳入函式或 Protocol 物件 |
| Observer | 事件通知 | callback list 或 Event class |
| Factory | 建立物件 | 工廠函式或 classmethod |
| Repository | 資料存取抽象 | Protocol + 具體實作 |
| Adapter | 介面轉換 | 包裝類別 |
| Singleton | 全域唯一實例 | 模組級變數（Python 天然 Singleton） |

## 與 ArkBot 架構的對應

| Clean Architecture 層 | ArkBot 四層架構 | 說明 |
|----------------------|----------------|------|
| Entities | Foundation | 核心資料模型、設定管理 |
| Use Cases | Decision Engine | 意圖分類、Skill 路由 |
| Interface Adapters | Skill Runtime | Skill Registry、Executor |
| Frameworks | Integration | Telegram SDK、FastAPI、Web UI |

## 架構檢查清單

- [ ] 業務邏輯不依賴框架（可以不啟動 FastAPI 就測試）
- [ ] 資料存取透過 Repository 抽象（可以換資料庫不改業務邏輯）
- [ ] 每個模組只有一個改變的理由
- [ ] 新功能可以透過擴展而非修改既有程式碼來加入
- [ ] 重要的架構決策都有 ADR 紀錄

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/clean-architecture.md | Clean Architecture 詳細分層說明與完整 Python 範例 | 需要深入理解分層時 |
| references/design-patterns.md | 常用設計模式詳解：Strategy、Observer、Factory、Repository | 需要選擇設計模式時 |
