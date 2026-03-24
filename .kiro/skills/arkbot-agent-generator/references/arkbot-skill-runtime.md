# Skill Package 開發指南

本文件說明如何為 ArkBot 建立自訂 Skill Package，涵蓋標準格式、執行模式、註冊流程與測試方式。

---

## 1. Skill Package 結構

每個 Skill 為獨立目錄，放在 `skills/` 下：

```
skills/{skill_id}/
├── skill.json    # 中繼資料（Registry 掃描用）
└── skill.py      # 執行入口（Executor 呼叫）
```

## 2. skill.json 規格

```json
{
  "skill_id": "my-skill",
  "intent": "RESEARCH",
  "description": "技能描述，供 Skill Resolver 語意比對",
  "examples": ["觸發範例 1", "觸發範例 2"],
  "required_params": [],
  "optional_params": ["param1", "param2"],
  "tags": ["關鍵字1", "關鍵字2"],
  "priority": 10,
  "enabled": true,
  "mode": "subprocess",
  "response_type": "text"
}
```

### 欄位說明

| 欄位 | 必填 | 說明 |
|:---|:---|:---|
| `skill_id` | ✅ | 唯一識別碼，kebab-case，與目錄名一致 |
| `intent` | ✅ | 對應意圖：`DASHBOARD` / `RESEARCH` / `CASUAL` |
| `description` | ✅ | 技能描述，Skill Resolver 用於語意比對 |
| `examples` | ✅ | 觸發範例陣列，Resolver 比對用 |
| `required_params` | ⬜ | 必要參數清單（目前未強制驗證） |
| `optional_params` | ⬜ | 可選參數清單 |
| `tags` | ✅ | 關鍵字標籤，輔助 Resolver 匹配 |
| `priority` | ✅ | 優先級，數字越大越優先（同 intent 時比較），`-1` 為最低 |
| `enabled` | ✅ | `true` 啟用 / `false` 停用（Registry 跳過） |
| `mode` | ⬜ | 執行模式：`subprocess`（預設）或 `async` |
| `response_type` | ⬜ | 回應類型：`text`（預設）或 `dashboard` |

### 執行模式

- `subprocess`（預設）：Executor 以子程序執行 `py skill.py "使用者輸入"`，透過 stdout 取得結果。適合一般 Skill，天然隔離。
- `async`：Executor 以 `importlib` 動態載入 skill.py，直接呼叫 `run()` 函式（支援 async/sync）。適合需要 async I/O 的 Skill（如 Gemini API 呼叫）。

### 回應類型

- `text`（預設）：`arkbot_core.py` 將結果作為純文字 `reply` 事件回傳。
- `dashboard`：`arkbot_core.py` 解析結果中的 `html_path` 和 `summary`，以 `dashboard_reply` 事件回傳（前端顯示開啟按鈕）。

## 3. skill.py 規格

### subprocess 模式

```python
import sys
import os

# 設定路徑
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

def run(user_input: str) -> str:
    """Executor 呼叫的統一入口"""
    # 實作邏輯
    return "結果字串"

if __name__ == "__main__":
    user_input = sys.argv[1] if len(sys.argv) > 1 else ""
    print(run(user_input))
```

### async 模式

```python
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

async def run(user_input: str) -> str:
    """Executor 呼叫的統一入口（async）"""
    # 實作邏輯（可使用 await）
    return "結果字串"

if __name__ == "__main__":
    import asyncio
    user_input = sys.argv[1] if len(sys.argv) > 1 else ""
    print(asyncio.run(run(user_input)))
```

### 重點規則

- 函式名稱固定為 `run`，接受 `user_input: str`，回傳 `str`
- subprocess 模式必須有 `if __name__ == "__main__"` 區塊
- `PROJECT_ROOT` 指向專案根目錄，用於 import `src/` 下的模組
- 回傳值為純字串；dashboard 類型需回傳含 `html_path` 的 JSON 字串

## 4. 路由與觸發流程

### 對話觸發

```
使用者輸入
  → Intent Router（Gemini 分類：DASHBOARD / RESEARCH / CASUAL）
  → Hybrid Router
  → Skill Resolver（語意比對 description + examples + tags）
  → 匹配成功 → Executor 執行 skill.py
  → 匹配失敗 → Foundation fallback（CASUAL 閒聊）
```

### API 直接呼叫

```
POST /api/skill/{skill_id}
  → Executor 直接執行（不經 Intent Router）
  → 回傳 JSON {success, skill_id, result, execution_time_ms}
```

### 排程觸發

```
Scheduler cron 到期
  → Executor 直接執行（不經 Intent Router）
  → 結果寫入 data/scheduler.log
```

## 5. 內建 Skill 參考

| skill_id | intent | mode | response_type | priority | 說明 |
|:---|:---|:---|:---|:---|:---|
| `dashboard` | DASHBOARD | async | dashboard | 10 | 儀表板產生（JSON → Gemini → HTML） |
| `crawler` | RESEARCH | subprocess | text | 10 | 爬蟲研究（URL → 摘要） |
| `chat` | CASUAL | subprocess | text | -1 | 閒聊對話（最低優先，兜底） |

## 6. 新增 Skill 步驟

1. 建立 `skills/{skill_id}/` 目錄
2. 建立 `skill.json`（參考 §2 規格）
3. 建立 `skill.py`（參考 §3 規格）
4. 獨立測試：`py skills/{skill_id}/skill.py "測試輸入"`
5. 重啟服務，確認 Registry log 顯示載入新 Skill
6. 透過對話或 API 觸發驗證

無需修改任何核心程式碼 — Registry 自動掃描 `skills/` 目錄。

## 7. 排程設定

在 `data/schedules.json` 新增排程項目：

```json
{
  "id": "unique-schedule-id",
  "skill_id": "dashboard",
  "input": "要傳給 skill.py 的輸入文字",
  "cron": "0 9 * * *",
  "enabled": true,
  "description": "排程說明"
}
```

cron 格式：`分 時 日 月 星期`（標準 5 欄位）。

## 8. Skill API 使用

```bash
# 列出所有 Skill
curl http://localhost:2141/api/skills -H "X-API-Key: YOUR_KEY"

# 執行指定 Skill
curl -X POST http://localhost:2141/api/skill/chat \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "你好"}'
```

API Key 設定在 `.env` 的 `SKILL_API_KEY` 欄位。
