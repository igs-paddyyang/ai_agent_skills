---
name: skill-seeker
description: "讀取文件來源（文件網站 URL、GitHub repository、本地 Markdown/PDF 檔案）並自動轉換為完整的 Kiro Skill 草稿，產出 SKILL.md、README.md 與 references/ 結構。當使用者提到從文件建立技能、文件轉 Skill、doc to skill、自動產生技能、匯入文件為技能、將文件轉換為技能、documentation to skill、從 URL 建立技能、從 GitHub 建立技能、convert docs to skill、文件轉技能時，請務必使用此技能。"
---

# 技能探索器（Skill Seeker）

將任意文件來源自動轉換為符合 Kiro Skill 規範的技能草稿。省去手動整理文件、拆分結構的繁瑣工作，
讓你從一個 URL 或本地檔案出發，幾分鐘內得到可用的技能骨架。

## 使用時機

- 使用者提供一個文件 URL，想快速建立對應的技能
- 使用者指向一個 GitHub repo，想把它的知識轉為技能
- 使用者有本地的 Markdown / PDF / HTML 檔案，想轉為技能
- 使用者想批次處理一個目錄下的多個文件檔案

## 輸入

接受以下內容（至少提供第 1 項）：

| 輸入 | 必要 | 說明 |
|------|------|------|
| 文件來源 | 是 | URL / GitHub repo / 本地檔案 / 本地目錄 |
| 技能名稱 | 否 | kebab-case，未提供則從來源自動推導 |
| 技能描述提示 | 否 | 使用者對技能用途的補充說明 |
| 輸出路徑 | 否 | 預設為 `.kiro/skills/<skill-name>/` |

## 工作流程

### Phase 1：來源擷取（Ingest）

判斷來源類型並擷取內容：

| 來源類型 | 判斷方式 | 擷取方法 |
|---------|---------|---------|
| URL | 以 `http://` 或 `https://` 開頭 | web fetch 抓取頁面，內容不足時用 rendered 模式重試 |
| GitHub | 含 `github.com/` 或 `owner/repo` 格式 | 抓取 README.md + 選擇性抓取 docs/ 子頁面 |
| 本地檔案 | 檔案路徑（`.md` `.pdf` `.txt` `.html`） | 直接讀取檔案內容 |
| 本地目錄 | 目錄路徑 | 掃描並讀取所有 `.md` / `.txt` / `.html` 檔案 |

URL 來源的額外步驟：
1. 先檢查是否有 `llms.txt`（在根路徑嘗試 `<domain>/llms.txt`），有的話優先使用
2. 若主頁面內容不足（< 500 字），嘗試抓取 2-3 個關鍵子頁面

GitHub 來源的額外步驟：
1. 擷取 repo 描述、主要語言、目錄結構
2. 優先抓取 README.md（raw 格式）
3. 若有 docs/ 目錄，選擇性抓取關鍵文件

### Phase 2：內容分析與結構化（Structure）

分析擷取的原始內容，將其分類到以下區塊：

| 內容類型 | 識別關鍵字 | 對應產出 |
|---------|-----------|---------|
| 概述/簡介 | introduction, overview, about, 簡介 | SKILL.md 核心指令 |
| API 參考 | api, reference, endpoint, method, function | references/api-reference.md |
| 使用指南 | guide, tutorial, how-to, usage, 使用 | references/usage-guide.md |
| 設定/安裝 | install, setup, configuration, getting started | references/setup-guide.md |
| 範例 | example, sample, demo, cookbook | references/examples.md |
| 其他專題 | 無法歸類的重要內容 | references/<topic>.md |

結構化決策：
- 若所有內容合計 < 500 行 → 全部放 SKILL.md，不建立 references/
- 若合計 > 500 行 → 精簡版放 SKILL.md（核心概念 + 資源索引），詳細內容拆到 references/
- 每個 references/ 檔案保持聚焦，單檔不超過 300 行

從內容中提取技能元資料：
1. **技能名稱**：從來源標題或 repo 名稱推導（kebab-case，≤ 64 字元）
2. **一句話描述**：概括技能的核心價值
3. **觸發關鍵字**：從內容中提取使用者可能的觸發短語
4. **核心能力清單**：技能能提供的關鍵知識或操作

### Phase 3：技能草稿產生（Generate）

產生完整的 Kiro Skill 目錄結構。產出的每個檔案都遵循本專案的規範。

#### 產生 SKILL.md

```yaml
---
name: <推導或使用者指定的名稱>
description: >
  <從內容自動產生的觸發描述，≤ 1024 字元>
  <包含功能描述 + 觸發情境關鍵字>
---
```

SKILL.md 本體結構：
1. 標題與一句話說明
2. 使用時機（觸發情境列表）
3. 核心知識/能力（從文件精簡提取）
4. 附帶資源索引表（列出 references/ 中的檔案、用途、何時載入）

#### 產生 README.md

使用 `skill-creator/templates/readme.md` 範本格式，填入：
- 版本：0.1.0
- 作者：paddyyang
- 功能說明：從文件來源自動轉換而來
- 使用方式：列出觸發語句範例
- 檔案結構：實際產出的目錄結構
- 變更紀錄：v0.1.0 初始版本（從 <來源> 自動轉換）

#### 產生 references/

根據 Phase 2 的分類結果，為每個有實質內容的類別產生對應檔案。
每個檔案開頭包含一行說明其涵蓋範圍和來源。

### Phase 4：自我檢核

產出完成後，逐項檢查：

- [ ] SKILL.md 行數 < 500
- [ ] description ≤ 1024 字元
- [ ] name 為 kebab-case，≤ 64 字元
- [ ] README.md 包含版本資訊表格、功能說明、使用方式、檔案結構、變更紀錄
- [ ] 所有 references/ 檔案都在 SKILL.md 的資源索引表中被引用
- [ ] 不包含硬編碼的密碼或 API Key

若有項目未通過，自動修正後再次檢查。

## 邊界案例處理

| 情境 | 處理方式 |
|------|---------|
| 來源內容 < 100 字 | 提示使用者內容不足，建議補充來源或提供更多頁面 |
| 來源內容 > 50KB | 聚焦最重要的部分，告知使用者已做取捨 |
| URL 無法存取（404、需登入） | 回報錯誤，建議提供本地檔案或檢查 URL |
| 來源非文件性質 | 提示此內容可能不適合轉為技能 |
| 目標路徑已存在同名技能 | 提示使用者，不覆蓋現有技能 |

## 產出後的下一步

產出草稿後，向使用者說明：
1. 草稿已建立在 `<輸出路徑>`，請審閱並調整
2. 可使用 `skill-creator` 進一步迭代改進
3. 可執行 `quick_validate.py` 驗證結構合規性

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/conversion-guide.md | 各來源類型的詳細轉換策略與內容分類規則 | Phase 2 分析內容時參考 |
| references/output-templates.md | SKILL.md / README.md 的產出範本與範例 | Phase 3 產生檔案時參考 |
