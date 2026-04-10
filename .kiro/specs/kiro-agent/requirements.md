# Requirements Document

## Introduction

kiro-agent 是一個以 Python 建構的多 Agent 艦隊管理系統，靈感來自 AgEnD（Agent Engineering Daemon）。系統將 Telegram 轉變為 AI 編碼 Agent 的指揮中心，以 Kiro CLI 為主要後端，支援多種 AI CLI 後端混用。每個 Telegram Forum Topic 對應一個獨立的 Agent Session，Agent 之間透過 MCP Tool 進行 P2P 協作。系統提供費用控管、掛起偵測、Context 輪替、排程任務、Web Dashboard 等自主運維能力，讓艦隊可無人值守運行。

## Glossary

- **Fleet_Manager**: 艦隊管理核心程序，負責啟動、停止、監控所有 Agent Instance，管理全域配置與生命週期
- **Instance**: 一個獨立的 Agent 工作單元，綁定特定專案目錄與 AI CLI 後端，在獨立的 tmux Session 中執行
- **Backend_Adapter**: AI CLI 後端抽象層，將不同的 CLI 工具（Kiro CLI、Claude Code、Gemini CLI 等）統一為一致的介面
- **Channel_Router**: 訊息頻道路由器，負責接收 Telegram 訊息並分派到對應的 Instance
- **General_Dispatcher**: General Topic 的特殊 Instance，使用自然語言理解將使用者訊息路由到正確的 Agent
- **MCP_Bridge**: MCP Tool 橋接層，為 Agent 之間的 P2P 協作提供 list_instances、send_to_instance、delegate_task 等工具
- **Cost_Guard**: 費用控管模組，追蹤每個 Instance 的 API 使用費用並在達到上限時自動暫停
- **Hang_Detector**: 掛起偵測模組，監控 Instance 活動狀態，在超時無回應時發出通知
- **Context_Guardian**: Context 輪替模組，監控 CLI Session 的 context 使用率，在超過閾值時自動重啟並注入快照
- **Scheduler**: 排程系統，基於 cron 表達式觸發定時任務，以 SQLite 持久化儲存
- **Dashboard_Server**: Web 儀表板伺服器，透過 SSE 提供即時艦隊狀態監控
- **Fleet_Config**: 艦隊配置檔（fleet.yaml），定義所有 Instance、Team、預設值與安全策略
- **Team**: 一組相關 Instance 的邏輯分組，支援廣播訊息與批次操作
- **Rotation_Snapshot**: Context 輪替時產生的狀態快照，包含當前工作摘要與關鍵決策，用於注入新 Session

## Requirements

### Requirement 1: 艦隊配置載入與驗證

**User Story:** As a 開發者, I want to 透過 YAML 配置檔定義艦隊的所有 Instance、Team 與預設值, so that 可以用宣告式方式管理整個 Agent 艦隊

#### Acceptance Criteria

1. WHEN Fleet_Manager 啟動時, THE Fleet_Manager SHALL 從 `~/.kiro-agent/fleet.yaml` 載入 Fleet_Config 並驗證其結構完整性
2. IF Fleet_Config 包含無效欄位或缺少必要欄位, THEN THE Fleet_Manager SHALL 回傳描述性錯誤訊息，指出具體的欄位名稱與問題
3. THE Fleet_Config SHALL 支援定義 project_roots、channel、defaults、instances、teams 五個頂層區段
4. WHEN Fleet_Config 中的 Instance 未指定 backend 或 model, THE Fleet_Manager SHALL 使用 defaults 區段的值作為該 Instance 的預設值
5. THE Fleet_Config_Parser SHALL 將 fleet.yaml 解析為 Python 資料結構，THE Fleet_Config_Printer SHALL 將 Python 資料結構格式化回有效的 fleet.yaml，FOR ALL 有效的 Fleet_Config 物件，解析後列印再解析 SHALL 產生等價的物件（round-trip property）

### Requirement 2: 多後端 AI CLI 抽象層

**User Story:** As a 開發者, I want to 在不同 Instance 上使用不同的 AI CLI 後端, so that 可以根據任務特性選擇最適合的 AI 模型

#### Acceptance Criteria

1. THE Backend_Adapter SHALL 為所有支援的 AI CLI 後端提供統一的介面，包含 start_session、send_message、stop_session、get_status 四個操作
2. THE Backend_Adapter SHALL 支援以下後端：kiro-cli（主要）、claude-code、gemini-cli、codex、opencode
3. WHEN 啟動一個 Instance, THE Backend_Adapter SHALL 在獨立的 tmux Session 中執行對應的 CLI 工具
4. WHEN Backend_Adapter 啟動 kiro-cli 後端, THE Backend_Adapter SHALL 確認 `.kiro/steering/` 目錄存在於該 Instance 的工作目錄中
5. IF 指定的後端 CLI 工具未安裝或認證失敗, THEN THE Backend_Adapter SHALL 回傳結構化錯誤，包含後端名稱、錯誤類型與建議的修復步驟
6. WHEN 使用 kiro-cli 後端, THE Backend_Adapter SHALL 支援 auto、claude-sonnet-4.5、claude-sonnet-4、claude-haiku-4.5 四種模型選項

### Requirement 3: Telegram 訊息頻道整合

**User Story:** As a 開發者, I want to 透過 Telegram Forum Topic 與各個 Agent 互動, so that 可以從手機隨時管理和指揮 Agent 艦隊

#### Acceptance Criteria

1. WHEN Telegram Bot 收到 Forum Topic 中的訊息, THE Channel_Router SHALL 根據 Topic ID 將訊息路由到對應的 Instance
2. WHEN 訊息來自 General Topic, THE Channel_Router SHALL 將訊息轉交給 General_Dispatcher 進行自然語言路由
3. WHEN 建立新的 Instance, THE Channel_Router SHALL 在 Telegram Group 中自動建立對應的 Forum Topic
4. THE Channel_Router SHALL 僅接受 Fleet_Config 中 access.allowed_users 清單內的使用者訊息
5. IF 訊息來自未授權的使用者, THEN THE Channel_Router SHALL 忽略該訊息並記錄一筆存取拒絕事件到 events.db
6. WHEN Agent 產生回應, THE Channel_Router SHALL 將回應發送到對應的 Telegram Forum Topic，長度超過 4096 字元的回應 SHALL 自動分割為多則訊息
7. WHEN Agent 請求工具使用權限, THE Channel_Router SHALL 在 Telegram 中顯示 inline button（Allow / Deny），等待使用者回應

### Requirement 4: General Topic 自然語言路由

**User Story:** As a 開發者, I want to 在 General Topic 用自然語言描述任務, so that 系統自動將任務分派到最適合的 Agent

#### Acceptance Criteria

1. WHEN General_Dispatcher 收到使用者訊息, THE General_Dispatcher SHALL 分析訊息內容並識別目標 Instance 或 Team
2. WHEN General_Dispatcher 識別出目標 Instance, THE General_Dispatcher SHALL 將訊息轉發到該 Instance 並在 General Topic 回覆路由結果
3. IF General_Dispatcher 無法識別目標 Instance, THEN THE General_Dispatcher SHALL 列出所有可用的 Instance 及其描述，請使用者明確指定
4. WHEN 使用者訊息包含 Team 名稱, THE General_Dispatcher SHALL 將訊息廣播到該 Team 的所有成員 Instance

### Requirement 5: Agent 間 MCP 協作

**User Story:** As a 開發者, I want to Agent 之間可以互相發現、傳訊和委派任務, so that 多個 Agent 可以協同完成複雜的跨專案工作

#### Acceptance Criteria

1. THE MCP_Bridge SHALL 提供以下 MCP Tool：list_instances、send_to_instance、request_information、delegate_task、report_result、create_team、broadcast
2. WHEN Agent 呼叫 list_instances, THE MCP_Bridge SHALL 回傳所有 Instance 的名稱、狀態、描述與後端類型
3. WHEN Agent 呼叫 delegate_task 指定目標 Instance 與任務描述, THE MCP_Bridge SHALL 喚醒目標 Instance（若未啟動）並傳送任務訊息
4. WHEN 目標 Instance 完成委派任務, THE MCP_Bridge SHALL 透過 report_result 將結果回傳給委派者
5. IF delegate_task 的目標 Instance 不存在, THEN THE MCP_Bridge SHALL 回傳錯誤訊息，包含可用的 Instance 清單
6. WHEN Agent 呼叫 send_to_instance, THE MCP_Bridge SHALL 透過 IPC（Unix socket）將訊息傳送到目標 Instance 的 tmux Session

### Requirement 6: Kiro CLI 特化整合

**User Story:** As a 開發者, I want to Kiro CLI 後端能正確載入 Steering 檔案和 Skills, so that Agent 擁有專案上下文和擴展能力

#### Acceptance Criteria

1. WHEN 啟動 kiro-cli 後端的 Instance, THE Backend_Adapter SHALL 檢查工作目錄中是否存在 `.kiro/steering/` 目錄
2. THE Fleet_Manager SHALL 將 fleet context（Instance 身份、協作規則、可用 Instance 清單）寫入 `.kiro/steering/fleet-context.md` 作為 Kiro CLI 的上下文注入方式
3. WHEN Fleet_Config 中的 Instance 清單變更, THE Fleet_Manager SHALL 自動更新所有 kiro-cli Instance 的 `fleet-context.md` 檔案
4. WHEN kiro-cli Instance 啟動, THE Backend_Adapter SHALL 確認 `.kiro/skills/` 目錄中的技能可被 Kiro CLI 載入

### Requirement 7: 費用控管

**User Story:** As a 開發者, I want to 設定每日費用上限, so that 多 Agent 並行時不會產生超出預期的 API 費用

#### Acceptance Criteria

1. THE Cost_Guard SHALL 追蹤每個 Instance 的累計 API 使用費用（以 USD 計算），資料持久化於 events.db
2. WHEN Instance 的當日累計費用達到 Fleet_Config 中 cost_guard.warn_at_percentage 的比例, THE Cost_Guard SHALL 透過 Telegram 發送費用警告通知
3. WHEN Instance 的當日累計費用達到 cost_guard.daily_limit_usd, THE Cost_Guard SHALL 自動暫停該 Instance 並透過 Telegram 發送暫停通知
4. WHEN 新的一天開始（依 cost_guard.timezone 判定）, THE Cost_Guard SHALL 重置所有 Instance 的當日累計費用

### Requirement 8: 掛起偵測

**User Story:** As a 開發者, I want to 自動偵測 Agent 是否掛起無回應, so that 可以及時處理異常狀態

#### Acceptance Criteria

1. WHILE hang_detector.enabled 為 true, THE Hang_Detector SHALL 每 60 秒檢查一次每個 running 狀態 Instance 的最後活動時間
2. WHEN Instance 的最後活動時間超過 hang_detector.timeout_minutes, THE Hang_Detector SHALL 透過 Telegram 發送掛起通知，包含 inline button（重啟 / 繼續等待 / 強制停止）
3. WHEN 使用者點擊「重啟」按鈕, THE Hang_Detector SHALL 停止該 Instance 的 tmux Session 並重新啟動

### Requirement 9: Context 輪替

**User Story:** As a 開發者, I want to 在 Agent 的 context 使用率過高時自動輪替, so that Agent 不會因 context 耗盡而停止工作

#### Acceptance Criteria

1. THE Context_Guardian SHALL 定期讀取每個 Instance 的 statusline.json 以取得 context 使用率百分比
2. WHEN Instance 的 context 使用率超過 80%, THE Context_Guardian SHALL 產生 Rotation_Snapshot（包含當前工作摘要與關鍵決策）
3. WHEN Rotation_Snapshot 產生完成, THE Context_Guardian SHALL 停止當前 tmux Session 並啟動新 Session，將 Rotation_Snapshot 作為初始訊息注入
4. IF statusline.json 不存在或無法解析, THEN THE Context_Guardian SHALL 記錄警告事件並跳過該 Instance 的本次檢查

### Requirement 10: 持久化排程系統

**User Story:** As a 開發者, I want to 建立 cron 排程讓 Agent 定時執行任務, so that 例行工作可以自動化

#### Acceptance Criteria

1. THE Scheduler SHALL 將排程資料持久化於 `~/.kiro-agent/scheduler.db`（SQLite），包含 id、cron 表達式、訊息內容、目標 Instance、啟用狀態、上次執行時間
2. WHEN cron 表達式匹配當前時間, THE Scheduler SHALL 將排程訊息發送到目標 Instance
3. WHEN Fleet_Manager 重啟, THE Scheduler SHALL 從 scheduler.db 載入所有啟用的排程並恢復計時
4. THE Scheduler SHALL 提供 create_schedule、delete_schedule、list_schedules、toggle_schedule 四個操作介面

### Requirement 11: Instance 生命週期管理

**User Story:** As a 開發者, I want to 動態建立、啟動、停止和刪除 Instance, so that 可以靈活調整艦隊規模

#### Acceptance Criteria

1. WHEN 收到 create_instance 請求, THE Fleet_Manager SHALL 驗證工作目錄存在、Instance 名稱唯一，然後建立新的 Instance 配置並寫入 fleet.yaml
2. WHEN 收到 start_instance 請求, THE Fleet_Manager SHALL 啟動對應的 tmux Session 並將 Instance 狀態設為 running
3. WHEN 收到 stop_instance 請求, THE Fleet_Manager SHALL 優雅地終止 tmux Session 並將 Instance 狀態設為 stopped
4. IF Instance 的 tmux Session 意外終止, THEN THE Fleet_Manager SHALL 自動重啟該 Instance，重試次數上限為 3 次，每次間隔遞增（5 秒、15 秒、45 秒）
5. WHEN 收到 delete_instance 請求, THE Fleet_Manager SHALL 停止 Instance、移除 runtime 資料（`~/.kiro-agent/instances/<name>/`）並從 fleet.yaml 中刪除該 Instance 配置

### Requirement 12: 事件日誌系統

**User Story:** As a 開發者, I want to 記錄艦隊中所有重要事件, so that 可以追蹤問題和分析 Agent 行為

#### Acceptance Criteria

1. THE Fleet_Manager SHALL 將所有事件記錄到 `~/.kiro-agent/events.db`（SQLite），每筆事件包含 timestamp、event_type、instance_name、data（JSON）
2. THE Fleet_Manager SHALL 記錄以下事件類型：instance_started、instance_stopped、instance_crashed、message_sent、message_received、cost_warning、cost_limit_reached、hang_detected、context_rotated、schedule_triggered
3. WHEN events.db 中的記錄超過 30 天, THE Fleet_Manager SHALL 自動清理過期記錄

### Requirement 13: Web Dashboard 即時監控

**User Story:** As a 開發者, I want to 透過 Web 介面即時監控艦隊狀態, so that 可以在瀏覽器中一覽所有 Agent 的運行狀況

#### Acceptance Criteria

1. THE Dashboard_Server SHALL 提供 HTTP API 端點，回傳所有 Instance 的即時狀態（名稱、狀態、後端、模型、context 使用率、當日費用）
2. THE Dashboard_Server SHALL 透過 Server-Sent Events（SSE）推送即時狀態更新到前端
3. WHEN Instance 狀態變更（啟動、停止、掛起、費用警告）, THE Dashboard_Server SHALL 在 3 秒內透過 SSE 推送更新事件
4. THE Dashboard_Server SHALL 使用 FastAPI 框架，監聽 Fleet_Config 中 health_port 指定的埠號

### Requirement 14: 語音訊息轉錄

**User Story:** As a 開發者, I want to 透過 Telegram 語音訊息指揮 Agent, so that 在不方便打字時也能操作艦隊

#### Acceptance Criteria

1. WHEN Channel_Router 收到 Telegram 語音訊息, THE Channel_Router SHALL 下載音訊檔案並傳送到 Groq Whisper API 進行轉錄
2. WHEN 轉錄完成, THE Channel_Router SHALL 將轉錄文字作為一般文字訊息處理，並在 Telegram 回覆中附上轉錄結果
3. IF Groq Whisper API 呼叫失敗, THEN THE Channel_Router SHALL 回覆錯誤訊息並建議使用者改用文字輸入

### Requirement 15: HTML 對話匯出

**User Story:** As a 開發者, I want to 將 Agent 的對話記錄匯出為自包含的 HTML 檔案, so that 可以離線檢視和分享工作成果

#### Acceptance Criteria

1. WHEN 使用者發送匯出指令, THE Fleet_Manager SHALL 將指定 Instance 的對話記錄匯出為單一自包含 HTML 檔案（內嵌 CSS 和 JavaScript）
2. THE Fleet_Manager SHALL 在匯出的 HTML 中保留訊息的時間戳記、發送者標識與程式碼區塊格式

### Requirement 16: 模型故障轉移

**User Story:** As a 開發者, I want to 在主要模型不可用時自動切換到備用模型, so that Agent 不會因單一模型故障而停止工作

#### Acceptance Criteria

1. WHEN Backend_Adapter 偵測到 API rate limit 或模型不可用錯誤, THE Backend_Adapter SHALL 依照 Fleet_Config 中 model_failover 陣列的順序嘗試下一個模型
2. WHEN 成功切換到備用模型, THE Backend_Adapter SHALL 透過 Telegram 通知使用者目前使用的模型已變更
3. IF model_failover 陣列中所有模型都不可用, THEN THE Backend_Adapter SHALL 暫停該 Instance 並透過 Telegram 通知使用者

### Requirement 17: 安全與存取控制

**User Story:** As a 開發者, I want to 確保只有授權使用者可以操作艦隊, so that Agent 不會被未授權的人濫用

#### Acceptance Criteria

1. THE Fleet_Manager SHALL 從 `~/.kiro-agent/.env` 讀取所有敏感資訊（Bot Token、API Key），禁止在 fleet.yaml 或程式碼中硬編碼
2. THE Channel_Router SHALL 在處理每則訊息前驗證發送者的 Telegram User ID 是否在 access.allowed_users 清單中
3. WHILE access.mode 為 locked, THE Channel_Router SHALL 拒絕所有不在 allowed_users 清單中的使用者訊息

### Requirement 18: CLI 管理介面

**User Story:** As a 開發者, I want to 透過命令列管理艦隊, so that 可以在終端機中快速操作而不需開啟 Telegram

#### Acceptance Criteria

1. THE Fleet_Manager SHALL 提供 `kiro-agent` CLI 工具，支援以下子命令：fleet start、fleet stop、fleet status、instance create、instance delete、backend doctor
2. WHEN 執行 `kiro-agent fleet start`, THE Fleet_Manager SHALL 啟動所有已配置的 Instance 並開始監聽 Telegram 訊息
3. WHEN 執行 `kiro-agent fleet status`, THE Fleet_Manager SHALL 以表格格式顯示所有 Instance 的名稱、狀態、後端、模型與 context 使用率
4. WHEN 執行 `kiro-agent backend doctor <backend-name>`, THE Fleet_Manager SHALL 檢查該後端的安裝狀態、認證狀態與版本資訊，並以結構化格式回報結果
