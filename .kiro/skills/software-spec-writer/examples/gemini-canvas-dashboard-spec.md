# 🚀 Gemini Canvas 通用儀表板 (v1.0)

**目標：** 提供通用型 Gemini Canvas 儀表板技能，接受任意結構化 JSON 資料，透過 Gemini API 自動推斷最佳視覺化方式，產出包含 Tailwind CSS + Chart.js 的獨立 HTML 儀表板，可整合至 TigerBot 對話觸發或 CLI 獨立執行。

**作者**: paddyyang
**日期**: 2026-03-18
**版本**: v1.0

---

## 📝 與原始設計文件的差異

### gemini_canvas_v1.0.md（原始構想） vs 實際實作

| 項目 | 原始構想 | 實際實作 | 原因 |
|:---|:---|:---|:---|
| 後端框架 | FastAPI 獨立伺服器 + `/api/data` 端點 | 無獨立伺服器，`canvas_skill.py` 直接讀取 JSON 檔案 | 簡化架構：不需要額外啟動 API 伺服器 |
| 數據獲取 | 前端 `fetch('/api/data')` 即時取得 | 資料直接嵌入 HTML（`const` 變數） | 離線可用：HTML 單檔可直接開啟 |
| Canvas 環境 | Antigravity Canvas 即時編輯 | 無 Antigravity 依賴，Gemini 一次產出完整 HTML | Antigravity 非必要，Gemini 直接產出即可 |
| E2E 測試 | Playwright 自動化測試 | 無自動化測試，人工驗證 | 專案尚未設定測試框架 |
| Mock 模式 | `?mock=true` 隨機數據 | 無 mock 模式 | 通用型技能不需要 mock，直接餵不同 JSON |
| 數據驗證 | Pydantic schema 驗證 | 無 schema 驗證，Gemini 自動推斷 | 通用型設計：接受任意 JSON 結構 |
| 整合方式 | 獨立 FastAPI 服務 | 整合至 TigerBot（DASHBOARD 意圖 + `/canvas` 端點） | 統一入口，不需額外服務 |

---

## ═══ Part I：規格設計 ═══

## 📋 1. 需求分析

### 1.1 核心功能需求

1. **通用 JSON 視覺化** — 接受任意結構化 JSON，自動推斷最佳圖表類型（KPI 卡片、折線圖、甜甜圈圖、長條圖、表格）
2. **Gemini API 產出 HTML** — 透過精心設計的 prompt template，呼叫 Gemini 2.5 Flash 產出專業級單檔 HTML
3. **離線可用** — 產出的 HTML 內嵌所有資料，含 CSS fallback，可直接用瀏覽器開啟（file://）
4. **CLI 獨立執行** — 提供 `generate_canvas.py` 腳本，支援 `--input`、`--output`、`--title` 參數
5. **TigerBot 整合** — DASHBOARD 意圖觸發，對話中說「產生儀表板」或「canvas」自動產出
6. **Web 端點** — `/canvas?file=xxx` 端點供瀏覽器開啟產出的 HTML
7. **HTML 提取容錯** — 從 Gemini 回應中正確提取 HTML，處理 markdown 包裝（```html）、截斷等異常
8. **設計系統一致性** — 統一配色（Primary #2563eb、Success #10b981、Warning #f59e0b、Danger #ef4444）、Glass-morphism 卡片、Inter 字型
9. **摘要回饋** — 產出後回傳結構化摘要（KPI 數量、趨勢筆數、分類項數、表格筆數）

### 1.2 Skill 編排需求

本技能為單一 Skill，不涉及多 Skill 串接。但作為「被編排」的角色，可被其他 Skill 呼叫：

| 呼叫方 | 使用方式 | 說明 |
|:---|:---|:---|
| `game-analysis-dashboard`（開發階段） | 呼叫 Gemini 產出 HTML 草稿 | 複用 prompt_template.txt + extract_html() |
| TigerBot `arkbot_core.py` | `canvas_skill.generate_canvas_dashboard()` | DASHBOARD 意圖觸發 |
| CLI 使用者 | `py scripts/generate_canvas.py --input data.json` | 獨立執行 |

### 1.3 技術約束與驗證指標

| 模組 | 前置需求 | 獨立性 | 驗證指標 |
|:---|:---|:---|:---|
| JSON 讀取 | JSON 檔案存在 | 高 | 給予有效 JSON 路徑，成功載入並解析 |
| Prompt 組裝 | prompt_template.txt 存在 | 高 | 模板中 `{title}` 和 `{data}` 被正確替換 |
| Gemini API 呼叫 | GOOGLE_API_KEY 設定於 .env | 中 | API 回傳非空文字，含 HTML 內容 |
| HTML 提取 | Gemini 回應含 HTML | 中 | extract_html() 回傳以 `<!DOCTYPE html>` 開頭、`</html>` 結尾的完整 HTML |
| 檔案寫入 | data/canvas/ 目錄可寫 | 高 | HTML 檔案成功寫入，UTF-8 編碼 |
| 摘要產生 | JSON 含標準欄位 | 高 | 摘要含 KPI/趨勢/分類/表格的數量統計 |
| TigerBot 意圖 | intent_router.py | 中 | 輸入「產生儀表板」分類為 DASHBOARD |
| Web 端點 | web_server.py | 低 | GET `/canvas?file=xxx` 回傳 200 + HTML |

### 1.4 測試支援要求

- CLI 腳本可獨立執行（`py scripts/generate_canvas.py --input data.json`）
- 支援 `--input`（必填）、`--output`（選填）、`--title`（選填）參數
- 錯誤時印出明確訊息（缺少 API Key、JSON 格式錯誤、Gemini 回應為空）

---

## 🏗️ 2. 系統設計

### 2.1 架構設計

```
┌──────────────────────────────────────────────────────────────────┐
│                    Gemini Canvas 儀表板流程                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  輸入                                                             │
│  ┌─────────────┐                                                 │
│  │  data.json   │  任意結構化 JSON                                │
│  └──────┬──────┘                                                 │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  canvas_skill.py                                         │     │
│  │                                                          │     │
│  │  1. 讀取 JSON 資料                                       │     │
│  │  2. 載入 prompt_template.txt                             │     │
│  │  3. 組裝 prompt（替換 {title} + {data}）                 │     │
│  │  4. 呼叫 Gemini 2.5 Flash API                           │     │
│  │  5. extract_html() 提取 HTML                             │     │
│  │  6. 寫入 data/canvas/canvas_{timestamp}.html             │     │
│  │  7. 產生摘要文字                                         │     │
│  └──────┬──────────────────────────────────────────────────┘     │
│         │                                                         │
│         ▼                                                         │
│  輸出                                                             │
│  ┌─────────────┐  ┌──────────────────────┐                      │
│  │  摘要文字    │  │  canvas_{ts}.html     │                      │
│  └─────────────┘  └──────────────────────┘                      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

#### TigerBot 整合路徑

```
使用者輸入「產生儀表板」
        │
        ▼
intent_router.py → DASHBOARD 意圖
        │
        ▼
arkbot_core.py → canvas_skill.generate_canvas_dashboard(json_path)
        │
        ▼
canvas_skill.py → Gemini API → HTML
        │
        ▼
web_server.py → /canvas?file=canvas_{ts}.html → 瀏覽器開啟
```

### 2.2 數據結構設計

#### 標準 JSON 契約（建議格式）

```json
{
  "title": "儀表板標題",
  "kpi_cards": [
    { "title": "指標名", "value": "數值", "trend": "+12%", "color": "blue" }
  ],
  "trend_data": [
    { "date": "03-01", "users": 520, "revenue": 8200 }
  ],
  "category_ratio": [
    { "name": "分類名", "value": 45 }
  ],
  "recent_transactions": [
    { "id": "TX001", "user": "User_1", "amount": "$320", "status": "成功" }
  ]
}
```

#### 自動推斷規則

Gemini 會根據 JSON 結構自動選擇視覺化方式：

| JSON 結構特徵 | 推斷為 | 視覺化方式 |
|:---|:---|:---|
| `{ title, value, trend }` 物件陣列 | KPI 指標 | KPI 卡片（4 欄 grid） |
| 含日期/時間 + 數值欄位的陣列 | 時間序列 | 折線圖（Line Chart） |
| `{ name, value }` 物件陣列 | 分類佔比 | 甜甜圈圖（Doughnut Chart） |
| 分類 + 數值的陣列 | 比較資料 | 長條圖（Bar Chart） |
| 多欄位字串 + 數值的陣列 | 明細資料 | 表格（Table） |
| 頂層單一數值 | 關鍵指標 | KPI 卡片 |

#### Prompt Template 設計（prompt_template.txt）

提詞模板包含四大區塊：

| 區塊 | 內容 | 目的 |
|:---|:---|:---|
| TECHNICAL STACK | Inter 字型、Tailwind CSS CDN、Chart.js 4.x CDN | 確保技術棧一致 |
| DESIGN SYSTEM | 配色、Glass-morphism 卡片、動畫、CSS fallback | 確保視覺品質 |
| LAYOUT RULES | KPI grid、圖表容器、表格樣式、Footer | 確保版面結構 |
| CRITICAL REQUIREMENTS | 單檔 HTML、內嵌資料、繁體中文、離線支援 | 確保產出品質 |

關鍵約束：
- 資料必須內嵌為 `const` 變數，禁止 `fetch()` 外部 API
- 禁止 `document.write()`，使用 DOM 操作
- 必須含 CSS fallback（支援 file:// 離線開啟）
- Chart.js 不可用時顯示 graceful fallback 訊息
- 所有 UI 文字使用繁體中文

### 2.3 目錄結構

```
.kiro/skills/gemini-canvas-dashboard/      # Kiro Skill 定義
├── SKILL.md                                # 技能描述與觸發詞
├── assets/
│   └── prompt_template.txt                 # Gemini 提詞模板（核心資產）
├── scripts/
│   └── generate_canvas.py                  # CLI 產生腳本
└── references/
    └── canvas_data_contract.md             # 通用數據契約文件

tigerbot/src/                               # TigerBot 整合
├── canvas_skill.py                         # 核心技能模組（generate_canvas_dashboard）
├── intent_router.py                        # DASHBOARD 意圖關鍵字
├── arkbot_core.py                          # DASHBOARD 分支
└── web_server.py                           # /canvas 端點

tigerbot/data/canvas/                       # 產出目錄
└── canvas_{timestamp}.html                 # 產出的 HTML 儀表板

docs/gemini-canvas/                         # 設計文件
├── gemini_canvas_v1.0.md                   # 原始設計文件
├── gemini-canvas-dashboard-spec.md         # 本規格文件
├── data.json                               # 範例 JSON 資料
└── visual_design.txt                       # 視覺設計規範（早期版本）
```

---

## 🛠️ 3. 實作路徑

### Phase 1: 核心技能模組（canvas_skill.py）

**交付物**: `tigerbot/src/canvas_skill.py` 可被呼叫，產出 HTML
**前置**: 無

**實作步驟**:
1. 建立 `canvas_skill.py`，實作 `load_prompt_template()` — 讀取 `assets/prompt_template.txt`
2. 實作 `extract_html()` — 從 Gemini 回應提取完整 HTML（處理 ```html 包裝、截斷）
3. 實作 `generate_canvas_dashboard(json_path, title)` — 主函式：
   - 讀取 JSON → 載入 prompt → 替換 `{title}` + `{data}` → 呼叫 Gemini API → extract_html → 寫入檔案
4. 產出摘要文字（KPI/趨勢/分類/表格數量統計）
5. 輸出路徑：`tigerbot/data/canvas/canvas_{timestamp}.html`

**驗證**:
```python
from tigerbot.src.canvas_skill import generate_canvas_dashboard
summary, html_path = generate_canvas_dashboard("docs/gemini-canvas/data.json", "測試儀表板")
# 預期：html_path 指向 data/canvas/ 下的 HTML 檔案，摘要含 KPI/趨勢/分類/表格數量
```

---

### Phase 2: Prompt Template 設計（prompt_template.txt）

**交付物**: `.kiro/skills/gemini-canvas-dashboard/assets/prompt_template.txt`
**前置**: Phase 1（需要核心模組來測試 prompt 效果）

**實作步驟**:
1. 定義 Role（資深前端與數據可視化專家）
2. 定義 TECHNICAL STACK（Inter 字型、Tailwind CSS CDN、Chart.js 4.x CDN）
3. 定義 DESIGN SYSTEM（配色、Glass-morphism 卡片、動畫、CSS fallback）
4. 定義 LAYOUT RULES（KPI grid、圖表容器、表格樣式、Footer）
5. 定義 DATA ANALYSIS INSTRUCTIONS（自動推斷視覺化方式）
6. 定義 CRITICAL REQUIREMENTS（單檔 HTML、內嵌資料、繁體中文、離線支援）
7. 預留 `{title}` 和 `{data}` 佔位符

**驗證**:
- 用 `docs/gemini-canvas/data.json` 測試，產出 HTML 含 4 個 KPI 卡片 + 折線圖 + 甜甜圈圖 + 表格
- HTML 以 `<!DOCTYPE html>` 開頭、`</html>` 結尾
- 離線開啟（file://）版面正常

---

### Phase 3: TigerBot 整合

**交付物**: 對話說「產生儀表板」可觸發，`/canvas` 端點可瀏覽
**前置**: Phase 1 + Phase 2

**修改檔案清單**:

| 檔案 | 修改內容 |
|:---|:---|
| `tigerbot/src/intent_router.py` | DASHBOARD 意圖關鍵字（canvas、儀表板、dashboard） |
| `tigerbot/src/arkbot_core.py` | DASHBOARD 分支呼叫 `canvas_skill.generate_canvas_dashboard()` |
| `tigerbot/src/web_server.py` | `/canvas?file=xxx` GET 端點 + WebSocket `canvas_` 路由 |

**實作步驟**:
1. `intent_router.py` — 新增 DASHBOARD 關鍵字（canvas、儀表板、產生儀表板、generate dashboard）
2. `arkbot_core.py` — DASHBOARD 分支：取得 JSON 路徑 → 呼叫 canvas_skill → yield 摘要 + HTML 路徑
3. `web_server.py` — `/canvas?file=xxx` 端點讀取 `data/canvas/` 下的 HTML 檔案
4. `web_server.py` — WebSocket 路由判斷 `canvas_` 前綴，組裝 dashboard_url

**驗證**:
- TigerBot 對話輸入「產生儀表板」→ 回傳摘要 + 儀表板連結
- 瀏覽器開啟 `http://localhost:3000/canvas?file=canvas_xxx.html` → 顯示 HTML
- 輸入「昨日營收」→ 仍走 REVENUE 路徑（不被 DASHBOARD 攔截）

---

### Phase 4: CLI 腳本與文件收尾

**交付物**: `scripts/generate_canvas.py` CLI 工具、SKILL.md 完善
**前置**: Phase 3

**實作步驟**:
1. 建立 `scripts/generate_canvas.py`，支援 `--input`、`--output`、`--title` 參數
2. 確認 SKILL.md 內容與實際實作一致
3. 確認 `references/canvas_data_contract.md` 與 JSON 契約一致
4. 驗證所有端點與意圖路由正常運作

---

## ✅ 4. 驗證與測試指南

### 4.1 功能性測試

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| 標準 JSON 產出 | `py scripts/generate_canvas.py --input docs/gemini-canvas/data.json` | 產出 HTML 至 `data/canvas/`，含 KPI + 圖表 + 表格 |
| 指定標題 | `py scripts/generate_canvas.py --input data.json --title "銷售分析"` | HTML 標題為「銷售分析」 |
| 指定輸出路徑 | `py scripts/generate_canvas.py --input data.json --output ./test.html` | HTML 寫入 `./test.html` |
| 自訂 JSON 結構 | 餵入非標準格式 JSON | Gemini 自動推斷視覺化方式，產出合理 HTML |
| 缺少 API Key | 移除 GOOGLE_API_KEY | 拋出 RuntimeError("找不到 GOOGLE_API_KEY") |
| JSON 不存在 | 指定不存在的路徑 | 拋出 FileNotFoundError |
| Gemini 回應為空 | API 回傳空文字 | 拋出 RuntimeError("Gemini API 回應為空") |

### 4.2 格式與相容性測試

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| HTML 完整性 | 檢查產出 HTML | 以 `<!DOCTYPE html>` 開頭，以 `</html>` 結尾 |
| 離線開啟 | 用瀏覽器直接開啟 HTML（file://） | CSS fallback 生效，版面不崩壞 |
| 中文顯示 | 檢查 HTML 內容 | UI 文字為繁體中文，UTF-8 編碼 |
| Chart.js 不可用 | 斷網開啟 HTML | 圖表區域顯示 fallback 訊息，不白屏 |
| extract_html 容錯 | Gemini 回應含 ```html 包裝 | 正確提取純 HTML，無 markdown 殘留 |

### 4.3 整合測試

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| 意圖 — 產生儀表板 | TigerBot 輸入「產生儀表板」 | intent = DASHBOARD |
| 意圖 — canvas | TigerBot 輸入「canvas」 | intent = DASHBOARD |
| 意圖 — 營收不被攔截 | TigerBot 輸入「昨日營收」 | intent = REVENUE |
| 意圖 — 遊戲不被攔截 | TigerBot 輸入「遊戲分析」 | intent = GAME_ANALYSIS |
| Web 端點 | GET `/canvas?file=canvas_test.html` | 回傳 HTML，200 OK |
| Web 端點無檔案 | GET `/canvas?file=not_exist.html` | 回傳 404 |
| WebSocket 路由 | 對話觸發 DASHBOARD | dashboard_url 為 `/canvas?file=xxx` |
| 既有功能不受影響 | 輸入「昨日營收」 | 營收儀表板正常產出 |

### 4.4 Skill 編排驗證

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| prompt_template 載入 | 檢查 load_prompt_template() | 回傳非空字串，含 `{title}` 和 `{data}` 佔位符 |
| prompt 組裝 | 替換 {title} + {data} | 產出的 prompt 含實際標題和 JSON 資料 |
| Gemini API 呼叫 | 檢查 model 參數 | 使用 `gemini-2.5-flash` |
| 摘要格式 | 檢查回傳 summary | 含 📊 標題 + KPI/趨勢/分類/表格數量 |

---

## 🐛 5. 已知問題與修正紀錄

| # | 問題 | 狀態 | 修正方式 |
|---|---|---|---|
| 1 | Gemini 回應含 ```html markdown 包裝 | ✅ 已修正 | `extract_html()` 先清理 ```html 標記，再用 regex 提取 `<!DOCTYPE html>...</html>` |
| 2 | Gemini 偶爾截斷 HTML（token 限制） | ⏳ 待觀察 | 目前 prompt 未限制 HTML 行數；game-analysis-dashboard 已加入完整性檢查 + retry，canvas_skill 尚未加入 |
| 3 | CDN 離線時圖表不顯示 | ✅ 已處理 | prompt_template 要求 Chart.js 不可用時顯示 fallback 訊息；CSS fallback 規則確保版面不崩壞 |
| 4 | 原始設計文件提及 Antigravity / Playwright 但未實作 | ✅ 已記錄 | 實際架構簡化為 canvas_skill.py 直接呼叫 Gemini，不需要 Antigravity 環境或 Playwright 測試 |
| 5 | 產出 HTML 品質因 Gemini 每次回應不同而有差異 | ⏳ 已知限制 | 通用型技能接受此特性；若需穩定版面，參考 game-analysis-dashboard 的固定樣板策略 |

---

## 📎 附錄

### A. 與其他儀表板技能的比較

| 項目 | gemini-canvas-dashboard（本技能） | market-revenue-dashboard | game-analysis-dashboard |
|:---|:---|:---|:---|
| 定位 | 通用型，接受任意 JSON | 專用營收報表 | 專用遊戲分析 |
| 資料來源 | 任意 JSON 檔案 | SQL Server GameConsume | SQL Server SessionBetWinLog |
| HTML 產出 | 每次呼叫 Gemini API 動態產出 | 固定 Python 模板 | 固定 HTML 樣板 + JSON 注入 |
| Gemini 依賴 | 執行時需要（每次呼叫） | 不需要 | 僅開發階段需要 |
| 品質穩定性 | 每次略有差異（Gemini 特性） | 完全一致 | 完全一致（固定樣板） |
| 適用場景 | 探索性分析、一次性報表、快速原型 | 每日營收追蹤 | 每日遊戲行為追蹤 |

### B. Prompt Template 維護指南

prompt_template.txt 是本技能的核心資產，修改時注意：

1. `{title}` 和 `{data}` 佔位符不可移除或改名
2. DESIGN SYSTEM 區塊定義了統一視覺風格，修改配色需同步更新 SKILL.md
3. CSS FALLBACK 區塊確保離線可用，不可移除
4. CRITICAL REQUIREMENTS 區塊的第 1-6 條為硬性約束，不可放寬
5. 新增圖表類型時，在 DATA ANALYSIS INSTRUCTIONS 區塊補充推斷規則

### C. extract_html() 處理邏輯

```python
def extract_html(text: str) -> str:
    """從 Gemini 回應中提取 HTML"""
    # Step 1: 清理 markdown 包裝
    cleaned = text.strip()
    cleaned = re.sub(r'^```html\s*\n?', '', cleaned)
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    # Step 2: 嘗試找完整 <!DOCTYPE html>...</html>
    match = re.search(r'(<!DOCTYPE html>.*</html>)', cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Step 3: 退而求其次找 <html>...</html>
    match = re.search(r'(<html.*</html>)', cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Step 4: 都找不到，回傳清理後的全文
    return cleaned.strip()
```

處理順序：markdown 清理 → DOCTYPE 匹配 → html 標籤匹配 → 全文回傳

---

## ═══ Part II：執行計畫 ═══

## 📊 6. 任務分解與時間估算

### Task 6.1: 核心技能模組實作

**對應 Phase**: Phase 1
**預估時間**: 15 min
**前置任務**: —

**執行步驟**:
1. 建立 `tigerbot/src/canvas_skill.py`
2. 實作 `load_prompt_template()` — 讀取 prompt_template.txt
3. 實作 `extract_html()` — 從 Gemini 回應提取 HTML
4. 實作 `generate_canvas_dashboard(json_path, title)` — 主函式
5. 測試：用 `docs/gemini-canvas/data.json` 呼叫，確認產出 HTML

**交付物**: `tigerbot/src/canvas_skill.py`

---

### Task 6.2: Prompt Template 設計與調校

**對應 Phase**: Phase 2
**預估時間**: 20 min
**前置任務**: Task 6.1

**執行步驟**:
1. 撰寫 prompt_template.txt 四大區塊（STACK / DESIGN / LAYOUT / REQUIREMENTS）
2. 定義 DATA ANALYSIS INSTRUCTIONS（自動推斷規則）
3. 用標準 JSON（data.json）測試產出品質
4. 調校 prompt 直到產出 HTML 品質穩定
5. 確認離線開啟正常（CSS fallback）

**交付物**: `.kiro/skills/gemini-canvas-dashboard/assets/prompt_template.txt`

---

### Task 6.3: TigerBot 整合

**對應 Phase**: Phase 3
**預估時間**: 10 min
**前置任務**: Task 6.2

**執行步驟**:
1. `intent_router.py` — 新增 DASHBOARD 關鍵字
2. `arkbot_core.py` — 新增 DASHBOARD 分支
3. `web_server.py` — 新增 `/canvas` 端點 + WebSocket 路由
4. 重啟 TigerBot 驗證

**交付物**: TigerBot 可對話觸發 Canvas 儀表板 + 網頁瀏覽

---

### Task 6.4: CLI 腳本與文件

**對應 Phase**: Phase 4
**預估時間**: 10 min
**前置任務**: Task 6.3

**執行步驟**:
1. 建立 `scripts/generate_canvas.py`（argparse: --input, --output, --title）
2. 確認 SKILL.md 與實際實作一致
3. 確認 canvas_data_contract.md 與 JSON 契約一致

**交付物**: CLI 工具 + 文件同步

---

### Task 6.5: 端對端整合測試

**對應 Phase**: Phase 3 + 4
**預估時間**: 10 min
**前置任務**: Task 6.4

**執行步驟**:
1. CLI 測試（標準 JSON / 指定標題 / 指定輸出）
2. Web 端點測試（GET `/canvas?file=xxx`、無檔案 404）
3. 意圖路由測試（DASHBOARD / REVENUE / GAME_ANALYSIS 不互相攔截）
4. 既有功能回歸測試

**交付物**: 測試結果記錄

---

### 6.6 時間總表

| Task | 工項 | 預估時間 | 前置任務 | 狀態 |
|:---|:---|:---|:---|:---|
| 6.1 | 核心技能模組實作 | 15 min | — | ✅ 已完成 |
| 6.2 | Prompt Template 設計與調校 | 20 min | 6.1 | ✅ 已完成 |
| 6.3 | TigerBot 整合 | 10 min | 6.2 | ✅ 已完成 |
| 6.4 | CLI 腳本與文件 | 10 min | 6.3 | ✅ 已完成 |
| 6.5 | 端對端整合測試 | 10 min | 6.4 | ⏳ 待人工測試 |
| **合計** | | **~65 min** | | |

> 所有開發工項（6.1-6.4）已完成，canvas_skill.py 與 TigerBot 整合已上線。Task 6.5 待人工驗證。

---

## ☑️ 7. 執行 Checklist

### Checklist: Task 6.1 — 核心技能模組

- [x] `canvas_skill.py` 建立完成
- [x] `load_prompt_template()` 正確讀取 prompt_template.txt
- [x] `extract_html()` 處理 ```html 包裝
- [x] `extract_html()` 提取 `<!DOCTYPE html>...</html>`
- [x] `generate_canvas_dashboard()` 呼叫 Gemini API 成功
- [x] 產出 HTML 寫入 `data/canvas/` 目錄
- [x] 摘要文字含 KPI/趨勢/分類/表格數量

**實際執行結果**:
> canvas_skill.py 已實作完成，使用 google-genai SDK 呼叫 Gemini 2.5 Flash。

---

### Checklist: Task 6.2 — Prompt Template

- [x] prompt_template.txt 含 TECHNICAL STACK 區塊（Inter + Tailwind + Chart.js）
- [x] prompt_template.txt 含 DESIGN SYSTEM 區塊（配色 + Glass-morphism + 動畫）
- [x] prompt_template.txt 含 CSS FALLBACK 區塊（file:// 離線支援）
- [x] prompt_template.txt 含 LAYOUT RULES 區塊（KPI grid + 圖表 + 表格）
- [x] prompt_template.txt 含 DATA ANALYSIS INSTRUCTIONS（自動推斷規則）
- [x] prompt_template.txt 含 CRITICAL REQUIREMENTS（10 條硬性約束）
- [x] `{title}` 和 `{data}` 佔位符正確
- [x] 產出 HTML 含 KPI 卡片 + 圖表 + 表格
- [x] 離線開啟版面正常

**實際執行結果**:
> prompt_template.txt 已完成，含完整設計系統定義。產出 HTML 品質穩定。

---

### Checklist: Task 6.3 — TigerBot 整合

- [x] `intent_router.py` DASHBOARD 關鍵字正確
- [x] `arkbot_core.py` DASHBOARD 分支呼叫 canvas_skill
- [x] `web_server.py` `/canvas` 端點正確
- [x] `web_server.py` WebSocket `canvas_` 路由正確

**實際執行結果**:
> 三個檔案修改完畢，DASHBOARD 意圖路由正常。

---

### Checklist: Task 6.4 — CLI 腳本與文件

- [x] SKILL.md 觸發詞與 intent_router 一致
- [x] SKILL.md 執行方式與 CLI 參數一致
- [x] SKILL.md 數據契約與實際 JSON 格式一致

**實際執行結果**:
> SKILL.md 已同步，CLI 腳本可獨立執行。

---

### Checklist: Task 6.5 — 端對端整合測試

- [ ] CLI `--input data.json` 產出 HTML ← 待人工驗證
- [ ] CLI `--title "自訂標題"` 標題正確 ← 待人工驗證
- [ ] GET `/canvas?file=canvas_test.html` → 200 OK ← 待人工驗證
- [ ] GET `/canvas?file=not_exist.html` → 404 ← 待人工驗證
- [ ] 對話「產生儀表板」→ DASHBOARD 意圖 ← 待人工驗證
- [ ] 對話「昨日營收」→ REVENUE 意圖（不被攔截） ← 待人工驗證
- [ ] 對話「遊戲分析」→ GAME_ANALYSIS 意圖（不被攔截） ← 待人工驗證
- [ ] 營收儀表板正常（`/dashboard`） ← 待人工驗證
- [ ] 遊戲分析儀表板正常（`/game-analysis`） ← 待人工驗證

**實際執行結果**: （待人工測試）

---

## ⚠️ 8. 風險管理與應對

| 風險 | 機率 | 影響 | 狀態 | 應對策略 |
|:---|:---|:---|:---|:---|
| Gemini API 回應截斷（token 限制） | 中 | 高 | ⏳ 待處理 | game-analysis-dashboard 已實作完整性檢查 + retry，可移植至 canvas_skill |
| Gemini API 每次產出品質不一致 | 中 | 中 | ✅ 已接受 | 通用型技能特性；需穩定版面時改用固定樣板策略 |
| GOOGLE_API_KEY 過期或額度用盡 | 低 | 高 | ⬜ 待預防 | 錯誤訊息明確提示；考慮加入 API 呼叫失敗的 retry |
| CDN 離線導致圖表不顯示 | 低 | 中 | ✅ 已處理 | CSS fallback + Chart.js 可用性檢查 + fallback 訊息 |
| prompt_template.txt 被意外修改 | 低 | 高 | ⬜ 待預防 | 納入版本控制，修改前備份 |
| 意圖衝突（DASHBOARD vs GAME_ANALYSIS） | 低 | 中 | ✅ 已處理 | GAME_ANALYSIS 優先順序高於 DASHBOARD |

---

**文件版本**: v1.0
**維護者**: paddyyang
**最後更新**: 2026-03-18
