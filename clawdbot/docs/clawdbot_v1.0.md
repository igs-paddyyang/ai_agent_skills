# 🚀 AI Agent 實作指南：ClawdBot 智庫助理 (v1.0)

**目標：** 透過 Google Antigravity 框架整合 Gemini API 與 SQLite，打造具備「主動獵取」與「結構化存儲」能力的個人智庫助理，解決資訊碎片化與 AI 幻覺問題。

---

## 📋 1. 需求分析 (Requirement Analysis)

### 1.1 核心功能需求
*   **主動網頁獵取 (Active Clawing)**：輸入 URL 後自動抓取 HTML 並轉化為結構化的 Markdown。
*   **智慧意圖分類 (Intent Routing)**：精準區分「研究型 (Research)」與「閒聊型 (Casual)」請求。
*   **長效本地記憶 (Long-term Memory)**：將獵取內容與對話精華持久化存儲於 SQLite。
*   **漸進式體驗 (Proactive UI)**：在 Telegram 提供即時狀態回饋與標註來源的專業摘要。

### 1.2 技術約束與驗證指標
| **模組** | **前置需求** | **獨立性** | **驗證指標** |
| :--- | :--- | :--- | :--- |
| **Clawd Engine** | 具備連網權限 | 高度獨立 | 給予網址，檢查資料庫 `brain.db` 是否產出 MD。 |
| **Intent Router** | Gemini API (google-genai) | 中度獨立 | 測試混合問題，檢查 JSON 分類標籤正確率。 |
| **SQLite Sink** | 本地寫入權限 | 高度獨立 | 確認 `UNIQUE` 約束是否能防止重複抓取。 |
| **UX Interface** | Telegram Token | 整合層 | 檢查 `escape_md` 是否能防止動態內容出錯；靜態字串必須手動跳脫 MarkdownV2 保留字元。 |

### 1.3 測試支援要求
*   **對話測試指南**：產出 `docs/telegram_test_guide.md`，指導使用者進行意圖觸發、獵取驗證與邊界測試。

---

## 🏗️ 2. 系統設計 (System Design)

### 2.1 數據結構設計 (Data Architecture)
*   **`raw_crawls` 表**：存儲原文。包含 `url` (Unique), `content_md`, `created_at`。
*   **`memories` 表**：存儲大腦產出。包含 `content`, `is_star` (一鍵存入智庫標籤)。

### 2.2 提詞策略與工作流 (Prompt Strategy)
*   **Router 提詞**：設定 Agent 為「數據分流器」，輸出格式鎖定為 `{"intent": "RESEARCH", "url": "..."}`。
*   **摘要提詞 (`summarize_content`)**：指示 AI 引用 `raw_crawls` 數據，使用腳註標註資訊來源，輸出繁體中文結構化摘要。
*   **對話提詞 (`chat`)**：設定 Agent 為友善助理，直接回應閒聊，不使用摘要格式。兩種提詞必須嚴格分離，避免格式污染。

### 2.3 目錄結構與管理 (Project Folder Structure)
依據 Antigravity 統一架構規範，確保數據、代碼與運維職責分離：
*   **`docs/`**：存放系統設計文件 (如 `clawdbot_v1.0.md`)、執行計畫與測試手冊。
*   **`src/`**：存放核心代碼 (`bot_main.py`, `crawler_skill.py`, `intent_router.py`)。
*   **`data/`**：存放持久化資料庫 (`brain.db`)。
*   **`reports/`**：存放智庫分析快照與維運報告。
*   **`scripts/`**：存放資料庫初始化等維運腳本。
*   **`tests/`**：存放功能驗證腳本。

---

## 🛠️ 3. 實作路徑 (Implementation Workflow)

### Phase 1: 環境配置與資料庫初始化
1. 配置專案根目錄下的 `.env` 金鑰 (包含 `GOOGLE_API_KEY`, `TELEGRAM_TOKEN`, `DATABASE_PATH`)。
2. 執行初始化腳本生成 `clawdbot/data/brain.db`，確保 `UNIQUE(url)` 約束生效。

### Phase 2: 開發 Clawd 爬蟲引擎
1. 實作 `crawler_skill.py`：`requests` + `BeautifulSoup` + `markdownify` 轉化主題內容。
2. **優化重點**：偽裝 User-Agent 並處理 403 / 超時情況，加入快取優先 (Cache First) 邏輯。

### Phase 3: 大腦路由與意圖分流
1. 建立 `intent_router.py`：利用 `google-genai` 將輸入轉為結構化 JSON 意圖。
2. 配置 `ClawdBrain` 類別，包含三個獨立方法：
   - `classify_intent()`：意圖分類，輸出 JSON。
   - `summarize_content()`：研究型摘要，含腳註。
   - `chat()`：閒聊型對話，直接友善回應。

### Phase 4: Telegram UX 介面強化
1. 實作 `bot_main.py` 與 `format_utils.py` (轉義處理)。
2. 加入漸進式狀態回饋（「🧠 正在思考...」→「🔍 獵取中...」→「📄 摘要完成」）。
3. **靜態文本規範**：所有 MarkdownV2 靜態字串必須手動跳脫保留字元 `_ * [ ] ( ) ~ \` > # + - = | { } . !`。

---

## ✅ 4. 驗證與測試指南 (Testing Guide)

### 4.1 功能性測試
*   **資料庫寫入**：確認重複抓取同一 URL 時，系統從快取讀取而非重複執行。
*   **意圖分流**：輸入閒聊 → 呼叫 `chat()`；輸入網址 → 呼叫 `summarize_content()`，兩者不可混用。

### 4.2 MarkdownV2 格式測試
*   **動態內容**：發送含 `.` `_` `*` 的網頁內容，驗證 `escape_markdown_v2()` 是否生效。
*   **靜態字串**：驗證 `/start` 等固定文本已手動跳脫保留字元（如 `\(v1\.0\)`、`\!`）。

### 4.3 對話測試
*   詳見 `docs/telegram_test_guide.md`，涵蓋初始化、研究意圖、快取驗證、閒聊模式、邊界測試共五個案例。

---

## 🐛 5. 已知問題與修正紀錄 (Bug Log)

### BUG-01：`/start` 指令觸發 `BadRequest: Can't parse entities`
*   **發現日期**：2026-03-11
*   **錯誤訊息**：`telegram.error.BadRequest: Can't parse entities: character '(' is reserved and must be escaped with the preceding '\'`
*   **根本原因**：`start()` handler 的 `welcome_text` 使用 `MARKDOWN_V2` 模式，但 `(v1.0)` 的括號與結尾 `！` 屬於保留字元，未跳脫直接發送導致 Telegram API 解析失敗。
*   **MarkdownV2 保留字元完整清單**：`_ * [ ] ( ) ~ \` > # + - = | { } . !`，出現在純文字區域時全部需要加 `\` 前綴。
*   **修正方式**：`(v1.0)` 改為 `\(v1\.0\)`，`！` 改為 `\!`。
*   **影響範圍**：`clawdbot/src/bot_main.py` → `start()` 的 `welcome_text`。
*   **預防準則**：手寫的 MarkdownV2 靜態字串發送前必須確認保留字元已跳脫；動態內容一律透過 `escape_markdown_v2()` 處理。

---

### BUG-02：閒聊模式回應格式錯誤（摘要格式污染）
*   **發現日期**：2026-03-11
*   **測試案例**：`telegram_test_guide.md` 案例 2.4 — 輸入「你好，你覺得今天台北天氣如何？」
*   **錯誤現象**：Bot 回應條列式摘要格式（「使用者訊息摘要：...」），而非簡潔友善的對話回覆。
*   **根本原因**：casual 分支錯誤呼叫 `summarize_content()`，該方法 prompt 設計為「針對 Markdown 內容進行專業摘要」，AI 不管輸入是什麼都會用摘要格式回應。
*   **修正方式**：`ClawdBrain` 新增專屬 `chat()` 方法，使用對話型 prompt；casual 分支改呼叫 `self.brain.chat(user_input)`。
*   **影響範圍**：`clawdbot/src/intent_router.py` 新增 `chat()` 方法；`clawdbot/src/bot_main.py` → `handle_message()` 的 `else` 分支。
*   **預防準則**：`summarize_content()` 僅用於研究型內容摘要；閒聊回應必須使用獨立的 `chat()` 方法，兩者 prompt 不可混用。

---
*最後更新日期: 2026-03-11*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
