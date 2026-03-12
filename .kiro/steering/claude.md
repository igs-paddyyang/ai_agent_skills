---
inclusion: always
# 📌 注入模式：永遠自動注入
# 📋 用途：AI 行為準則與代碼風格規範，每次對話必須載入
# ✏️ 維護：架構決策改變時更新，日常開發不需修改
---

# 行為準則（AI 協作規範）

> **唯一來源聲明**：此檔案是 AI 行為準則的唯一權威來源。
> `.agent/rules/` 下的原始檔供人類閱讀參考，AI 以本文件為準。
> 專案當前進度請參閱 `memory.md`，協作 SOP 請參閱 `ai_workflow.md`。

---

## 🧠 核心思維：Skill-First

本專案的核心模式：

> **SKILL.md（劇本）** + **Gemini API（演員）** + **Python 腳本（導演）**

- **SKILL.md**：定義 AI 角色、產出規範、格式要求、品質檢核標準
- **Gemini API**：接收含技能定義的 Prompt，按規範生成內容
- **Python 腳本**：載入技能 → 組裝 Prompt → 呼叫 Gemini → 串接上下文 → 組裝產出

在修改或新增任何程式碼前，先確認：這是技能定義的問題，還是腳本邏輯的問題？

---

## ✍️ 代碼風格

### 命名規範
| 類型 | 格式 | 範例 |
|---|---|---|
| Python 檔案 | `snake_case` | `gdd_generator.py` |
| 技能目錄 | `kebab-case` | `level-designer/` |
| 類別名稱 | `PascalCase` | `SkillLoader` |
| 變數 / 函式 | `snake_case` | `load_skill()` |

### Python 規範
- Python 3.12+，遵循 PEP 8
- 所有函數定義包含 Type Hinting
- 所有檔案使用 UTF-8 編碼
- 嚴禁硬編碼 API Key，一律用 `os.getenv()` 或 `.env`

### `.agent/skills/` 目錄規則
- 每個技能一個目錄：`.agent/skills/{skill-name}/`
- 必備：`SKILL.md`（技能定義，Markdown 格式）
- 可選：`references/`（參考資料）、`scripts/`（輔助腳本）、`examples/`（範例）

---

## 🚫 禁止事項

| 禁止 | 原因 |
|---|---|
| 硬編碼 API 金鑰 | 安全風險，一律用 `.env` |
| 破壞 SKILL.md 的結構格式 | 技能定義是 Prompt 注入的來源，格式錯誤會影響生成品質 |
| 跳過技能載入直接寫死 Prompt | 違反 Skill-First 原則，失去可替換性 |
| 在生成內容中包含 PII | 日誌與產出禁止記錄用戶個資 |

---

## 🌐 語言規範

- 所有對外產出（GDD、報告）一律使用**繁體中文**
- 代碼內的 `print` 日誌可使用英文（方便 Debug）
- 文件與註解優先使用繁體中文

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
