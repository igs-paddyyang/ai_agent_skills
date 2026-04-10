# kiro-agent

多 Agent 艦隊管理系統 — 將 Telegram 轉變為 AI 編碼 Agent 的指揮中心。

## 專案結構

```
kiro_agent/
├── __init__.py             # 套件入口、版本、RUNTIME_DIR
├── __main__.py             # CLI 入口（kiro-agent 命令）
├── models.py               # 資料模型（dataclass）與自訂例外
├── config.py               # fleet.yaml 載入、驗證、序列化
├── db.py                   # SQLite schema 初始化
├── event_logger.py         # 事件日誌 CRUD
├── fleet_manager.py        # 艦隊生命週期管理核心
├── channel_router.py       # Telegram 訊息路由 + 存取控制
├── backend_adapter.py      # AI CLI 後端抽象層（5 個 Adapter）
├── general_dispatcher.py   # General Topic 自然語言路由（Gemini）
├── mcp_bridge.py           # Agent 間 MCP 協作（7 個 Tool）
├── cost_guard.py           # 費用控管
├── hang_detector.py        # 掛起偵測
├── context_guardian.py     # Context 輪替
├── scheduler.py            # cron 排程系統
├── model_failover.py       # 模型故障轉移
├── voice_transcriber.py    # 語音轉錄（Groq Whisper）
├── html_exporter.py        # HTML 對話匯出
├── dashboard.py            # Web Dashboard（FastAPI + SSE）
│
├── tests/                  # 測試
│   └── unit/               # 單元測試（330 tests）
│       ├── test_models.py
│       ├── test_config.py
│       ├── test_event_logger.py
│       ├── test_backend_adapter.py
│       ├── test_kiro_cli_adapter.py
│       ├── test_channel_router.py
│       ├── test_message_split.py
│       ├── test_fleet_manager.py
│       ├── test_cli.py
│       ├── test_general_dispatcher.py
│       ├── test_mcp_bridge.py
│       ├── test_cost_guard.py
│       ├── test_hang_detector.py
│       ├── test_context_guardian.py
│       ├── test_scheduler.py
│       ├── test_model_failover.py
│       ├── test_voice_transcriber.py
│       ├── test_html_exporter.py
│       └── test_dashboard.py
│
├── docs/                   # 文件
│   └── tutorial.md         # 教學使用手冊
│
├── pyproject.toml          # 套件配置（獨立安裝用）
└── requirements.txt        # 依賴清單
```

## 快速開始

```bash
# 安裝依賴
pip install -r kiro_agent/requirements.txt

# 以開發模式安裝
pip install -e .

# 執行測試
py -m pytest kiro_agent/tests/unit/ -q

# 檢查後端
kiro-agent backend doctor kiro-cli

# 啟動艦隊
kiro-agent fleet start
```

## 支援的後端

| 後端 | CLI 命令 |
|------|---------|
| kiro-cli | `kiro-cli` |
| claude-code | `claude` |
| gemini-cli | `gemini` |
| codex | `codex` |
| opencode | `opencode` |

## 模組分層

```
外部介面層    __main__.py / channel_router.py / dashboard.py
核心引擎層    fleet_manager.py / general_dispatcher.py / backend_adapter.py
協作層        mcp_bridge.py
自主運維層    cost_guard.py / hang_detector.py / context_guardian.py / scheduler.py / model_failover.py
輔助功能層    voice_transcriber.py / html_exporter.py
基礎設施層    models.py / config.py / db.py / event_logger.py
```

詳細使用說明請參考 [docs/tutorial.md](docs/tutorial.md)。
