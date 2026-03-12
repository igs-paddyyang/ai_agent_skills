# 📜 AI 程式開發與編碼規範 (AI Coding Standards)

**目標：** 統一系統代碼品質、確保 Python 3.12 最佳實踐，並強制執行「規格優先」流程。

---

## 1. 核心技術棧與風格 (Core Tech Stack)

* **語言版本**：強制使用 **Python 3.12+**。
* **類型標註 (Type Hinting)**：所有函數定義**必須**包含類型標註。
* **縮進與格式**：遵循 **PEP 8**。
* **編碼 (Encoding)**：所有文件（含 Batch 檔）必須使用 **UTF-8**。
* **非同步架構**：涉及網路 I/O (Telegram API, DB 查詢) 時，必須優先使用 `asyncio`。

---

## 2. 規格優先開發 (Spec-First Development)

在實作任何數據處理邏輯前，必須遵循以下順序：
1. **定義 Schema**：先產出 Pydantic Model 或 JSON Schema。
2. **驗證數據**：輸入數據必須通過 Schema 驗證。
3. **邏輯實作**：根據通過驗證的數據進行運算。
4. **輸出封裝**：輸出必須符合前端預期格式。

---

## 3. 安全與數據治理 (Security & Governance)

* **Secret 管理**：嚴禁將 API Key、資料庫密碼寫死 (Hard-code)。必須使用 `os.getenv()` 或 `.env` 檔案。
* **數據脫敏 (Masking)**：日誌與分析輸出禁止記錄用戶 PII (手機號、姓名、Email)。
* **SQL 注入防護**：查詢資料庫時，禁止使用字串拼接，必須使用參數化查詢。

---

## 4. 錯誤處理與日誌規範

* **優雅降級**：若數據查詢失敗，應回傳包含錯誤訊息的標準 JSON，而非讓程式崩潰。
* **結構化日誌**：日誌應包含 `timestamp`, `level`, `skill_id`, 以及 `trace_id`。

---

## 5. UI/UX 與 Canvas 規範

* **自適應佈局**：輸出的 HTML/CSS 必須採用百分比或 Flex 佈局。
* **配色一致性**：統一使用深色主題配色規範 (`#0f172a` 背景, `#00d4ff` 主色)。

---
*最後更新日期: 2026-03-10*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
