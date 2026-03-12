# 🚀 Gemini Canvas 自動化數據儀表板：實作執行計畫 (v1.1)

# 作者: paddyyang
# 最後修改日期: 2026-03-11

本計畫旨在根據 `gemini_canvas/docs/gemini_canvas_v1.0.md` 的規劃，建立一個具備「自動生成、偵測與測試」能力的數據儀表板。透過 FastAPI 提供後端數據（支援靜態檔案與隨機模式），Gemini API 負責 UI 生成，並利用 Playwright 進行自動化驗證。

---

## 📋 1. 計畫執行目標 (Execution Objectives)
*   **數據導向 (Data-Driven)**：建立嚴格的數據契約，預設從 `data/data.json` 讀取，確保可控與可重現。
*   **雙模式支援**：靜態檔案模式（預設）與隨機模擬模式（`?mock=true`）並存。
*   **Gen-UI 自動化**：利用大模型減少手動撰寫 HTML/CSS 的時間。
*   **全自動驗證**：實現無人值守的 E2E 渲染與邏輯測試。

---

## 🏗️ 2. 五階段詳細執行步驟 (Implementation Steps)

### 第一階段：數據層建設與 API 開發 (Data Infrastructure)
*   **目的**：建立穩定、可編輯的數據源，取代純隨機生成。
*   **具體任務**：
    1.  **環境初始化**：確保根目錄 `.env` 已就緒。
    2.  **靜態數據建立 (`data/data.json`)**：
        *   建立符合 `DashboardData` schema 的固定業務數據。
        *   包含 `kpi_cards`（4 張）、`trend_data`（10 天）、`category_ratio`（4 類）、`recent_transactions`（5 筆）。
    3.  **FastAPI 伺服器建置 (`server.py`)**：
        *   `/api/data`：預設從 `data/data.json` 讀取，支援 `?mock=true` 啟用隨機模式。
        *   `/dashboard`：回傳 `web/index.html` 靜態頁面。
    4.  **基礎連通測試**：驗證兩種模式的 JSON 結構是否符合預期。

### 第二階段：視覺規範與 Gen-UI 提詞策略 (Design & Prompting)
*   **目的**：定義視覺標準，產出具備專業圖表的單一 HTML。
*   **具體任務**：
    1.  **設計系統規範**：鎖定科技感配色 (#2563eb, #10b981) 與 Tailwind CSS 佈局。
    2.  **核心提詞開發 (`prompts/visual_design.txt`)**：撰寫專業提詞，指示 AI 產出包含 Chart.js 邏輯的前端代碼。
    3.  **初版 Canvas 生成**：執行生成任務，產出初版 `web/index.html`。

### 第三階段：Canvas 持久化與增量優化 (UI Refinement)
*   **目的**：利用 Antigravity Canvas 進行細節微調與功能增強。
*   **具體任務**：
    1.  **視覺增輝**：加入漸層填充與斑馬紋表格。
    2.  **功能注入**：實作「5 秒自動輪詢」機制與「異常紅色預警」邏輯。
    3.  **交互細化**：優化 Loading 轉場與 Tooltip 顯示效果。
    4.  **函數命名對齊**：前端渲染函數統一命名為 `updateDashboard()`，符合 prompt 規格。

### 第四階段：自動化預覽與 E2E 測試 (DevOps & QA)
*   **目標**：確保高品質產出，實現自動化驗證。
*   **具體任務**：
    1.  **啟動腳本 (`scripts/run_dashboard.py`)**：一鍵拉起 Web Server 並自動打開預覽。
    2.  **E2E 驗證腳本 (`tests/tester.py`)**：
        *   使用 Playwright 偵測 `<canvas>` 是否成功渲染。
        *   驗證 `fetch` 網路請求狀態是否為 200。
    3.  **異常場景模擬**：編輯 `data/data.json` 將異常率改為 > 5%，確認紅色脈動預警觸發。
    4.  **雙模式驗證**：分別測試靜態模式與 `?mock=true` 隨機模式。

### 第五階段：Antigravity 統一標準重構 (Standardization)
*   **目標**：依據 Antigravity 統一架構規範進行物理遷移並修正交叉引用路徑。
*   **具體任務**：
    1.  **物理遷移**：根據規範將 .py, .html, .json, .md, .txt 移入對應子目錄 (`src/`, `web/`, `data/`, `docs/`, `tests/`, `reports/`)。
    2.  **路徑修正**：修正 `server.py` 的 `data.json` 讀取路徑與靜態文件路徑。
    3.  **環境預備**：建立空目錄 `reports/` 供產出物存放。

---

## 📂 3. 目錄結構與管理 (Final Structure)

依據 Antigravity 統一架構規範，確保各組件職責明確：
*   **`docs/`**：存放系統設計文件 (如 `gemini_canvas_v1.0.md`) 與實作計畫。
*   **`src/`**：存放核心服務代碼 (如 `server.py`)。
*   **`web/`**：存放前端畫布組件與模板。
*   **`data/`**：存放靜態數據源 (`data.json`)。
*   **`reports/`**：存放產出的畫布快照與品質分析。
*   **`scripts/`**：存放啟動與維運腳本 (如 `run_dashboard.py`)。
*   **`tests/`**：存放自動化測試腳本 (如 `tester.py`)。

---

## ✅ 4. 測試與驗證項 (Checklist)

### 功能性驗證
- [x] **數據連通性**：`/api/data` 穩定回傳 JSON (完成)
- [x] **Gen-UI 完整性**：AI 生成的 HTML 能獨立運行 (完成)
- [x] **自動輪詢**：圖表隨數據改變動態更新 (完成)
- [x] **函數命名**：前端渲染函數已對齊為 `updateDashboard()` (完成)
- [x] **靜態數據源**：`/api/data` 預設從 `data/data.json` 讀取 (完成)
- [x] **隨機模式**：`/api/data?mock=true` 啟用隨機生成 (完成)

### 穩定性檢核 (Robustness)
- [x] **響應式佈局**：手機端解析度下佈局正確 (已驗證)
- [x] **負載驗證**：1000 數據點 Chart.js 渲染流暢 (已驗證)
- [x] **錯誤處理**：後端斷開時前端不當機 (完成)

### 數據源驗證 (待實作後勾選)
- [x] **靜態一致性**：多次 refresh 數據一致 (已驗證)
- [x] **隨機差異性**：`?mock=true` 每次數據不同 (已驗證)
- [ ] **異常預警**：編輯 `data.json` 異常率 > 5% 觸發紅色脈動

---
*最後修改日期: 2026-03-11*
*執行計畫產生日期：2026-03-11*
*狀態：Phase 1 數據層改造已完成，異常預警待手動驗證 ✅*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
