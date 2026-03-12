# 🤖 AI Agent 系統架構規範 (AI Agent Architecture)

**目標：** 定義本工作坊的 AI Agent 技能驅動架構與系統邏輯流。

---

## 1. 目錄結構規範 (Directory Structure)

`.agent` 資料夾採用四層分離結構：

* **`rules/` (系統護欄)**：定義全域編碼風格、資安規範。Agent 啟動時自動載入，全程監控行為。
* **`skills/` (原子能力)**：獨立的技能定義模組。每個技能包含 `SKILL.md` 定義檔，可附帶 `references/` 與 `scripts/`。
* **`workflows/` (標準 SOP)**：多步驟的序列指令（待建立）。
* **`context/` (知識庫)**：存放專案記憶、架構說明與技能歸類標準。

---

## 2. 技能庫架構 (Skills Architecture)

`.agent/skills/` 下有 13 個技能定義，按用途分類：

### 遊戲設計類（GDD 生成器使用）
* **`level-designer/`**：關卡環境設計（氛圍、危險要素、玩家目標）
* **`character-creator/`**：Boss 角色設計（名稱、技能、敘事動機）

### 文件與內容生成類
* **`document-summarizer/`**：文件摘要
* **`email-writer/`**：郵件撰寫
* **`presentation-writer/`**：簡報撰寫
* **`meeting-minutes-writer/`**：會議紀錄
* **`sop-writer/`**：標準作業程序撰寫

### 行銷與分析類
* **`marketing-copywriter/`**：行銷文案
* **`social-media-writer/`**：社群媒體內容
* **`market-analyzer/`**：市場分析

### 客服與規劃類
* **`customer-support-agent/`**：客服回覆
* **`task-planner/`**：任務規劃

### 工具類
* **`skill-creator/`**：建立新技能的工具（含 scripts/ 與 references/）

---

## 3. 系統核心邏輯流 (Core Logic Flow)

以 GDD 生成器為例的鏈式工作流：

```mermaid
graph TD
    User((使用者)) -->|輸入主題| Generator[gdd_generator.py 導演]
    
    subgraph "鏈式生成流程"
        Generator -->|1. 載入 SKILL.md| LevelDesigner[level-designer 劇本]
        LevelDesigner -->|注入 Prompt| Gemini1[Gemini API 演員]
        Gemini1 -->|環境設計| Generator
        
        Generator -->|2. 載入 SKILL.md + 上下文| CharCreator[character-creator 劇本]
        CharCreator -->|注入 Prompt| Gemini2[Gemini API 演員]
        Gemini2 -->|Boss 設計| Generator
    end
    
    Generator -->|3. 組裝 GDD| Report[reports/GDD_{主題}.md]
```

### 層級職責說明

* **技能定義層** (`.agent/skills/`)：SKILL.md 定義 AI 角色與產出規範
* **編排層** (`agent_skills/src/`)：Python 腳本負責載入技能、組裝 Prompt、串接上下文
* **執行層** (Gemini API)：接收含技能定義的 Prompt，按規範生成內容
* **產出層** (`reports/`)：結構化 Markdown 報告

---
*最後更新日期: 2026-03-12*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
