# 🚀 AI Agent 實戰指南：遊戲研發自動化與技能庫應用 (v1.0)

# 作者: paddyyang
# 最後修改日期: 2026-03-11

**目標：** 利用 `.agent/skills/` 下的專業技能（`level-designer`、`character-creator`）與 `antigravity-awesome-skills` 技能庫，將 AI 轉化為具備遊戲開發專業知識的「代理人工作流」，實現 GDD 文件自動生成與研發流程自動化。

---

## 📋 1. 需求分析

### 1.1 核心功能需求
*   **技能庫掛載**：從 `.agent/skills/` 動態引用專業遊戲開發技能（`level-designer`、`character-creator`），並可擴充引用 `antigravity-awesome-skills` 技能庫中的子技能。
*   **鏈式任務編排**：將多個技能按順序串接（如：`@level-designer` -> `@character-creator` -> GDD 組裝）。
*   **技能定義驅動**：`gdd_generator.py` 從 `.agent/skills/{skill-name}/SKILL.md` 讀取技能定義，注入 prompt 作為系統指令。
*   **專業規格產出**：產出符合工業標準的遊戲設計文件 (Markdown 格式)。
*   **知識傳承自動化**：將資深開發者的經驗封裝為技能（使用 `skill-creator`）並進行自動化校準。

### 1.2 技術約束與驗證獨立性
| 功能模組 | 驗證前置需求 | 模組獨立性 | 驗證指標 |
| :--- | :--- | :--- | :--- |
| **技能讀取器 (Skill Loader)** | `.agent/skills/` 目錄存在 | **高度獨立** | 驗證是否能正確掃描 `.agent/skills/` 下的 SKILL.md 技能定義檔。 |
| **GDD 生成引擎** | Gemini API 金鑰 + 技能定義 | **中度獨立** | 從 `.agent/skills/level-designer/SKILL.md` 與 `.agent/skills/character-creator/SKILL.md` 載入技能定義，依主題命名產出（如 `reports/GDD_{主題}_{日期}.md`），使用 `gemini-2.0-flash`。 |
| **流程執行器 (Chain Runner)** | Python 3.10+ | **高度獨立** | 執行 `src/` 下的鏈式腳本，使用 `google-genai` 套件。 |
| **品質驗證器 (QA Validator)** | 邏輯測試案例 | **整合層** | 透過 `tests/test_api.py` 確保模型連通性後執行審計。 |

---

## 🏗️ 2. 系統設計

### 2.1 技能架構
*   **技能來源**：`.agent/skills/` 目錄下的獨立技能與技能庫。
*   **核心技能**：
    *   `.agent/skills/level-designer/`：關卡設計師，負責環境氛圍、危險要素與玩家目標。
    *   `.agent/skills/character-creator/`：角色設計師，負責 Boss 名稱、能力設計與敘事動機。
    *   `.agent/skills/skill-creator/`：技能建立器，用於建立新技能。
*   **技能庫**：
    *   `.agent/skills/antigravity-awesome-skills/`：1200+ 社群技能庫，提供 `game-development/game-design` 等參考。
*   **運作原理**：`gdd_generator.py` 從 `.agent/skills/{skill-name}/SKILL.md` 讀取技能定義，注入 prompt 作為系統指令，強制 AI 執行特定的思維鏈 (CoT)。

### 2.2 鏈式設計流程 (思維鏈)
1.  **載入技能**：`gdd_generator.py` 從 `.agent/skills/level-designer/SKILL.md` 與 `.agent/skills/character-creator/SKILL.md` 讀取技能定義。
2.  **輸入**：使用者輸入主題（例：深海科研站）。
3.  **步驟 1 (@level-designer)**：將技能定義注入 prompt，產出地圖挑戰與環境描述。
4.  **步驟 2 (@character-creator)**：將技能定義 + 步驟 1 輸出注入 prompt，產出與環境互動的 Boss。
5.  **輸出**：彙整兩者產出為包含引用與腳註的 Markdown 文件。

### 2.3 目錄結構與管理 (Project Folder Structure)
依據全域規範，確保設計、腳本與報告職責分離：
*   **`src/`**：存放核心業務邏輯腳本 (如 `gdd_generator.py`, `loader.py`)。
*   **`reports/`**：存放 AI 自動產出的 GDD 文件與品質分析報告 (含完成日期)。
*   **`scripts/`**：存放維運與啟動腳本。
*   **`tests/`**：存放環境驗證與品質校驗腳本。
*   **`backup/`**：存放重構前的備份內容。

## 🛠️ 3. 實作路徑

### 第一階段：技術環境與自動化部署
1.  **環境搭建**：建立虛擬環境 `venv` 並安裝依賴套件 `google-genai`, `python-dotenv`。
2.  **金鑰配置**：建立 `.env` 填入 `GOOGLE_API_KEY` 與伺服器設定。
3.  **庫同步**：執行 `git clone` 同步 `antigravity-awesome-skills` 到 `.agent/skills/antigravity-awesome-skills`。

### 第二階段：技能讀取與基礎測試
1.  **路徑檢索**：編寫 `loader.py` 驗證 `skills/` 目錄下的路徑連通狀況。
2.  **API 驗證**：運行 `list_models.py` 列出可用模型，並透過 `test_api.py` 驗證 `gemini-2.0-flash` 回應品質。

### 第三階段：GDD 自動生成器開發
1.  **鏈式腳本**：實作 `gdd_generator.py`，串接關卡 (Level) 與角色 (Character) 兩大技能組。
2.  **上下文傳遞**：確保階段一的地圖數據能精準傳遞給階段二的角色生成器。
3.  **主題式產出**：產出檔案預設存放在 `reports/` 並以主題與日期命名。例如：輸入「科幻太空實驗室」，將產出 `reports/GDD_科幻太空實驗室_20260311.md`。

### 第四階段：目錄重構與標準化
1.  **結構重構**：將腳本、文件、報告遷移至符合 Rule 4 規範的物理目錄。
2.  **品質報告**：於 `reports/` 產出品質動態分析。

---

## ✅ 4. 驗證與測試指南

### 4.1 邏輯一致性測試
*   **測試點**：檢查生成的 Boss 技能是否與地圖環境配對。
*   **準則**：若地圖為「水下」，Boss 卻擁有「火焰攻擊」，則視為驗證失敗。

### 4.2 多樣性與主題適應
*   **測試**：切換主題參數（如 SLG 與 RPG 差異）。
*   **預期**：AI 應根據不同的技能組標籤，自動切換產出的數值深度與描述風格。

### 4.3 終端運行驗證
*   **指令**：`py agent_skills/src/gdd_generator.py "深海科研站"`
*   **預期**：終端最後一行應顯示 `Generation SUCCESS: reports/GDD_深海科研站_*.md`。

---
*最後更新日期: 2026-03-11*


---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
