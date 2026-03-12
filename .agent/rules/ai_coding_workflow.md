# 🔄 AI 開發工作流規範 (AI Coding Workflow)

**目標：** 說明如何有效利用 `.agent` 目錄下的四類檔案（Rules, Skills, Workflows, Context）來驅動 AI Agent 的開發運作。

---

## 1. Rules：系統護欄 (Passive Guardrails)

* **運作模式**：Agent 啟動時自動載入（被動監控），確保行為不偏離規範。
* **主要檔案**：
    * **`gemini.md`**：定義 Agent 的人格定位與 PDCA 執行邏輯（計畫、執行、驗證、修正）。
    * **`ai_coding_standards.md`**：定義代碼風格（Python 3.12+、Type Hinting）與安全紅線。
* **使用方式**：無需手動調用，Agent 在每一步動作前均會自動對齊這些規則。

---

## 2. Skills：原子化能力 (On-demand Capabilities)

* **運作模式**：Agent 根據任務需求，自動判斷並動態調用的功能模組。
* **存放路徑**：`.agent/skills/{skill-name}/`
* **核心組成**：
    * **`SKILL.md`**：技能的靈魂，定義該技能「能做什麼」及調用 Schema。
    * **`scripts/`**：存放該技能的實體執行腳本（Python/Node.js）。
* **使用方式**：當 Agent 判斷需要執行特定任務（如數據分析、圖表渲染）時，會查閱 `SKILL.md` 並執行對應腳本。

---

## 3. Workflows：標準 SOP (Active Sequences)

* **運作模式**：預定義的多步驟自動化序列，通常由特定指令（Slash Command）觸發。
* **存放路徑**：`.agent/workflows/`
* **應用場景**：專案部署、全面的代碼審查、定期的日報生成。
* **使用方式**：透過輸入 `/` 指令或明確要求「執行 [工作流名稱]」來啟動，Agent 將嚴格遵循 SOP 步驟執行。

---

## 4. Context：知識記憶 (Semantic Knowledge)

* **運作模式**：存放專案的歷史決策、架構設計與當前狀態，作為 Agent 的長期記憶。
* **主要檔案**：
    * **`memory.md`**：記錄當前進度、技術棧與未來計畫。
    * **`ai_agent.md`**：定義系統的邏輯架構與模組職責。
* **使用方式**：當 Agent 需要理解背景（Context Awareness）或接續上次進度時，會主動檢索這些文件。

---

## 5. 標準執行 PDCA 循環 (PDCA Cycle)

1. **Plan (計畫先行)**：Agent 查閱 Context 與 Rules，產出任務清單 (Task List)。
2. **Do (全代理執行)**：依據計畫，調用對應的 Skills 或執行代碼撰寫。
3. **Check (驗證)**：主動使用 Terminal 運行測試或啟用 Browser 點擊驗證。
4. **Action (修正與交付)**：若失敗則依據 Rules 啟動自我修正；若成功則產出 Artifacts 交付給「指揮官」。

---
*最後更新日期: 2026-03-10*
