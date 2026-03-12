---
name: skill-creator
description: "當使用者要求建立新技能、打造技能、製作自訂技能、開發 CLI 技能，或想要擴充 CLI 功能時，應使用此技能。自動化完成整個技能建立流程，包含腦力激盪、範本套用、驗證與安裝。"
category: meta
risk: safe
source: community
tags: "[自動化, 鷹架建構, 技能建立, 元技能]"
date_added: "2026-03-11"
---

# skill-creator（技能建立器）

## 用途

依循 Anthropic 官方最佳實踐，以零手動配置的方式建立新的 CLI 技能。此技能自動化完成腦力激盪、範本套用、驗證與安裝流程，同時維持漸進式揭露模式與寫作風格標準。

## 何時使用此技能

適用情境：
- 使用者想要以自訂功能擴充 CLI
- 使用者需要依照官方標準建立技能
- 使用者想要將重複性 CLI 任務自動化為可重用技能
- 使用者需要將領域知識封裝為技能格式
- 使用者需要本地與全域安裝選項

## 核心能力

1. **互動式腦力激盪** — 協作式會議，定義技能用途與範圍
2. **提詞增強** — 可選整合 prompt-engineer 技能進行精煉
3. **範本套用** — 從標準化範本自動產生檔案
4. **驗證** — 針對 Anthropic 標準進行 YAML、內容與風格檢查
5. **安裝** — 本地儲存庫或全域安裝（含符號連結）
6. **進度追蹤** — 視覺化進度條，顯示每個步驟的完成狀態

## 步驟 0：環境偵測

在開始建立技能之前，收集執行環境資訊：

```bash
# 偵測可用平台
COPILOT_INSTALLED=false
CLAUDE_INSTALLED=false
CODEX_INSTALLED=false

if command -v gh &>/dev/null && gh copilot --version &>/dev/null 2>&1; then
    COPILOT_INSTALLED=true
fi

if [[ -d "$HOME/.claude" ]]; then
    CLAUDE_INSTALLED=true
fi

if [[ -d "$HOME/.codex" ]]; then
    CODEX_INSTALLED=true
fi

# 判斷工作目錄
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILLS_REPO="$REPO_ROOT"

# 檢查是否在 cli-ai-skills 儲存庫中
if [[ ! -d "$SKILLS_REPO/.github/skills" ]]; then
    echo "⚠️  不在 cli-ai-skills 儲存庫中，將建立獨立技能。"
    STANDALONE=true
fi

# 從 git config 取得使用者資訊
AUTHOR=$(git config user.name || echo "Unknown")
EMAIL=$(git config user.email || echo "")
```

**需要收集的關鍵資訊：**
- 目標平台（Copilot、Claude、Codex，或全部）
- 安裝偏好（本地、全域、或兩者皆是）
- 技能名稱與用途
- 技能類型（通用、程式碼、文件、分析）

## 主要工作流程

### 進度追蹤指引

在整個工作流程中，於每個階段開始前顯示視覺化進度條，讓使用者掌握進度：

```
[████████████░░░░░░] 60% - 步驟 3/5：建立 SKILL.md
```

**格式規範：**
- 寬度 20 字元（使用 █ 表示已完成，░ 表示未完成）
- 百分比依據當前步驟（步驟 1=20%、步驟 2=40%、步驟 3=60%、步驟 4=80%、步驟 5=100%）
- 步驟計數器顯示 當前/總數（例如「步驟 3/5」）
- 簡短描述當前階段

### 階段 1：腦力激盪與規劃

```
[████░░░░░░░░░░░░░░] 20% - 步驟 1/5：腦力激盪與規劃
```

**向使用者提問：**

1. **這個技能要做什麼？**（自由描述）
   - 範例：「協助使用者透過分析堆疊追蹤來除錯 Python 程式碼」

2. **何時應該觸發？**（提供 3-5 個觸發短語）
   - 範例：「除錯 Python 錯誤」、「分析堆疊追蹤」、「修復 Python 例外」

3. **這是什麼類型的技能？**
   - [ ] 通用型（預設範本）
   - [ ] 程式碼生成/修改
   - [ ] 文件建立/維護
   - [ ] 分析/調查

4. **應支援哪些平台？**
   - [ ] GitHub Copilot CLI
   - [ ] Claude Code
   - [ ] Codex
   - [ ] 全部（建議）

5. **提供一句話描述**（將出現在中繼資料中）
   - 範例：「分析 Python 堆疊追蹤並建議修正方案」

### 階段 2：提詞增強（選用）

```
[████████░░░░░░░░░░] 40% - 步驟 2/5：提詞增強
```

**詢問使用者：**
「是否要使用 prompt-engineer 技能來精煉技能描述？」
- [ ] 是 — 使用 prompt-engineer 增強清晰度與結構
- [ ] 否 — 使用目前的描述繼續

若選擇**是**：
1. 檢查 prompt-engineer 技能是否可用
2. 以目前描述作為輸入進行調用
3. 與使用者一起審閱增強後的輸出
4. 詢問：「接受增強版本還是保留原始版本？」

### 階段 3：檔案產生

```
[████████████░░░░░░] 60% - 步驟 3/5：檔案產生
```

**產生技能結構：**

```bash
# 將技能名稱轉換為 kebab-case
SKILL_NAME=$(echo "$USER_INPUT" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

# 建立目錄
mkdir -p ".agent/skills/$SKILL_NAME"/{references,examples,scripts}
```

**套用範本：**

1. **SKILL.md** — 使用對應範本：
   - 替換佔位符：
     - `{{SKILL_NAME}}` → kebab-case 名稱
     - `{{DESCRIPTION}}` → 一行描述
     - `{{TRIGGERS}}` → 逗號分隔的觸發短語
     - `{{PURPOSE}}` → 腦力激盪階段的詳細用途
     - `{{AUTHOR}}` → 來自 git config
     - `{{DATE}}` → 當前日期 (YYYY-MM-DD)
     - `{{VERSION}}` → "1.0.0"

2. **README.md** — 使用 readme 範本：
   - 面向使用者的文件（300-500 字）
   - 包含安裝說明
   - 加入使用範例

3. **references/**（選用但建議）：
   - 建立 `detailed-guide.md` 存放延伸文件（2k-5k 字）
   - 將冗長內容移至此處，保持 SKILL.md 在 2k 字以內

**顯示建立的結構：**
```
✅ 已建立：
   .agent/skills/your-skill-name/
   ├── SKILL.md (832 行)
   ├── README.md (347 行)
   ├── references/
   ├── examples/
   └── scripts/
```

### 階段 4：驗證

```
[████████████████░░] 80% - 步驟 4/5：驗證
```

**執行驗證腳本：**

```bash
# 驗證 YAML 前置資料
py scripts/quick_validate.py ".agent/skills/$SKILL_NAME"
```

**預期輸出：**
```
🔍 正在驗證 YAML 前置資料...
✅ YAML 前置資料有效！

🔍 正在驗證內容...
✅ 字數良好：1847 字
✅ 內容驗證完成！
```

**若驗證失敗：**
- 顯示具體錯誤
- 提供自動修正（常見問題）
- 要求使用者手動修正複雜問題

### 階段 5：安裝

```
[████████████████████] 100% - 步驟 5/5：安裝
```

**詢問使用者：**
「您想如何安裝此技能？」

- [ ] **僅儲存庫** — 檔案建立在 `.agent/skills/`（在儲存庫中使用）
- [ ] **全域安裝** — 在 `~/.agent/skills/` 建立符號連結（任何地方都可使用）
- [ ] **兩者皆是**（建議，隨 git pull 自動更新）
- [ ] **跳過安裝** — 僅建立檔案

### 階段 6：完成

```
[████████████████████] 100% - ✓ 技能建立成功！
```

**顯示摘要：**

```
🎉 技能建立成功！

📦 技能名稱：your-skill-name
📁 位置：.agent/skills/your-skill-name/
🔗 安裝方式：全域

📋 已建立的檔案：
   ✅ SKILL.md (1,847 字)
   ✅ README.md (423 字)
   ✅ references/（空，可放延伸文件）
   ✅ examples/（空，可放程式碼範例）
   ✅ scripts/（空，可放工具腳本）

🚀 後續步驟：
   1. 測試技能：在 CLI 中嘗試觸發短語
   2. 新增範例：在 examples/ 中建立可運行的程式碼範例
   3. 擴充文件：在 references/ 中加入詳細指南
   4. 提交變更：git add .agent/skills/your-skill-name && git commit
   5. 分享：推送到儲存庫供團隊使用
```

## 錯誤處理

### 平台偵測問題
若無法偵測平台，提供手動指定或僅儲存庫安裝選項。

### 範本未找到
若範本遺失，提供手動建立最小技能結構的選項。

### 驗證失敗
顯示具體錯誤，提供自動修正常見問題，複雜問題要求手動修正。

### 安裝衝突
若符號連結已存在，提供覆蓋、重新命名或跳過選項。

## 附帶資源

### references/
需要時載入的詳細文件：
- `output-patterns.md` — 輸出模式指南
- `workflows.md` — 工作流程模式指南

### scripts/
可執行的工具腳本：
- `init_skill.py` — 從範本初始化新技能
- `package_skill.py` — 將技能打包為可分發的 .skill 檔案
- `quick_validate.py` — 快速驗證技能結構

## 品質標準

**SKILL.md 要求：**
- 1,500-2,000 字（理想）
- 不超過 5,000 字（上限）
- 第三人稱描述格式
- 祈使句/不定式寫作風格
- 漸進式揭露模式

**README.md 要求：**
- 300-500 字
- 面向使用者的語言
- 清楚的安裝說明
- 實用的使用範例
