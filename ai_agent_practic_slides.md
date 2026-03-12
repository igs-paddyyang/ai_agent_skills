---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
  code { background-color: #f1f3f5; color: #007bff; }
  h2 { color: #1a73e8; font-weight: bold; }
  .origin-box { background: #e8f0fe; padding: 15px; border-radius: 8px; border-left: 5px solid #1a73e8; }
  .highlight { color: #d9480f; font-weight: bold; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
  th { background-color: #f8f9fa; }
---

#  AI Agent 實戰系列 (0)：開發新思維
### 從「寫程式」到「下指令」的典範轉移
**讓 AI 成為您的數位架構師與全職特助**

<div style="position: absolute; bottom: 40px; right: 40px; font-size: 0.7em; text-align: right; color: #666;">
對象：非技術開發人員 / AI 指揮官<br>
講師：<b>paddyyang</b><br>
技術棧：Agentic Workflow | Antigravity
</div>

---

##  Module 1: 核心觀念的典範轉移

<div class="origin-box">

**傳統開發 (Coding)**：
人類思考邏輯 -> 寫代碼 (Python/JS) -> 解決 Bug -> 完成。

<span class="highlight">**AI CLI 開發 (Agentic)**：</span>
人類定義「需求」與「邊界」 -> **指揮 AI** -> AI 自主寫碼、測試、修復 -> 交付成果。
</div>

**重點：您不再需要親自動手寫 Code，您需要的是清楚的「規格」與「邏輯」。**

---

##  Module 2: AI Agent 的三大核心支柱

為了讓 AI 穩定運作並具備「專案感知」，我們在 `.agent` 中定義了核心支柱：

1.  **腦 - 強制約束 (Rules)**：定義 Agent 「不能做什麼」與對話守則的護欄文件。
    *   *對應目錄：* `.agent/rules/`
2.  **手 - 原子能力與流程 (Skills & Workflows)**：執行特定任務的工具與 SOP 流程。
    *   *對應目錄：* `.agent/skills/` 與 `.agent/workflows/`
3.  **心 - 背景與記憶 (Context)**：儲存專案設計、關鍵技術與進度的持久化記憶。
    *   *對應目錄：* `.agent/context/`

---

##  Module 3: 演進史  龍蝦的「脫殼」重生

<div class="origin-box">

1. **起源 (ClawdBot)**：2025 年 11 月發起，定位為具備利爪的「網頁獵取者」。
2. **轉折 (Moltbot)**：面對法律風暴進行「脫殼」，象徵成長的陣痛與擺脫模型依賴。
3. **蛻變 (OpenClaw)**：最終進化為開放體系。支援多種模型，強調**「資料主權」**與地端 AI 革命。
</div>

**演進核心：從單純的「工具」升級為「Your Machine, Your Keys, Your Data」的數位分身。**

---

##  結語：開啟您的 AI 統帥之路

### **核心心法**
1.  **規格即能力**：說明越清楚，AI 越強大。
2.  **全代理授權**：讓 AI 自行處理環境部署與自我修復。
3.  **掌握交付物**：關注邏輯與成果，而非繁瑣的實作細節。

> **「最好的開發工具不是軟體，而是您那顆清晰且具邏輯的大腦。」**

---

#  AI Agent 實戰系列 (1)：ClawdBot 智庫助理
### 整合 Google Antigravity + Gemini + SQLite
**打造具備「意圖感知」與「主動獵取」能力的個人 AI 特寫**

<div style="position: absolute; bottom: 40px; right: 40px; font-size: 0.7em; text-align: right; color: #666;">
對象：非技術開發人員 / AI 指揮官<br>
講師：<b>paddyyang</b><br>
技術棧：SQLite | Gemini API | Antigravity
</div>

---

##  課程大綱

1. **核心願景**：為什麼需要 ClawdBot？
2. **架構設計**：數據流與智慧路由機制 (System Design)
3. **技術拆解**：爬蟲引擎、記憶保險箱與意圖分類
4. **實作路徑**：從環境配置到 Telegram 部署
5. **策略優化**：確保系統的魯棒性 (Robustness)

---

##  Module 1: 核心願景與目標

<div class="origin-box">

* **痛點**：資訊碎片化、網頁內容難以檢索、AI 幻覺 (Lack of Grounding)。
* **解決方案**：
    * **主動獵取**：自動將 URL 轉化為乾淨的 Markdown 格式。
    * **長效記憶**：利用 SQLite 建立本地化的個人知識庫。
    * **智慧過濾**：自動區分「深度研究」與「日常閒聊」。
</div>

**目標：打造一個懂你、且擁有「外部眼界」的數位第二大腦。**

---

##  Module 2: 系統架構圖 (System Design)

* **輸入層**：Telegram Bot API (User Interaction)
* **大腦層**：
    * **Intent Classifier**：判斷用戶意圖 (Research vs. Casual)。
    * **Agent Runtime**：調度工具、邏輯路由與 Prompt 編排。
* **工具層**：
    * **Clawd Engine**：負責 Web Requests 與 Markdown 轉換。
* **存儲層**：
    * `raw_crawls`：存放原始文獻。
    * `memories`：存放對話與精華摘要。

---

##  Module 3: 數據結構與記憶保險箱

* **SQLite 角色**：輕量、本地、支持持久化。
* **關鍵 Table 設計**：
    * **`raw_crawls`**：使用 `UNIQUE` 約束 URL，避免重複爬取。
    * **`memories`**：加入 `is_star` 欄位，實作「一鍵存入智庫」。

<div class="origin-box">

**技術亮點**：這不是單純的聊天機器人，這是一個具備 **RAG (Retrieval-Augmented Generation)** 雛形的個人智庫系統。
</div>

---

##  Module 4: 爬蟲技術與魯棒性處理

### **標準工作流**
1. `requests.get()` 獲取 HTML -> `BeautifulSoup` 清洗標籤 -> `markdownify` 轉化文本。

### **魯棒性 (Robustness) 處理**
> **通俗解釋**：指系統的「強健度」。確保程式在遇到網路斷線、網站封鎖時不會當機。

*   處理 **403 Forbidden** (偽裝 User-Agent)。
*   實作 **超時 (Timeout)** 與編碼自動偵測。
*   **測試指令**：`py clawdbot/src/crawler_skill.py "URL"`

---

##  Module 5: 意圖分類與 UX 體驗

* **智慧路由**：
    * **Research**：偵測到 URL -> 發動 Clawd -> 深度分析 -> 呼叫 `summarize_content()`。
    * **Casual**：一般問候 -> 呼叫 `chat()` -> 直接友善回應，不觸發摘要格式。
* **分流設計重點**：
    * `summarize_content()` 與 `chat()` 使用獨立 prompt，嚴格分離，避免格式污染。
* **UX 體驗 (Safety Guard)**：
    * **Progressive Feedback**：` 正在獵取...` -> ` 正在分析...`
    * **`escape_md`**：嚴格轉義 Telegram 特殊字元，避免訊息發送失敗。

---

##  結語：打造您的數位大腦第二層

### **核心心法**
1. **掌握數據主權**：透過 SQLite 將知識留在本地，不依賴雲端。
2. **意圖驅動開發**：讓 AI 學習判斷何時調用工具，而非盲目回應。
3. **持續迭代**：從簡單的爬取開始，逐步構建您的專屬智庫。

> **「最好的開發工具，是那些能與您的邏輯共鳴，並無限延展您專業邊界的系統。」**

---

# 實戰對話(1)

## **分析clawdbot\_v1\.0\.md規格文件，幫我列出可執行計畫**
### 第一階段：基礎設施與資料庫開發 (Foundation)
### 第二階段：Clawd 獵取引擎與過濾器 (Scraping Engine)
### 第三階段：智慧路由與分析大腦 (Brain & Routing)
### 第四階段：Telegram 互動介面與部署 (Interface & UX)

---

#  實戰對話(2)

## **把可執行計畫產出一個任務文件，並放入相同目錄下**
### **開始執行任務1**
### **開始執行任務2**
### **開始執行任務3**
### **開始執行任務4**

---

#  AI Agent 實戰系列 (2)：遊戲研發自動化
### 技能庫應用與 GDD 文件生成
**從對話機器人轉向「代理人工作流」的生產力革命**

<div style="position: absolute; bottom: 40px; right: 40px; font-size: 0.7em; text-align: right; color: #666;">
對象：非技術開發人員 / AI 指揮官<br>
講師：<b>paddyyang</b><br>
技術棧：Game Dev | Skill Library | GDD
</div>

---

##  Module 1: AI 2.0 時代的生產力新範式

### **1. 為什麼傳統對話無法支撐專業研發？**
*   **不穩定性**：同樣的 Prompt，每次結果都不同。
*   **邏輯斷層**：缺乏標準作業程序 (SOP)。

### **2. Agentic Skills 框架**
*   將專業 SOP **模組化** 與 **封裝化**。
*   為 AI 裝上「專業外掛」，確保輸出符合工業規格。

---

##  Module 2: 全球最強 AI 技能庫

### **Antigravity Awesome Skills**
*   介紹 [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) 的 1200+ 技能體系。

### **核心分類（研發視角）**
*   `.agent/skills/level-designer/`：關卡設計師，負責環境氛圍與危險要素。
*   `.agent/skills/character-creator/`：角色設計師，負責 Boss 設計與邏輯一致性。
*   `.agent/skills/skill-creator/`：技能建立器，用於建立新的自訂技能。
*   `antigravity-awesome-skills/game-development/`：社群技能庫參考。

---

##  Module 3: 實作案例  GDD 自動生成器

### **任務需求 (Mission)**
根據「深海科研站」主題，一鍵產出具備邏輯一致性的遊戲設計文件。

### **鏈式調用工作流 (Chain of Thought)**
1.  **技能載入**：`gdd_generator.py` 從 `.agent/skills/` 讀取 `SKILL.md` 技能定義。
2.  **環境設計**：將 `level-designer` 技能定義注入 prompt，調用 `@level-designer` 生成地圖挑戰。
3.  **角色注入**：將 `character-creator` 技能定義 + 環境輸出注入 prompt，調用 `@character-creator` 生成 Boss。
4.  **成果驗證**：檢查 Boss 技能是否能對應關卡障礙（邏輯一致性）。

---

##  結語：開啟您的 Agentic 研發之路

### **核心心法**
1.  **規格即能力**：說明越清楚，AI 越強。
2.  **鏈式調用**：將大任務拆解，讓 AI 逐步完成。
3.  **持續迭代**：將經驗封裝成 Skill 檔案，實現知識永續。

> **「最好的開發工具，是將您的專業經驗編寫成 AI 可讀取的技能格式。」**

---

#  實戰對話(1)

## **分析agent\_skills\_v1\.0\.md規格文件，幫我列出可執行計畫**
### 第一階段：環境佈建與基礎設施 (Infrastructure)
### 第二階段：技能掛載與連通性驗證 (Connection & Loading)
### 第三階段：鏈式 GDD 生成器實作 (Workflow Engine)
### 第四階段：模型校準與自動化報告 (Calibration & QA)

---

#  實戰對話(2)

## **把可執行計畫產出一個任務文件，並放入相同目錄下**
### **開始執行任務1**
### **開始執行任務2**
### **開始執行任務3**
### **開始執行任務4**

---

#  AI Agent 實戰系列 (3)：全自動化前端開發
### FastAPI + Gemini + Antigravity
**體驗「Spec Coding」與「Vibe Coding」的極致結合**

<div style="position: absolute; bottom: 40px; right: 40px; font-size: 0.7em; text-align: right; color: #666;">
對象：非技術開發人員 / AI 指揮官<br>
講師：<b>paddyyang</b><br>
技術棧：FastAPI | Gemini API | Antigravity
</div>

---

##  Module 1: 定義數據源頭與路由 (FastAPI)

<div class="origin-box">

* **核心架構**：
    * 使用 `FastAPI` 建立非同步 API。
    * 建立 `/api/data` 接口，預設從 `data/data.json` 讀取固定數據，支援 `?mock=true` 啟用隨機模式。
* **開發重點**：
    * 定義 Pydantic 模型，確保數據結構與前端的「數據契約」一致。
    * 靜態數據源確保可控、可重現、可手動編輯；隨機模式用於壓力測試與動態展示。
</div>

**重點：在 Vibe Coding 中，後端數據結構是前端生成的唯一基準。**

---

##  Module 2: 結構化約束與視覺定義

<div class="origin-box">

* **提詞策略**：
    * 將 FastAPI 的數據範例 (JSON Schema) 餵給 Gemini。
    * 要求產出**單一 HTML 檔案** (內建 Tailwind CSS 與 Chart.js)。
* **關鍵規範**：
    * 「圖表配色必須符合系統的深色模式規範。」
    * 「請將 JS 邏輯封裝在 `window.onload` 之後。」
</div>

**目標：將數據轉換為精確的視覺語言，而非隨機生成。**

---

##  Module 3: 自動化部署與 E2E 測試

<div class="origin-box">

* **自動化部署**：
    * 透過 Antigravity 一鍵拉起 FastAPI 服務。
    * 自動開啟瀏覽器並全螢幕呈現儀表板。
* **無人值守測試 (E2E)**：
    * 利用 Playwright 自動驗證渲染成功、數據連通與響應式佈局。
</div>

**優勢：省略複雜配置，實現「自動生成、自動測試」的閉環。**

---

##  結語：Vibe Coding 實戰

### **核心心法**
1.  **定義 Spec**：制定數據格式與業務邏輯。
2.  **傳達 Vibe**：在畫布微調中引導 AI 達到期望的感官效果。
3.  **驗證 Result**：透過自動化腳本確保功能完備且穩定。

> **「這不是在寫程式，這是在指揮一場數位的交響樂。」**
---

#  實戰對話(1)

## **分析gemini\_canvas\_v1\.0\.md規格文件，幫我列出可執行計畫**
### 第一階段：後端數據開發與 API 建設 (Data Infrastructure)
### 第二階段：視覺規範與 Gen-UI 提詞策略 (Design & Prompting)
### 第三階段：Canvas 持久化與增量優化 (UI Refinement)
### 第四階段：自動化部署與 Playwright 測試 (DevOps & QA)

---

#  實戰對話(2)

## **把可執行計畫產出一個任務文件，並放入相同目錄下**
### **開始執行任務1**
### **開始執行任務2**
### **開始執行任務3**
### **開始執行任務4**

---
*Generated by paddyyang (IGS) | 2026-03-10*
