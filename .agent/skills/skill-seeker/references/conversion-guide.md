# 轉換策略與內容分類指南

> Phase 2（內容分析與結構化）時載入此文件，作為分類與精簡化的參考。

---

## 1. 各來源類型的轉換策略

### 1.1 URL 來源

**擷取策略**：
1. 先嘗試 `<domain>/llms.txt`（LLM-ready 文件），有的話直接使用
2. 抓取主頁面，評估內容量
3. 若主頁面 < 500 字，從導覽列或連結中找到 2-3 個關鍵子頁面
4. 優先抓取：Getting Started、API Reference、Quick Start

**分類策略**：
- 單頁文件 → 直接分析段落結構
- 多頁文件 → 每頁獨立分類，再合併同類內容

**常見問題**：
- SPA 網站可能需要 rendered 模式
- 部分網站有反爬蟲機制，抓取失敗時建議使用者提供本地檔案

### 1.2 GitHub 來源

**擷取策略**：
1. 抓取 README.md（raw 格式：`https://raw.githubusercontent.com/<owner>/<repo>/main/README.md`）
2. 列出目錄結構，識別 docs/ 或 documentation/ 目錄
3. 若有 docs/，選擇性抓取最重要的 3-5 個檔案
4. 擷取 repo 元資料：描述、主要語言、stars、topics

**分類策略**：
- README.md 通常包含概述 + 安裝 + 快速開始 → 拆分到對應類別
- docs/ 下的檔案通常已有明確分類 → 保持原有結構

**技能名稱推導**：
- 優先使用 repo 名稱（已是 kebab-case）
- 若 repo 名稱含底線，轉為連字號
- 若名稱過長（> 64 字元），取核心部分

### 1.3 本地檔案來源

**擷取策略**：
- `.md` → 直接讀取 Markdown 內容
- `.txt` → 讀取純文字，嘗試識別結構（標題、列表）
- `.html` → 讀取 HTML，提取主要內容區塊
- `.pdf` → 提示使用者 PDF 支援有限，建議先轉為 Markdown

**分類策略**：
- 單檔 → 按段落標題分類
- 若檔案已有清楚的章節結構（## 標題），直接對應到 references/ 分類

### 1.4 本地目錄來源

**擷取策略**：
1. 掃描目錄，列出所有 `.md` / `.txt` / `.html` 檔案
2. 排除明顯的非文件檔案（node_modules/、.git/、__pycache__/）
3. 按檔名排序，依序讀取
4. 若檔案數 > 20，提示使用者選擇最重要的檔案

**分類策略**：
- 每個檔案視為一個內容單元
- 從檔名推測類別（如 `api.md` → API 參考、`guide.md` → 使用指南）
- 無法從檔名推測的，分析內容後分類

---

## 2. 內容分類規則

### 2.1 分類關鍵字對照表

| 類別 | 關鍵字（英文） | 關鍵字（中文） |
|------|--------------|--------------|
| 概述 | introduction, overview, about, what is, summary | 簡介, 概述, 關於, 總覽 |
| API 參考 | api, reference, endpoint, method, function, class, module | API, 參考, 端點, 方法 |
| 使用指南 | guide, tutorial, how-to, usage, walkthrough, step-by-step | 指南, 教學, 使用方式, 步驟 |
| 設定/安裝 | install, setup, configuration, getting started, prerequisites | 安裝, 設定, 環境, 前置條件 |
| 範例 | example, sample, demo, cookbook, recipe, snippet | 範例, 示範, 食譜 |
| 架構 | architecture, design, pattern, structure, diagram | 架構, 設計, 模式, 結構 |
| 疑難排解 | troubleshoot, faq, common issues, debug, error | 疑難排解, 常見問題, 除錯 |

### 2.2 分類優先順序

當內容同時匹配多個類別時：
1. 概述 > 其他（概述性內容優先放 SKILL.md）
2. API 參考 > 使用指南（技術細節優先獨立成檔）
3. 範例歸入最相關的類別（如 API 範例歸入 API 參考）

### 2.3 內容精簡化原則

SKILL.md 的核心指令應精簡到讓 AI 能快速理解「這個技能能做什麼」和「怎麼做」：

- 保留：核心概念、關鍵 API、使用模式、決策邏輯
- 移除：冗長的歷史背景、重複的範例、過度詳細的參數說明
- 精簡：將 10 個範例濃縮為 2-3 個最具代表性的
- 引用：詳細內容放 references/，SKILL.md 只放索引

---

## 3. 品質檢查清單

產出前逐項確認：

| 項目 | 標準 |
|------|------|
| SKILL.md 行數 | < 500 行 |
| description 長度 | ≤ 1024 字元 |
| name 格式 | kebab-case，≤ 64 字元 |
| description 內容 | 同時包含功能描述和觸發情境關鍵字 |
| references/ 引用 | 每個檔案都在 SKILL.md 資源索引表中 |
| README.md 格式 | 包含版本表格、功能說明、使用方式、檔案結構、變更紀錄 |
| 無敏感資訊 | 不含硬編碼密碼、API Key、PII |
