# skill-seeker Skill Spec

**作者**: paddyyang
**日期**: 2026-03-24
**版本**: v0.1
**目標**: 作為 skill-creator 的輸入，產出 skill-seeker 技能

---

## 1. 技能定義

- **名稱**: skill-seeker
- **一句話描述**: 將文件來源（URL、GitHub repo、本地檔案、PDF）自動轉換為符合 Kiro Skill 規範的技能草稿目錄
- **觸發描述（description 欄位草稿）**:
  > 讀取文件來源（文件網站 URL、GitHub repository、本地 Markdown/PDF 檔案）並自動轉換為完整的 Kiro Skill 草稿，產出 SKILL.md、README.md 與 references/ 結構。當使用者提到從文件建立技能、文件轉 Skill、doc to skill、自動產生技能、匯入文件為技能、將文件轉換為技能、documentation to skill、從 URL 建立技能、從 GitHub 建立技能時，請務必使用此技能。

## 2. 行為規格

### 2.1 輸入

- **文件來源**（必要）：以下任一種
  - 文件網站 URL（如 `https://docs.example.com/`）
  - GitHub repository URL 或 `owner/repo` 格式
  - 本地檔案路徑（`.md`、`.pdf`、`.txt`、`.html`）
  - 本地目錄路徑（含多個文件檔案）
- **技能名稱**（選用）：kebab-case，若未提供則從來源自動推導
- **技能描述提示**（選用）：使用者對技能用途的補充說明

### 2.2 處理邏輯

整體流程借鏡 Skill Seekers 的三階段架構（Ingest → Structure → Generate），但適配 Kiro Skill 規範：

**Phase 1：來源擷取（Ingest）**

1. 判斷來源類型（URL / GitHub / 本地檔案 / 本地目錄）
2. 根據類型使用對應工具擷取內容：
   - URL → 使用 web fetch 抓取頁面（支援 rendered 模式重試）
   - GitHub → 抓取 README.md，選擇性抓取關鍵子頁面（docs/、API reference）
   - 本地檔案 → 直接讀取檔案內容
   - 本地目錄 → 掃描目錄，讀取所有 `.md` / `.txt` / `.html` 檔案
3. 若為 GitHub repo，額外擷取：repo 描述、主要語言、目錄結構
4. 產出原始內容清單（每個來源頁面/檔案為一個條目）

**Phase 2：內容分析與結構化（Structure）**

1. 分析原始內容，識別以下區塊：
   - 概述/簡介（→ SKILL.md 核心指令）
   - API 參考（→ references/api-reference.md）
   - 使用指南/教學（→ references/usage-guide.md）
   - 設定/安裝（→ references/setup-guide.md）
   - 範例/最佳實踐（→ references/examples.md）
   - 其他專題內容（→ references/<topic>.md）
2. 評估內容量，決定 SKILL.md 是否需要拆分到 references/
   - 若核心指令 < 500 行 → 全部放 SKILL.md
   - 若核心指令 > 500 行 → 精簡版放 SKILL.md，詳細內容拆到 references/
3. 從內容中提取：
   - 技能名稱（若使用者未提供）
   - 一句話描述
   - 觸發關鍵字
   - 核心能力清單

**Phase 3：技能草稿產生（Generate）**

1. 產生 SKILL.md：
   - YAML frontmatter（name、description）
   - 核心指令（精簡版，聚焦「做什麼」和「怎麼做」）
   - 附帶資源索引（列出 references/ 中的檔案及用途）
2. 產生 README.md：
   - 使用 skill-creator/templates/readme.md 範本格式
   - 版本從 0.1.0 開始
   - 包含：功能說明、使用方式、檔案結構、變更紀錄
3. 產生 references/ 目錄下的各檔案
4. 執行自我檢核：
   - SKILL.md 行數 < 500
   - description ≤ 1024 字元
   - name 為 kebab-case ≤ 64 字元
   - 所有 references/ 檔案都在 SKILL.md 中被引用

### 2.3 輸出格式

產出完整的 Kiro Skill 目錄結構：

```
<skill-name>/
├── SKILL.md              # YAML frontmatter + 核心指令（< 500 行）
├── README.md             # 技能說明文件（版本 0.1.0）
└── references/           # 按需載入的詳細內容
    ├── api-reference.md  # API 參考（若有）
    ├── usage-guide.md    # 使用指南（若有）
    ├── setup-guide.md    # 設定指南（若有）
    ├── examples.md       # 範例集（若有）
    └── <topic>.md        # 其他專題（依內容而定）
```

SKILL.md 範例結構：

```yaml
---
name: <skill-name>
description: >
  <從文件內容自動產生的觸發描述，≤ 1024 字元>
---

# <技能名稱>

<核心指令：精簡版的文件內容，聚焦於 AI 如何使用這些知識>

## 使用時機

- <觸發情境 1>
- <觸發情境 2>

## 核心能力

<從文件中提取的關鍵能力與知識>

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/api-reference.md | API 詳細參考 | 需要查閱 API 時 |
| references/usage-guide.md | 使用指南 | 需要操作步驟時 |
```

### 2.4 邊界案例

- **來源內容過少（< 100 字）**：提示使用者內容不足以產生有意義的技能，建議補充來源
- **來源內容過多（> 50KB）**：聚焦最重要的部分，其餘放入 references/，並告知使用者已做取捨
- **來源無法存取（404、需登入）**：回報錯誤，建議使用者提供本地檔案或檢查 URL
- **來源非文件性質（純行銷頁面、新聞）**：提示使用者此內容可能不適合轉為技能
- **不該做**：不自動部署到 .kiro/skills/，僅產生草稿讓使用者審閱
- **不該做**：不修改已存在的同名技能，若目標路徑已存在則提示使用者

---

## 3. 資源需求

### references/

| 文件 | 涵蓋範圍 |
|------|---------|
| conversion-guide.md | 各來源類型的轉換策略、內容分類規則、SKILL.md 精簡化原則 |
| output-templates.md | SKILL.md / README.md / references 各檔案的產出範本 |

### SKILL.md 預估
- 預估行數：~200 行（核心流程 + 來源類型處理 + 自我檢核清單）
- 是否需要拆分到 references/：是（轉換策略細節和範本拆到 references/）

---

## 4. 測試案例

| # | 提示詞 | 預期輸出 | 驗證方式 |
|---|--------|---------|---------|
| 1 | 「幫我把 https://fastapi.tiangolo.com/ 轉成一個 Kiro Skill」 | 產出 `fastapi/` 目錄，含 SKILL.md（name: fastapi, description 含 FastAPI 關鍵字）、README.md（v0.1.0）、references/（至少含 api-reference.md 和 usage-guide.md） | SKILL.md < 500 行、description ≤ 1024 字元、name 為 kebab-case、README.md 含版本表格 |
| 2 | 「從 langchain-ai/langchain 這個 GitHub repo 建立技能」 | 產出 `langchain/` 目錄，SKILL.md 包含 LangChain 核心概念（chains、agents、retrievers），references/ 含從 README 和 docs 提取的內容 | SKILL.md 有 YAML frontmatter、references/ 檔案都在 SKILL.md 中被引用 |
| 3 | 「把 docs/fish-game-sea-king-spec.md 這個本地檔案轉成技能」 | 產出 `fish-game-sea-king/` 目錄，SKILL.md 聚焦捕魚機規格知識，references/ 含詳細規格表 | 產出結構完整、內容來自本地檔案而非網路 |
| 4 | 「把這個空白頁面轉成技能：https://example.com/404」 | 不產出技能，回報來源無法存取或內容不足的錯誤訊息 | 不產生不完整的技能目錄，有明確的錯誤提示 |
| 5 | 「從 https://docs.python.org/3/ 建立 Python 技能」（大型文件） | 產出 `python/` 目錄，SKILL.md 精簡聚焦核心概念，大量內容拆到 references/（多個分類檔案） | SKILL.md < 500 行、references/ 有合理的分類、告知使用者已做內容取捨 |

---

## 5. 備註

### 與 Skill Seekers 的差異

| 面向 | Skill Seekers | skill-seeker（本技能） |
|------|--------------|-------------------------------|
| 定位 | 獨立 CLI 工具 + MCP Server | Kiro Skill（AI 指令驅動） |
| 來源支援 | 17 種（含影片、Confluence、Notion 等） | 4 種核心（URL、GitHub、本地檔案、本地目錄） |
| 輸出目標 | 12 個 LLM 平台 + RAG 框架 | 僅 Kiro Skill 格式 |
| 內容處理 | Python 爬蟲 + AST 解析 + AI 增強 | AI 直接分析與結構化（無獨立爬蟲） |
| 安裝需求 | `pip install skill-seekers` | 無額外安裝，純 Kiro Skill 指令 |

### 設計決策

1. **不做獨立爬蟲**：利用 Kiro 平台已有的 web fetch / readFile 工具，不重複造輪子
2. **聚焦 Kiro Skill 格式**：不支援多平台輸出，專注做好一件事
3. **草稿模式**：產出後不自動部署，讓使用者有機會審閱和調整
4. **漸進式支援**：v0.1 先支援 URL 和本地檔案，後續可擴展 GitHub 深度分析和 PDF

### 可借鏡 Skill Seekers 的具體機制

1. **內容分類策略**：Skill Seekers 使用 JSON config 的 `categories` 欄位定義分類關鍵字，可參考其分類邏輯
2. **llms.txt 偵測**：優先檢查目標網站是否有 `llms.txt`（LLM-ready 文件），有的話直接使用
3. **Enhancement Workflow**：Skill Seekers 的 AI 增強流程（清理 → 補充範例 → 產生導覽）可作為 Phase 3 的參考
4. **衝突偵測**：多來源合併時的衝突偵測機制，未來擴展多來源支援時可參考

### 後續擴展方向

- 支援 PDF 來源（需要 OCR 或文字提取）
- 支援 GitHub 深度分析（AST 解析、API 提取）
- 支援多來源合併（文件 + GitHub 合為一個技能）
- 與 `skill-creator` 整合：產出草稿後自動進入 skill-creator 的驗證流程
