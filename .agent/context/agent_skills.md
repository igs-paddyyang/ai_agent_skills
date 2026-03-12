# 🧩 AI Agent 技能歸類標準 (Skill Classification Standards)

**目標：** 定義 AI Agent 技能的歸類邏輯、目錄存放準則與版本控制策略，確保跨專案的一致性。

---

## 1. 技能存放目錄架構 (Skill Directory Structure)

AI Agent 採用三層目錄架構，確保業務邏輯與全域工具分流：

| 目錄層次 | 絕對路徑 / 模式 | 存放內容 | 版本控制 |
| :--- | :--- | :--- | :--- |
| **專案描述層** | `.agent/skills/{name}/SKILL.md` | 業務綁定的能力描述 | 隨專案 Git |
| **專案執行層** | `skills/{name}/` | Python 業務邏輯模組 | 隨專案 Git |
| **全域工具層** | `~/.gemini/antigravity/skills/` | 通用生產力工具 | 被動同步 |

---

## 2. 歸類判斷準則 (Classification Criteria)

滿足以下任一準則即歸入 **專案目錄** (`.agent/skills/`)：

* **準則 A：業務邏輯綁定 (Business Logic Coupling)**：
  涉及專案特有的計算邏輯（如：PlayBonus 轉換率計算）。換一個專案後 Skill 就失效者。
* **準則 B：特定數據規格 (Specific Data Schema)**：
  Input/Output Schema 具有強烈的專案特徵（如：必須讀取 `bonus_log.csv`）。
* **準則 C：執行層依賴 (Execution Layer Dependency)**：
  SKILL.md 必須調用專案實體目錄 `skills/` 下的專屬 Python 腳本。
* **準則 D：獨有操作流程 (Project-Specific SOP)**：
  遵循專案專屬的設計文件 (SDD/SRS) 作業程序（如：五步驟報表產出流）。

---

## 3. AI 核心技能歸類表

| Skill 名稱 | 歸類類型 | 滿足準則 | 核心理由 |
| :--- | :--- | :--- | :--- |
| **`@ai-orchestrator`** | 專案描述層 | A, C, D | 專案大腦，負責協排 AI 工作流順序。 |
| **`@ai-data-analyst`** | 專案描述層 | A, B, C | 定義了 AI 特有的 Spec-First 數據規格。 |
| **`@canvas-visualizer`** | 專案描述層 | A, B, C | 品牌與 UI 一致性，包含 AI 暗色主題配色規範。 |
| **`@bot-interface-master`** | 專案描述層 | A, C, D | 交互邏輯綁定，定義特定的選單按鈕與 Callback。 |
| **`@ai-security-guard`** | 專案描述層 | A, B, C | 包含 AI 專屬的數據脫敏規則與白名單路徑。 |

---

## 4. 通用工具與反例 (Global Utility Examples)

以下類型的 Skill 應放入 **全域目錄**，不隨單一專案移動：

* **`@code-cleanup`**：通用代碼格式化 (Black/Isort)，不涉及業務邏輯。
* **`@git-assistant`**：通用 Git Commit Message 生成。
* **`@web-search`**：通用網頁檢索與參考資料查找。
* **`@markdown-exporter`**：通用的文檔格式轉換 (MD to PDF/Word)。

---

## 5. 新增技能標準操作流程 (Action Flow)

1. **評估歸類**：使用四項準則 (A/B/C/D) 判斷技能屬性。
2. **目錄建立**：
   - 專案技能：在 `.agent/skills/` 建立 `SKILL.md`，在 `skills/` 建立執行模組。
   - 全域技能：直接於全域環境目錄建立單一 `SKILL.md`。
3. **更新記憶**：完成技能建立後，同步更新本文件與 `memory.md`。

---
*最後更新日期: 2026-03-10*
