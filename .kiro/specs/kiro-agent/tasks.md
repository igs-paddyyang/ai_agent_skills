# Implementation Plan: kiro-agent

## Overview

以核心功能優先的順序實作 kiro-agent 多 Agent 艦隊管理系統。先建立專案骨架與資料模型，再依序實作 Telegram Bot 整合、Kiro CLI 後端適配器、訊息路由、艦隊管理與 CLI 介面。進階自主運維功能（Cost Guard、Hang Detector、Context Guardian、Scheduler、MCP Bridge、Dashboard 等）標記為可選，可於後續階段實作。

## Tasks

- [ ] 1. 專案骨架與資料模型
  - [x] 1.1 建立專案目錄結構與套件配置
    - 建立 `kiro-agent/` 套件目錄與 `__init__.py`
    - 建立 `pyproject.toml`（或 `setup.py`），定義 `kiro-agent` CLI entry point
    - 建立 `requirements.txt`，包含 python-telegram-bot、PyYAML、FastAPI、uvicorn、httpx、croniter、mcp、google-genai、hypothesis、pytest、pytest-asyncio
    - 建立 `~/.kiro-agent/` 執行時資料目錄結構說明（README 或 init script）
    - _Requirements: 1.1, 18.1_

  - [x] 1.2 實作資料模型 (`models.py`)
    - 定義 `InstanceStatus` enum（STOPPED, STARTING, RUNNING, HUNG, PAUSED_COST, PAUSED_FAILOVER）
    - 定義 `InstanceState`, `RotationSnapshot`, `CostAlert`, `HangAlert`, `ScheduleEntry` dataclass
    - 定義自訂例外類別：`KiroAgentError`, `ConfigError`, `BackendError`, `InstanceError`, `DispatchError`
    - _Requirements: 2.5, 11.4_

  - [x] 1.3 實作配置載入與驗證 (`config.py`)
    - 定義 `FleetConfig`, `InstanceConfig`, `TeamConfig`, `CostGuardConfig`, `HangDetectorConfig`, `AccessConfig` dataclass
    - 實作 `load_config(path)` — 從 YAML 載入並驗證，缺少必要欄位或無效值 raise `ConfigError`
    - 實作 `dump_config(config)` — 序列化為 YAML 字串
    - 實作 defaults 合併邏輯：Instance 未指定 backend/model 時使用 defaults 區段的值
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 1.4 Property tests for config (Properties 1-3)
    - **Property 1: Fleet_Config round-trip** — 任意有效 FleetConfig 經 dump_config → load_config 後等價
    - **Validates: Requirements 1.5**
    - **Property 2: Config default merging** — 未指定 backend/model 的 Instance 載入後等於 defaults 值
    - **Validates: Requirements 1.4**
    - **Property 3: Invalid config error descriptiveness** — 缺少必要欄位或無效值 raise ConfigError 包含欄位名稱
    - **Validates: Requirements 1.2**

  - [x] 1.5 實作 SQLite 工具函式與事件日誌 (`db.py`, `event_logger.py`)
    - 實作 `init_db(path)` — 建立 events.db schema（events 表 + cost_records 表 + indexes）
    - 實作 `EventLogger` 類別 — log(), query(), cleanup(days=30)
    - 使用參數化查詢，遵循安全規範
    - _Requirements: 12.1, 12.2, 12.3_

  - [ ]* 1.6 Property test for event cleanup (Property 9)
    - **Property 9: Event cleanup by age** — cleanup(days=30) 精確移除超過 30 天的事件
    - **Validates: Requirements 12.3**

- [x] 2. Checkpoint — 確認基礎模組可用
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Telegram Bot 整合
  - [x] 3.1 實作 Channel_Router 核心 (`channel_router.py`)
    - 建立 `ChannelRouter` 類別，初始化 python-telegram-bot Application
    - 實作 `start()` — 啟動 Telegram Bot polling
    - 實作 `on_message()` — 訊息處理主流程：驗證 user_id → 判斷 topic → 路由到 Instance
    - 實作存取控制：檢查 `access.allowed_users`，未授權訊息記錄 `access_denied` 事件
    - _Requirements: 3.1, 3.4, 3.5, 17.2, 17.3_

  - [ ]* 3.2 Property test for access control (Property 4)
    - **Property 4: Access control enforcement** — locked 模式下僅 allowed_users 中的 User ID 可通過
    - **Validates: Requirements 3.4, 3.5, 17.2, 17.3**

  - [x] 3.3 實作訊息分割與發送
    - 實作 `send_to_topic(topic_id, text)` — 超過 4096 字元自動分割為多則訊息
    - 實作 `create_topic(instance_name)` — 在 Telegram Group 建立 Forum Topic
    - _Requirements: 3.3, 3.6_

  - [ ]* 3.4 Property test for message splitting (Property 5)
    - **Property 5: Message splitting preserves content** — 分割後每段 ≤ 4096 且串接還原原始字串
    - **Validates: Requirements 3.6**

  - [x] 3.5 實作 inline button 回調處理
    - 實作 `on_callback_query()` — 處理 Allow/Deny（工具使用權限）與重啟/繼續等待/強制停止按鈕
    - _Requirements: 3.7, 8.2_

- [ ] 4. Kiro CLI 後端適配器
  - [x] 4.1 實作 Backend_Adapter 抽象層 (`backend_adapter.py`)
    - 定義 `BackendAdapter` ABC — start_session, send_message, stop_session, get_status
    - 實作 `BACKEND_REGISTRY` dict 與 `get_adapter(backend_name)` 工廠函式
    - 不存在的 backend 名稱 raise `BackendError`，包含可用 backend 清單
    - _Requirements: 2.1, 2.2, 2.5_

  - [ ]* 4.2 Property test for backend error (Property 19)
    - **Property 19: Backend error structure** — 不存在的 backend 名稱 raise BackendError 包含名稱與可用清單
    - **Validates: Requirements 2.5, 5.5**

  - [x] 4.3 實作 KiroCliAdapter
    - 實作 `start_session()` — 檢查 `.kiro/steering/` 存在 → 寫入 fleet-context.md → tmux new-session → send-keys 啟動 kiro-cli
    - 實作 `send_message()` — tmux send-keys 傳送訊息
    - 實作 `stop_session()` — 優雅終止 tmux session
    - 實作 `get_status()` — 檢查 tmux session 存活狀態
    - 支援 auto, claude-sonnet-4.5, claude-sonnet-4, claude-haiku-4.5 模型
    - _Requirements: 2.3, 2.4, 2.6, 6.1, 6.2_

  - [ ]* 4.4 Property test for fleet-context.md generation (Property 14)
    - **Property 14: Fleet-context.md generation** — 產生的內容包含 Instance 身份、所有 peer 名稱與描述、協作規則
    - **Validates: Requirements 6.2**

  - [x] 4.5 實作其他 Backend Adapter 骨架
    - 實作 `ClaudeCodeAdapter`, `GeminiCliAdapter`, `CodexAdapter`, `OpenCodeAdapter` 的基本 start/stop/send/status
    - 各 Adapter 的 tmux 啟動命令對應各自的 CLI 工具
    - _Requirements: 2.2_

- [x] 5. Checkpoint — 確認 Telegram + Backend Adapter 可用
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. 艦隊管理核心與 Topic 路由
  - [x] 6.1 實作 Fleet_Manager (`fleet_manager.py`)
    - 實作 `start_fleet()` — 載入配置 → 初始化 Adapters → 啟動 auto_start Instances → 啟動 Telegram Bot
    - 實作 `stop_fleet()` — 停止所有 Instance → 停止 Telegram Bot
    - 實作 `create_instance()`, `start_instance()`, `stop_instance()`, `delete_instance()`
    - 實作 Instance 名稱唯一性驗證
    - 實作 tmux crash 自動重啟（最多 3 次，間隔 5s/15s/45s）
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 18.2_

  - [ ]* 6.2 Property tests for fleet management (Properties 13, 16)
    - **Property 13: Retry interval calculation** — 第 N 次重試間隔為 5×3^N 秒，3 次後不再重試
    - **Validates: Requirements 11.4**
    - **Property 16: Instance name uniqueness validation** — 重複名稱被拒絕，唯一名稱可建立
    - **Validates: Requirements 11.1**

  - [x] 6.3 實作 Topic-Instance 路由映射
    - 在 `ChannelRouter` 中維護 `topic_instance_map: dict[int, str]`
    - 新建 Instance 時自動建立 Telegram Topic 並更新映射
    - 訊息到達時根據 topic_id 查找對應 Instance 並 send_message
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 6.4 Property test for topic routing (Property 17)
    - **Property 17: Topic routing correctness** — 已映射的 topic_id 訊息路由到正確的 Instance
    - **Validates: Requirements 3.1**

- [ ] 7. CLI 管理介面
  - [x] 7.1 實作 CLI 入口 (`__main__.py`)
    - 使用 argparse 建立子命令：fleet start, fleet stop, fleet status, instance create, instance delete, backend doctor
    - `fleet start` — 呼叫 Fleet_Manager.start_fleet()
    - `fleet stop` — 呼叫 Fleet_Manager.stop_fleet()
    - `fleet status` — 以表格格式顯示所有 Instance 狀態
    - `instance create` — 互動式建立新 Instance
    - `instance delete` — 刪除指定 Instance
    - `backend doctor` — 檢查後端安裝/認證/版本
    - _Requirements: 18.1, 18.2, 18.3, 18.4_

  - [ ]* 7.2 Property test for fleet status table (Property 11)
    - **Property 11: Fleet status table completeness** — 狀態表包含每個 Instance 的 name, status, backend, model, context_usage_pct
    - **Validates: Requirements 18.3**

- [x] 8. Checkpoint — 核心功能完成
  - Ensure all tests pass, ask the user if questions arise.
  - 此時應可透過 TG 操作 Kiro CLI 啟用 subagent 來做事情（核心目標）

- [ ] 9. （可選）General Dispatcher — 自然語言路由
  - [x] 9.1 實作 General_Dispatcher (`general_dispatcher.py`)
    - 使用 google-genai (Gemini) 分析使用者訊息意圖
    - 實作 `dispatch()` — 回傳 DispatchResult(target, target_type, confidence, explanation)
    - 實作 `_build_routing_prompt()` — 包含所有 Instance 名稱與描述
    - 無法識別時列出可用 Instance 請使用者指定
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 9.2 Property test for team broadcast (Property 15)
    - **Property 15: Team broadcast completeness** — 廣播到 Team 的 N 個成員，無遺漏無重複
    - **Validates: Requirements 4.4**

- [ ] 10. （可選）MCP Bridge — Agent 間協作
  - [x] 10.1 實作 MCP_Bridge (`mcp_bridge.py`)
    - 使用 FastMCP 建立 MCP Server
    - 實作 list_instances, send_to_instance, request_information, delegate_task, report_result, create_team, broadcast 七個 MCP Tool
    - delegate_task 自動喚醒未啟動的 Instance
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 10.2 Property test for list_instances (Property 20)
    - **Property 20: list_instances completeness** — 回傳所有 Instance 的 name, status, description, backend
    - **Validates: Requirements 5.2**

- [ ] 11. （可選）自主運維模組
  - [x] 11.1 實作 Cost_Guard (`cost_guard.py`)
    - 追蹤每個 Instance 的 API 費用，持久化於 events.db 的 cost_records 表
    - 達到 warn_at_percentage 發送 Telegram 警告
    - 達到 daily_limit_usd 自動暫停 Instance
    - 每日重置（依 timezone）
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 11.2 Property test for cost threshold (Property 6)
    - **Property 6: Cost threshold alerting** — 費用達 warn 比例產生 warning，達 limit 產生 limit_reached 並暫停
    - **Validates: Requirements 7.2, 7.3**

  - [x] 11.3 實作 Hang_Detector (`hang_detector.py`)
    - 每 60 秒檢查 running Instance 的 last_activity
    - 超過 timeout_minutes 發送 Telegram 通知（含 inline button）
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 11.4 Property test for hang timeout (Property 7)
    - **Property 7: Hang timeout detection** — 超過 M 分鐘才報告 hang
    - **Validates: Requirements 8.2**

  - [x] 11.5 實作 Context_Guardian (`context_guardian.py`)
    - 讀取 statusline.json 取得 context 使用率
    - 超過 80% 產生 RotationSnapshot → 重啟 Session → 注入快照
    - statusline.json 不存在時跳過
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 11.6 Property test for context rotation (Property 8)
    - **Property 8: Context rotation threshold** — 僅在使用率超過 80% 時觸發輪替
    - **Validates: Requirements 9.2**

  - [x] 11.7 實作 Scheduler (`scheduler.py`)
    - SQLite 持久化排程（scheduler.db）
    - 實作 create_schedule, delete_schedule, list_schedules, toggle_schedule, tick
    - 使用 croniter 解析 cron 表達式
    - Fleet_Manager 重啟時從 DB 恢復排程
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 11.8 Property test for cron trigger (Property 18)
    - **Property 18: Cron trigger correctness** — cron 表達式匹配當前時間時且僅在匹配時觸發
    - **Validates: Requirements 10.2**

- [ ] 12. （可選）模型故障轉移
  - [x] 12.1 實作 ModelFailover (`model_failover.py`)
    - 依 model_failover 陣列順序嘗試備用模型
    - 成功切換時 Telegram 通知
    - 全部失敗時暫停 Instance
    - _Requirements: 16.1, 16.2, 16.3_

  - [ ]* 12.2 Property test for failover ordering (Property 10)
    - **Property 10: Model failover ordering** — 依陣列順序嘗試，全部失敗則暫停
    - **Validates: Requirements 16.1, 16.3**

- [ ] 13. （可選）輔助功能
  - [x] 13.1 實作語音轉錄 (`voice_transcriber.py`)
    - 使用 httpx 呼叫 Groq Whisper API 轉錄語音
    - 整合到 ChannelRouter.on_message() 的語音訊息處理
    - 失敗時回覆錯誤訊息
    - _Requirements: 14.1, 14.2, 14.3_

  - [x] 13.2 實作 HTML 對話匯出 (`html_exporter.py`)
    - 將 chat_history.jsonl 匯出為自包含 HTML（內嵌 CSS + JS）
    - 保留時間戳記、發送者標識、程式碼區塊格式
    - _Requirements: 15.1, 15.2_

  - [ ]* 13.3 Property test for HTML export (Property 12)
    - **Property 12: HTML export content preservation** — 匯出 HTML 包含每則訊息的 timestamp, sender, code blocks
    - **Validates: Requirements 15.1, 15.2**

- [ ] 14. （可選）Web Dashboard
  - [x] 14.1 實作 Dashboard (`dashboard.py`)
    - FastAPI app，監聽 health_port
    - GET /api/instances — 回傳所有 Instance 即時狀態
    - GET /api/events — 回傳最近事件日誌
    - GET /sse — SSE 即時狀態推送
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 15. 最終 Checkpoint — 全部測試通過
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks 1-8 為核心功能，實作完成即可透過 TG 操作 Kiro CLI subagent
- Tasks 9-14 標記為可選，可依需求逐步實作
- 子任務標記 `*` 為可選的 property-based tests，可跳過以加速 MVP
- 每個 task 引用具體的 Requirements 編號以確保可追溯性
- Python 3.12，遵循 PEP 8，snake_case 命名
- 所有敏感資訊從 `.env` 讀取，SQL 使用參數化查詢
