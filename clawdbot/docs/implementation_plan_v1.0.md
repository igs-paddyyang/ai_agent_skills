# 🚀 ClawdBot 智庫助理：實作執行計畫 (v1.0)

# 作者: paddyyang
# 最後修改日期: 2026-03-11

本計畫旨在根據 `clawdbot/docs/clawdbot_v1.0.md` 的規劃，將其轉化為具體的開發步驟與檢核清單，確保 ClawdBot (智庫助理) 能夠穩定地完成「網頁獵取」、「智慧分類」與「持久化存儲」。

---

## 📋 1. 計畫執行目標 (Execution Objectives)
*   **環境標準化**：整合根目錄 `.env`，統一金鑰管理。
*   **引擎模組化**：實作獨立的爬蟲 (`crawler_skill.py`) 與大腦 (`intent_router.py`)。
*   **核心存儲**：鎖定 `clawdbot/data/brain.db` 以利資料持久化。

---

## 🏗️ 2. 四階段詳細執行步驟 (Implementation Steps)

### 第一階段：基礎設施與資料庫開發 (Foundation)
*   **目的**：建立數據的「根基」，確保資料能正確存儲與排重。
*   **具體任務**：
    1.  **環境初始化**：建立 `clawdbot/src/` 目錄，並在**專案根目錄**配置 `.env`。
    2.  **資料庫建模 (`init_db.py`)**：建立 `clawdbot/data/brain.db`，建立 `raw_crawls` 表 (含 URL 唯一索引 `UNIQUE`)。
    3.  **基礎測試**：撰寫 `test_db.py` 驗證 UNIQUE 約束是否生效。

### 第二階段：Clawd 獵取引擎與過濾器 (Scraping Engine)
*   **目的**：將雜亂的網頁 HTML 轉化為乾淨、可被 AI 閱讀的 Markdown。
*   **具體任務**：
    1.  **爬蟲核心實作 (`crawler_skill.py`)**：整合 `Cache First` 邏輯，優先讀取本地資料。
    2.  **安全性設計**：加入 SSL 跳過 (verify=False) 與隨機 User-Agent 輪替。

### 第三階段：智慧路由與分析大腦 (Brain & Routing)
*   **目的**：利用 Gemini API 判斷使用者意圖，並依類型分流處理。
*   **具體任務**：
    1.  **意圖分類器 (`intent_router.py`)**：串接 `google-genai` SDK，鎖定輸出為 JSON 指令。
    2.  **摘要引擎 (`summarize_content`)**：實作繁體中文摘要與資料來源腳註標註，僅用於研究型請求。
    3.  **對話引擎 (`chat`)**：實作友善對話回應，僅用於閒聊型請求，prompt 與摘要引擎嚴格分離。

### 第四階段：Telegram 互動介面與部署 (Interface & UX)
*   **目的**：將所有模組整合，提供對終端使用者友善的互動介面。
*   **具體任務**：
    1.  **機器人主程式 (`bot_main.py`)**：整合 `python-telegram-bot` 庫，研究意圖呼叫 `summarize_content()`，閒聊意圖呼叫 `chat()`。
    2.  **轉義工具 (`format_utils.py`)**：解決 Telegram MarkdownV2 動態內容的特殊字元渲染報錯。
    3.  **靜態文本審計**：全面檢查 `bot_main.py` 中的靜態字串，手動跳脫所有 MarkdownV2 保留字元。
    4.  **體驗優化**：實現「🧠 正在思考...」→「🔍 獵取中...」→「📄 摘要完成」的漸進式進度回饋。
    5.  **測試建檔**：於 `docs/` 目錄產出 `telegram_test_guide.md`，提供五個核心測試案例。

### 第五階段：Antigravity 統一標準重構 (Standardization)
*   **目標**：依據 Antigravity 統一架構規範進行物理遷移並修正交叉引用路徑與環境變數。
*   **具體任務**：
    1.  **物理遷移**：根據規範將 .py, .db, .md 移入對應子目錄 (`src/`, `data/`, `docs/`, `tests/`, `reports/`)。
    2.  **路徑修正**：更新 `.env` 中的 `DATABASE_PATH` 為 `clawdbot/data/brain.db`。
    3.  **代碼校正**：確保 `src/` 下腳本能正確讀取根目錄 `.env`。

---

## ✅ 3. 測試與驗證項 (Checklist)

### Bug 修正驗證
- [x] **BUG-02**：閒聊模式回應為友善對話，不再輸出摘要格式。

### 功能性驗證
- [x] **URL 快取測試**：輸入相同網址，第二次成功從資料庫讀取 (Cache Hit)。
- [x] **研究意圖分流**：輸入網址正確觸發爬蟲與 `summarize_content()`。
- [x] **閒聊意圖分流**：一般閒聊正確歸類為 `CASUAL`，呼叫 `chat()`，不觸發爬蟲。
- [x] **金鑰隔離**：成功從專案根目錄讀取 `.env`。
- [x] **測試文件**：已產出 `docs/telegram_test_guide.md` 供使用者參考。

### 穩定性檢核 (Robustness)
- [x] **MarkdownV2 轉義 (動態)**：摘要內容包含 `.` `_` `-` 時，透過 `escape_markdown_v2()` 正確顯示。
- [x] **MarkdownV2 轉義 (靜態)**：`/start` 等靜態文本已手動跳脫保留字元（`\(v1\.0\)`、`\!`）。
- [x] **資料庫路徑**：正確指向 `clawdbot/data/brain.db`。

---
*執行計畫產生日期：2026-03-11*
*狀態：全線開發完成，Bug 修正已驗證*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
