# 🚀 AI Agent 實作指南：Canvas 自動化數據儀表板 (v1.1)

# 作者: paddyyang
# 最後修改日期: 2026-03-11

**目標：** 透過 FastAPI + Gemini API + Antigravity 打造「自動生成、偵測與測試」的數據儀表板，實現從數據定義到視覺化產出的自動化閉環。

---

## 📋 1. 需求分析 (Requirement Analysis)

### 1.1 核心功能需求
*   **數據源服務 (Data Provider)**：建立 FastAPI 後端，從 `data/data.json` 讀取結構化數據，提供穩定且可編輯的 JSON 接口。
*   **自動化繪圖 (Gen-UI)**：利用 Gemini API 根據數據契約自動生成包含 Tailwind CSS 與 Chart.js 的單一 HTML 檔案。
*   **即時精煉 (Canvas Refinement)**：在 Antigravity Canvas 環境中進行 UI 的增量優化與視覺微調。
*   **全自動測試 (E2E Test)**：利用 Playwright 進行無人值守測試，驗證圖表渲染、數據連通性與響應式佈局。

### 1.2 技術約束與驗證指標
| 功能模組 | 驗證前置需求 | 模組獨立性 | 驗證指標 |
| :--- | :--- | :--- | :--- |
| **Data Provider** | Python 3.10+ | 高度獨立 | 透過 `/api/data` 獲取正確 JSON 結構。 |
| **Data Source** | `data/data.json` 存在 | 高度獨立 | JSON 結構符合 `DashboardData` schema。 |
| **Gen-UI Engine** | Gemini API Key | 中度獨立 | 輸出的 HTML 是否內含 `fetch` 邏輯與圖表載入。 |
| **Canvas UI** | Antigravity 環境 | 整合層 | 在畫布中是否能正確渲染數據並進行增量編輯。 |
| **E2E Tester** | Playwright | 高度獨立 | 腳本是否能偵測到 `<canvas>` 標籤內容與 200 OK。 |

---

## 🏗️ 2. 系統設計 (System Design)

### 2.1 數據架構 (Data Architecture)

#### 數據源策略
*   **預設模式（靜態檔案）**：從 `data/data.json` 讀取固定數據，確保可控、可重現、可手動編輯。
*   **模擬模式（隨機生成）**：透過 `GET /api/data?mock=true` 啟用，每次呼叫隨機產生數據，用於壓力測試與動態展示。

#### 數據契約 (Data Contract)
後端回傳 Pydantic 驗證過的 JSON，結構如下：
```json
{
  "kpi_cards":            [{ "title", "value", "trend", "color" }],
  "trend_data":           [{ "date", "users", "revenue" }],
  "category_ratio":       [{ "name", "value" }],
  "recent_transactions":  [{ "id", "user", "amount", "status" }]
}
```
前端 HTML 統一使用 `fetch('/api/data')` 進行異步數據獲取，呼叫 `updateDashboard()` 渲染至 DOM。

### 2.2 提詞框架 (Prompt Template)
為確保高品質產出，提詞應包含下列四個維度：
1.  **身份定義 (Role)**：資深前端與數據可視化專家。
2.  **技術棧 (Stack)**：HTML5, Tailwind CSS, Chart.js。
3.  **佈局規範 (Layout)**：4 個 KPI 卡片、左側趨勢圖、右側佔比圖、底部數據表格。
4.  **交互定義 (Interactive)**：Tooltip 懸停顯示、響應式縮放、手動重整按鈕。

### 2.3 目錄結構與管理 (Project Folder Structure)
依據 Antigravity 統一架構規範，確保邏輯、資源與報告職責分離：
*   **`docs/`**：存放系統設計文件 (如 `gemini_canvas_v1.0.md`) 與實作計畫。
*   **`src/`**：存放核心服務代碼 (如 `server.py`)。
*   **`web/`**：存放前端畫布組件與模板。
*   **`data/`**：存放靜態數據源 (`data.json`)。
*   **`reports/`**：存放生成的畫布快照與品質分析。
*   **`scripts/`**：存放啟動與維運腳本。
*   **`tests/`**：存放自動化測試腳本。

---

## 🛠️ 3. 實作路徑 (Implementation Workflow)

### Phase 1: 數據層建設 (Data Infrastructure)
1.  建立 `data/data.json`，填入符合 `DashboardData` schema 的固定業務數據。
2.  實作 FastAPI 異步伺服器，`/api/data` 預設從 `data.json` 讀取。
3.  保留 `?mock=true` 參數啟用隨機模式，用於動態展示與壓力測試。
4.  開發 `/dashboard` 靜態檔案路由。

### Phase 2: 視覺定義與圖表規範
1.  **配色方案**：指定主色 (#2563eb)、成功色 (#10b981) 與警告色 (#ef4444)。
2.  **專業圖表細節**：
    *   **折線圖**：平滑曲線 (tension: 0.4) 與漸層填充。
    *   **甜甜圈圖**：cutout 80%，底部圖例。
    *   **表格**：斑馬紋路 (Striped) 與狀態色標。

### Phase 3: Canvas 協作與增量編輯
1.  產出初版 HTML 後，於 Canvas 進行優化：
    *   「將折線圖改為漸層填充色，增加科技感。」
    *   「加入異常率 > 5% 的紅色脈動預警動畫。」
2.  **狀態處理**：加入 Loading 轉場與 Tooltip 顯示效果。
3.  **異常測試**：直接編輯 `data.json` 將異常率改為 > 5%，驗證預警 UI。

### Phase 4: 自動化部署與 E2E 測試
1.  利用 `scripts/run_dashboard.py` 一鍵拉起服務並開啟瀏覽器。
2.  E2E 測試驗證 `<canvas>` 渲染、API 200 OK、KPI 卡片數量。
3.  **場景切換測試**：分別用 `data.json`（固定）和 `?mock=true`（隨機）驗證兩種模式。

---

## ✅ 4. 驗證與測試指南 (Testing Guide)

### 4.1 自動化瀏覽測試 (E2E)
*   **渲染驗證**：檢查 `<canvas>` 標籤是否成功生圖。
*   **連通性驗證**：監控網路請求，確認 `fetch` 成功獲取 200 狀態。
*   **響應式驗證**：自動調整螢幕寬度，檢查 Layout 是否符合呼吸感。

### 4.2 數據源測試
*   **靜態模式**：多次 refresh，確認數據一致（來自 `data.json`）。
*   **隨機模式**：呼叫 `/api/data?mock=true`，確認每次數據不同。
*   **異常預警**：編輯 `data.json` 將異常率設為 > 5%，驗證紅色脈動動畫。

### 4.3 進階場景測試
*   **定時更新**：驗證「實時監控」開關每 5 秒成功觸發 `updateDashboard()`。
*   **錯誤處理**：關閉後端 API，確認前端不會當機。

---
*最後更新日期: 2026-03-11*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
