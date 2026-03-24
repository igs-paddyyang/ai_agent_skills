# 🚀 遊戲分析儀表板 (v2.0)

**目標：** 編排三個既有 Kiro Skill（sqlserver-data-exporter → gemini-canvas-dashboard → arkbot-generator），從 SQL Server 查詢遊戲押注贏分資料，透過 Gemini Canvas 產出 HTML 儀表板樣板，調整至滿意後固定，ArkBot 僅套用樣板注入即時資料。

**作者**: paddyyang
**日期**: 2026-03-17
**版本**: v2.0

---

## 📝 v2.0 調整說明

### 與 v1.0 的差異

| 項目 | v1.0（舊） | v2.0（新） | 原因 |
|:---|:---|:---|:---|
| HTML 產出方式 | 每次呼叫 Gemini API 動態產出 | 一次性產出樣板，之後套用固定樣板 | 穩定性：Gemini 每次產出品質不一；效能：省去 API 呼叫延遲 |
| 押注量單位 | 原始數值（如 $1,234,567） | 兆為單位（如 1.23T） | 數值過大，兆為單位更易閱讀 |
| Skill 編排流程 | 三段式一次跑完 | 分兩階段：① Skill 產出+調整樣板 ② ArkBot 套用樣板 | 可先調好版面再上線，ArkBot 不依賴 Gemini |
| ArkBot 依賴 | 需要 GOOGLE_API_KEY | 不需要（僅套用本地樣板） | 降低外部依賴，提升穩定性 |
| Phase 2 定位 | 每次執行都呼叫 Gemini | 開發階段用 Gemini 產出樣板，產出後固定 | 樣板是「開發產物」，不是「執行時依賴」 |

### 新架構流程

```
┌─────────────────────────────────────────────────────────────────┐
│  開發階段（一次性）                                              │
│                                                                  │
│  ① Skill 產出 JSON → ② Gemini 產出 HTML 樣板 → ③ 人工調整樣板  │
│                                                                  │
│  產出物：dashboard_template.html（含 {placeholder} 佔位符）      │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 樣板固定後
┌─────────────────────────────────────────────────────────────────┐
│  執行階段（每次觸發）                                            │
│                                                                  │
│  ① SQL Server 查詢 → JSON → ② 套用固定樣板（注入資料）→ HTML   │
│                                                                  │
│  ArkBot 不呼叫 Gemini，僅讀取樣板 + 注入 JSON                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 1. 需求分析

> ═══ Part I：規格設計 ═══

### 1.1 核心功能需求

1. **遊戲押量分析** — 查詢各遊戲的 TotalBet / TotalWin / RTP / 場次數 / 玩家數，區分老虎機與捕魚機
2. **玩家行為分析** — VIP 等級分佈、國家/市場分佈（TW/CN/JP/VN/US/OTHER）
3. **日環比計算** — 與前一天比較，計算押注量、贏分量、玩家數的變化百分比
4. **測試帳號排除** — 從 App_Pig.dbo.GameAccount 取得測試帳號，查詢時排除
5. **遊戲名稱對照** — 從 MobileDW_Pig.dbo.DimScene 取得 GameName / GameName_CHT
6. **數值格式** — 押注量/贏分量以兆（T）為單位顯示（如 1.23T），提升可讀性
7. **JSON 資料產出** — 輸出符合樣板數據契約的結構化 JSON
8. **HTML 樣板產出** — 透過 Gemini API 一次性產出 HTML 樣板，人工調整後固定
9. **HTML 套用產出** — ArkBot 執行時僅套用固定樣板，注入 JSON 資料，不呼叫 Gemini
10. **TigerBot 整合** — 新增 GAME_ANALYSIS 意圖，對話觸發自動產出報告
11. **Web 端點** — 新增 `/game-analysis?date=YYYYMMDD` 端點供瀏覽器開啟

### 1.2 Skill 編排需求

本功能分為「開發階段」與「執行階段」兩個流程：

#### 開發階段（一次性）— 產出並調整 HTML 樣板

| 階段 | 使用 Skill | 輸入 | 輸出 | 說明 |
|:---|:---|:---|:---|:---|
| ① 資料抽取 | `sqlserver-data-exporter` | SQL 查詢 + db.yaml | 結構化 JSON | 查詢遊戲押注/贏分、VIP、國家分佈 |
| ② 樣板產出 | `gemini-canvas-dashboard` | JSON + prompt_template | HTML 樣板草稿 | 呼叫 Gemini API 產出初版 HTML |
| ③ 樣板調整 | 人工 | HTML 草稿 | `dashboard_template.html` | 調整版面、佔位符、數值格式至滿意 |

#### 執行階段（每次觸發）— ArkBot 套用固定樣板

| 階段 | 使用 Skill | 輸入 | 輸出 | 說明 |
|:---|:---|:---|:---|:---|
| ① 資料抽取 | `sqlserver-data-exporter` | SQL 查詢 + db.yaml | 結構化 JSON | 同開發階段 |
| ② 套用樣板 | `game-analysis-dashboard` | JSON + dashboard_template.html | 完成 HTML | 注入 JSON 資料至固定樣板，不呼叫 Gemini |
| ③ 佈署整合 | `arkbot-generator`（模式參考） | HTML + 整合規範 | TigerBot 端點 | 掛載意圖路由 + Web 端點 + WebSocket 路由 |

> **關於樣板策略**：v1.0 每次都呼叫 Gemini API 動態產出 HTML，品質不穩定且有延遲。v2.0 改為先用 Gemini 產出樣板草稿，人工調整至滿意後固定為 `dashboard_template.html`。ArkBot 執行時僅讀取樣板並注入 `/*__DASHBOARD_DATA__*/` 佔位符，完全不依賴 Gemini API。

> **關於第 ③ 階段**：`arkbot-generator` 的定位是「從零產生 TigerBot 專案」，而此處需要的是「把新功能掛進既有 TigerBot」。因此不直接呼叫 arkbot-generator，而是參考其架構模式（三層架構、意圖路由、WebSocket 協議），定義標準化的「TigerBot 整合清單」。

### 1.3 技術約束與驗證指標

| 模組 | 前置需求 | 獨立性 | 驗證指標 |
|:---|:---|:---|:---|
| SQL 查詢（老虎機） | SQL Server 連線、db.yaml | 高 | 給予 ProDate=最新日期，回傳 slot_games 陣列，每筆含 game_id/total_bet/total_win/rtp/sessions/users |
| SQL 查詢（捕魚機） | SQL Server 連線、db.yaml | 高 | 給予 ProDate=最新日期，回傳 fish_games 陣列，結構同上 |
| 測試帳號排除 | App_Pig 連線權限 | 高 | 查詢 App_Pig.dbo.GameAccount 回傳 UserID 清單，查詢結果不含這些 UserID |
| 遊戲名稱對照 | MobileDW_Pig 連線權限 | 高 | 查詢 DimScene 回傳 GameID → GameName/GameName_CHT 對照 dict（支援變體 GameID 回退） |
| VIP 分佈查詢 | SQL Server 連線 | 高 | 回傳各 VipLV 的 users 數與 total_bet |
| 國家分佈查詢 | SQL Server 連線 | 高 | 回傳 TW/CN/JP/VN/US/OTHER 各市場的 users 數與 total_bet |
| 日環比計算 | 前一天資料存在 | 中 | 前日無資料時 trend 顯示 "N/A"，有資料時計算百分比 |
| JSON 組裝 | 以上查詢全部完成 | 低 | 輸出 JSON 含 kpi_cards/slot_games/fish_games/category_ratio/vip_distribution/country_distribution |
| Gemini HTML 產出 | GOOGLE_API_KEY、prompt_template.txt | 中 | 呼叫 Gemini API 回傳非空 HTML，含 `<!DOCTYPE html>` 開頭（僅開發階段） |
| 樣板套用 | dashboard_template.html | 高 | 讀取固定樣板，注入 JSON 資料，產出完整 HTML（執行階段） |
| TigerBot 意圖路由 | intent_router.py | 中 | 輸入「遊戲分析」分類為 GAME_ANALYSIS；輸入「營收」仍為 REVENUE |
| Web 端點 | web_server.py | 低 | GET `/game-analysis?date=20260316` 回傳 200 + HTML 內容 |

### 1.4 測試支援要求

- CLI 腳本可獨立執行（`py scripts/generate_game_dashboard.py`）
- 支援 `--date` 參數指定日期，預設查最新一天
- 錯誤時印出明確錯誤訊息與 traceback

---

## 🏗️ 2. 系統設計

### 2.1 Skill 編排架構

#### 開發階段（一次性：產出並調整樣板）

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     開發階段：樣板產出與調整                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ① sqlserver-data-exporter                                       │    │
│  │                                                                  │    │
│  │  連線模式：讀取 sqlserver/config/db.yaml                        │    │
│  │  驅動：DRIVER={SQL Server}                                      │    │
│  │  查詢策略：同執行階段                                            │    │
│  │                                                                  │    │
│  │  輸出：game_analysis_{YYYYMMDD}.json（樣本資料）                │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ② gemini-canvas-dashboard（一次性）                              │    │
│  │                                                                  │    │
│  │  提詞模板：.kiro/skills/gemini-canvas-dashboard/assets/         │    │
│  │            prompt_template.txt                                   │    │
│  │  API：Gemini 2.0 Flash（google-genai SDK）                      │    │
│  │  策略：用樣本 JSON 產出 HTML 草稿                                │    │
│  │                                                                  │    │
│  │  輸出：HTML 草稿（需人工調整）                                  │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ③ 人工調整樣板                                                   │    │
│  │                                                                  │    │
│  │  調整項目：                                                      │    │
│  │    - 版面佈局、配色、圖表樣式                                   │    │
│  │    - 數值格式（兆為單位）                                       │    │
│  │    - 佔位符：/*__DASHBOARD_DATA__*/ 用於注入 JSON               │    │
│  │    - 確認 Chart.js / CSS 正確                                   │    │
│  │                                                                  │    │
│  │  輸出：dashboard_template.html（固定樣板）                      │    │
│  │  存放：.kiro/skills/game-analysis-dashboard/assets/             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### 執行階段（每次觸發：ArkBot 套用樣板）

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     執行階段：ArkBot 套用固定樣板                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ① sqlserver-data-exporter                                       │    │
│  │                                                                  │    │
│  │  連線模式：讀取 sqlserver/config/db.yaml                        │    │
│  │  驅動：DRIVER={SQL Server}                                      │    │
│  │  查詢策略：                                                      │    │
│  │    App_Pig    → dbo.GameAccount（測試帳號排除）                  │    │
│  │    MobileDW_Pig → dbo.DimScene（遊戲名稱對照）                  │    │
│  │    ExtData_Pig → f_SessionBetWinLog（老虎機）                   │    │
│  │                → f_FishSessionBetWinLog（捕魚機）               │    │
│  │                → VIP 分佈 / 國家分佈 / 前日總計                 │    │
│  │                                                                  │    │
│  │  輸出：game_analysis_{YYYYMMDD}.json                            │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ② 套用固定樣板（不呼叫 Gemini）                                 │    │
│  │                                                                  │    │
│  │  樣板：.kiro/skills/game-analysis-dashboard/assets/             │    │
│  │        dashboard_template.html                                   │    │
│  │  注入方式：                                                      │    │
│  │    template.replace("/*__DASHBOARD_DATA__*/",                   │    │
│  │      f"const DASHBOARD_DATA = {json_str};")                     │    │
│  │  數值格式：押注量/贏分量以兆（T）為單位                         │    │
│  │                                                                  │    │
│  │  輸出：game_analysis_{YYYYMMDD}.html                            │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ ③ arkbot-generator（模式參考，非直接呼叫）                      │    │
│  │                                                                  │    │
│  │  參考架構：三層式（arkbot_core → bot_main / web_server）        │    │
│  │  整合清單：                                                      │    │
│  │    intent_router.py  → +GAME_ANALYSIS 關鍵字 + 意圖判斷        │    │
│  │    arkbot_core.py    → +GAME_ANALYSIS 分支（動態 import 腳本）  │    │
│  │    web_server.py     → +/game-analysis?date= 端點               │    │
│  │                      → WebSocket 路由（game_analysis_ 前綴）    │    │
│  │                                                                  │    │
│  │  輸出：TigerBot 可對話觸發 + 網頁瀏覽                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 TigerBot 整合清單（標準化流程）

> 此清單參考 `arkbot-generator` 架構模式，適用於所有分析類 Skill 掛載 TigerBot。
> 未來新增分析功能時，照此清單修改即可。

#### Step 1: intent_router.py — 新增意圖

```python
# 新增關鍵字清單
GAME_ANALYSIS_KEYWORDS = [
    "遊戲分析", "遊戲行為", "押注分析", "game behavior",
    "遊戲報表", "rtp 分析", "rtp分析", "玩家行為",
    "遊戲儀表板", "老虎機分析", "捕魚機分析",
    "game analysis", "game dashboard", "遊戲押量"
]

# classify_intent() 中新增判斷（優先於 CANVAS）
if any(kw in lower_input for kw in GAME_ANALYSIS_KEYWORDS):
    target_date = extract_date(user_input)
    return {"intent": "GAME_ANALYSIS", "url": None, "date": target_date}

# Gemini 兜底 prompt 中新增意圖描述
# - 提到遊戲分析、遊戲行為、押注分析、RTP → GAME_ANALYSIS
```

意圖優先順序：`GAME_ANALYSIS > CANVAS > REVENUE > RESEARCH > CASUAL`

#### Step 2: arkbot_core.py — 新增處理分支

```python
# 腳本路徑
GAME_ANALYSIS_SCRIPT = os.path.join(
    os.path.dirname(PROJECT_ROOT), ".kiro", "skills",
    "game-analysis-dashboard", "scripts", "generate_game_dashboard.py"
)

# process_message() 中新增分支
elif intent == "GAME_ANALYSIS":
    # 動態 import 腳本，避免啟動時載入
    import importlib.util
    spec = importlib.util.spec_from_file_location(...)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    summary, json_path, html_path = mod.generate_game_analysis_report(target_date=date)
    yield {"type": "dashboard", "content": summary, "html_path": html_path}
```

#### Step 3: web_server.py — 新增端點 + WebSocket 路由

```python
# 新增 GET 端點
@app.get("/game-analysis", response_class=HTMLResponse)
async def game_analysis(date: str = Query(default=None)):
    # 找 tigerbot/data/game_analysis_{date}.html 或最新

# WebSocket 路由判斷
if html_name.startswith("game_analysis_"):
    date_match = re.search(r'(\d{8})', html_name)
    date_param = f"?date={date_match.group(1)}" if date_match else ""
    dashboard_url = f"/game-analysis{date_param}"
```

### 2.3 數據來源設計

#### 來源資料表

| 資料表 | 資料庫 | 筆數 | 用途 | 關鍵欄位 |
|:---|:---|:---|:---|:---|
| `dbo.f_SessionBetWinLog` | ExtData_Pig | 12.8M | 老虎機押注/贏分 | ProDate(int), GameID, UserID, TotalBet, TotalWin, Country, VipLV |
| `dbo.f_FishSessionBetWinLog` | ExtData_Pig | 365M | 捕魚機押注/贏分 | ProDate(int), GameID, UserID, TotalBet, TotalWin, Country, VipLV |
| `dbo.DimScene` | MobileDW_Pig | ~145 | 遊戲名稱對照 | SceneCode(→GameID), SceneName(中文名) |
| `dbo.GameAccount` | App_Pig | 395 | 測試帳號清單 | UserID |

#### SQL 查詢策略

- **日期篩選**：`WHERE ProDate = {date}`，ProDate 為 int 型別（YYYYMMDD）
- **測試帳號排除**：`AND UserID NOT IN (id1, id2, ...)`，從 App_Pig.dbo.GameAccount 取得
- **市場分類**：使用 CASE WHEN 將 Country 歸類為 TW/CN/JP/VN/US/OTHER
- **遊戲名稱**：查詢 DimScene 後在 Python 端 JOIN（避免跨資料庫 JOIN 的效能問題），支援變體 GameID（10xxx/30xxx/50xxx/101xxx）回退到基礎 GameID
- **捕魚機注意**：f_FishSessionBetWinLog 有 365M 筆，查詢務必帶 ProDate 條件

#### 輸出 JSON 結構（數據契約）

```json
{
  "title": "遊戲分析儀表板 (20260316)",
  "report_date": "20260316",
  "generated_at": "2026-03-17 10:30:00",
  "data_source": "ExtData_Pig",
  "kpi_cards": [
    { "title": "總押注量", "value": "1.23T", "trend": "+5.2%", "color": "blue" },
    { "title": "總贏分量", "value": "0.99T", "trend": "-2.1%", "color": "green" },
    { "title": "整體 RTP", "value": "96.5%", "trend": "", "color": "purple" },
    { "title": "老虎機玩家數", "value": "12,345", "trend": "+8.1%", "color": "orange" }
  ],
  "slot_games": [
    {
      "game_id": 101, "game_name": "Fortune Tiger", "game_name_cht": "招財虎",
      "total_bet": 500000.00, "total_win": 475000.00, "rtp": 95.00,
      "sessions": 8500, "users": 2300, "avg_bet_per_session": 58.82
    }
  ],
  "fish_games": [
    {
      "game_id": 201, "game_name": "Ocean King", "game_name_cht": "海洋之王",
      "total_bet": 300000.00, "total_win": 270000.00, "rtp": 90.00,
      "sessions": 5000, "users": 1500, "avg_bet_per_session": 60.00
    }
  ],
  "category_ratio": [
    { "name": "老虎機", "value": 650000.00 },
    { "name": "捕魚機", "value": 350000.00 }
  ],
  "vip_distribution": [
    { "vip_level": 0, "users": 5000, "total_bet": 100000.00 }
  ],
  "country_distribution": [
    { "country": "TW", "users": 4000, "total_bet": 300000.00 }
  ]
}
```

> **數值格式說明**：JSON 中的 `total_bet` / `total_win` 保留原始數值（方便計算），KPI cards 的 `value` 欄位以兆（T）為單位顯示。格式化邏輯在 `build_report_json()` 中處理：`>= 1T` 顯示 `X.XXT`，`>= 1B` 顯示 `X.XXB`，`>= 1M` 顯示 `X.XXM`，否則千分位逗號。

### 2.4 目錄結構

```
.kiro/skills/game-analysis-dashboard/     # Kiro Skill 定義
├── SKILL.md                               # 技能描述與觸發詞
├── assets/
│   └── dashboard_template.html            # 固定 HTML 樣板（含 /*__DASHBOARD_DATA__*/ 佔位符）
├── scripts/
│   └── generate_game_dashboard.py         # 核心產生腳本（單檔可執行）
└── references/
    └── game_data_contract.md              # JSON 數據契約

tigerbot/src/                              # TigerBot 整合（修改既有檔案）
├── intent_router.py                       # +GAME_ANALYSIS 意圖關鍵字
├── arkbot_core.py                         # +GAME_ANALYSIS 分支
└── web_server.py                          # +/game-analysis 端點

tigerbot/data/                             # 輸出目錄
├── game_analysis/
│   ├── game_analysis_{YYYYMMDD}.json      # 結構化分析資料
│   └── game_analysis_{YYYYMMDD}.html      # 套用樣板後的完成 HTML
├── market_revenue/                        # 營收 JSON + HTML 儀表板
└── canvas/                                # Canvas 通用儀表板 HTML

docs/                                      # 規格文件
└── game-analysis-dashboard-spec_v2.0.md   # 本文件
```


---

## 🛠️ 3. 實作路徑

### Phase 1: 資料抽取（使用 sqlserver-data-exporter 模式）

**對應 Skill**: `sqlserver-data-exporter`
**交付物**: `generate_game_dashboard.py` 可獨立執行，產出 JSON

**Skill 使用方式**:
- 複用 `sqlserver-data-exporter` 的連線模式（讀取 `sqlserver/config/db.yaml`、`DRIVER={SQL Server}`）
- 不直接呼叫 `export_data.py`，因為需要多次跨資料庫查詢 + Python 端 JOIN + 自訂聚合邏輯
- 參考其 `get_connection(database)` 函式簽名，在腳本中實作同等功能

**實作步驟**:
1. 建立 `generate_game_dashboard.py`，實作 DB 連線（讀取 db.yaml）
2. 實作 `get_test_accounts()` — 連線 App_Pig 取得測試帳號
3. 實作 `load_game_names()` — 連線 MobileDW_Pig 取得遊戲名稱對照
4. 實作 `query_slot_games()` — 老虎機各遊戲統計（GROUP BY GameID）
5. 實作 `query_fish_games()` — 捕魚機各遊戲統計（GROUP BY GameID）
6. 實作 `query_vip_distribution()` — VIP 分佈（GROUP BY VipLV）
7. 實作 `query_country_distribution()` — 國家分佈（CASE WHEN + GROUP BY）
8. 實作 `query_prev_day_totals()` — 前日總計（日環比用）
9. 實作 `build_report_json()` — 組裝完整 JSON（填入遊戲名稱、計算 KPI）
10. CLI 入口：`--date`、`--output` 參數

**驗證**:
```bash
py .kiro/skills/game-analysis-dashboard/scripts/generate_game_dashboard.py --date 20260316
# 預期：產出 tigerbot/data/game_analysis/game_analysis_20260316.json
# 檢查：JSON 結構完整，含 kpi_cards / slot_games / fish_games / vip / country
```

**注意事項**:
- f_FishSessionBetWinLog 有 365M 筆，務必帶 ProDate 條件
- 遊戲名稱在 Python 端 JOIN，不做跨資料庫 SQL JOIN
- 測試帳號查詢失敗時不中斷，改為不排除（graceful degradation）

---

### Phase 2: 樣板產出與調整（使用 gemini-canvas-dashboard，一次性）

**對應 Skill**: `gemini-canvas-dashboard`
**交付物**: `assets/dashboard_template.html` 固定樣板
**前置**: Phase 1 完成（需要樣本 JSON 資料）

**Skill 使用方式**:
- 複用 `gemini-canvas-dashboard` 的提詞模板（`assets/prompt_template.txt`）
- 複用其 `extract_html()` 函式邏輯（從 Gemini 回應提取 HTML）
- API Key 從 `tigerbot/.env` 的 `GOOGLE_API_KEY` 讀取
- **僅在開發階段呼叫 Gemini**，產出 HTML 草稿後人工調整

**實作步驟**:
1. 用 Phase 1 產出的樣本 JSON，呼叫 Gemini API 產出 HTML 草稿
2. 人工檢視 HTML 草稿，調整版面、配色、圖表樣式
3. 將 JSON 資料區塊替換為佔位符 `/*__DASHBOARD_DATA__*/`
4. 確認數值格式使用兆（T）為單位
5. 確認 Chart.js / CSS 正確，離線可開啟
6. 儲存為 `.kiro/skills/game-analysis-dashboard/assets/dashboard_template.html`

**樣板佔位符規範**:
```html
<script>
/*__DASHBOARD_DATA__*/
// 執行時會被替換為：const DASHBOARD_DATA = { ... };
</script>
```

**樣板調整檢查項目**:
- [ ] HTML 以 `<!DOCTYPE html>` 開頭，以 `</html>` 結尾
- [ ] 含 `/*__DASHBOARD_DATA__*/` 佔位符
- [ ] KPI 卡片讀取 `DASHBOARD_DATA.kpi_cards`
- [ ] 遊戲表格讀取 `DASHBOARD_DATA.slot_games`
- [ ] VIP 分佈圖讀取 `DASHBOARD_DATA.vip_distribution`
- [ ] 國家分佈圖讀取 `DASHBOARD_DATA.country_distribution`
- [ ] 押注量/贏分量以兆（T）為單位顯示
- [ ] 離線開啟版面正常（CSS fallback）

**驗證**:
```bash
# 用樣本 JSON 測試樣板注入
py .kiro/skills/game-analysis-dashboard/scripts/generate_game_dashboard.py --date 20260316
# 預期：產出 tigerbot/data/game_analysis/ 下的 .json 和 .html
# 檢查：HTML 版面穩定一致（不再因 Gemini 每次產出不同而變化）
```

---

### Phase 3: TigerBot 佈署整合（參考 arkbot-generator 模式）

**對應 Skill**: `arkbot-generator`（模式參考）
**交付物**: 對話說「遊戲分析」可觸發產出報告，網頁可瀏覽
**前置**: Phase 2 完成（dashboard_template.html 已固定）

**Skill 使用方式**:
- 參考 `arkbot-generator` 的三層架構模式（arkbot_core → bot_main / web_server）
- 參考其 WebSocket 訊息協議（status → dashboard_reply）
- 參考其意圖路由模式（關鍵字快速匹配 + Gemini 兜底）
- 不重新產生專案，而是修改既有 3 個檔案
- **ArkBot 執行時不呼叫 Gemini API**，僅讀取固定樣板 + 注入 JSON 資料

**HTML 產出方式（執行時）**:
```python
# generate_game_dashboard.py 中的 generate_html()
def generate_html(data_json, output_path):
    """套用固定樣板，注入 JSON 資料（不呼叫 Gemini）"""
    template_path = os.path.join(SKILL_ROOT, "assets", "dashboard_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    data_str = json.dumps(data_json, ensure_ascii=False)
    html = template.replace("/*__DASHBOARD_DATA__*/",
                            f"const DASHBOARD_DATA = {data_str};")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
```

**修改檔案清單**:

| 檔案 | 修改內容 | 參考來源 |
|:---|:---|:---|
| `tigerbot/src/intent_router.py` | +GAME_ANALYSIS_KEYWORDS + classify_intent 判斷 + Gemini prompt | revenue_skill 的 REVENUE 意圖模式 |
| `tigerbot/src/arkbot_core.py` | +GAME_ANALYSIS 分支（動態 import 腳本） | DASHBOARD 分支的 canvas_skill 模式 |
| `tigerbot/src/web_server.py` | +`/game-analysis` 端點 + WebSocket 路由 | `/dashboard` 端點 + canvas 路由模式 |

**實作步驟**:
1. `intent_router.py` — 新增 GAME_ANALYSIS_KEYWORDS 清單
2. `intent_router.py` — classify_intent() 中新增 GAME_ANALYSIS 判斷（優先於 CANVAS）
3. `intent_router.py` — Gemini 兜底 prompt 新增 GAME_ANALYSIS 意圖描述
4. `arkbot_core.py` — 定義 GAME_ANALYSIS_SCRIPT 路徑
5. `arkbot_core.py` — process_message() 新增 GAME_ANALYSIS 分支（動態 import + 執行）
6. `web_server.py` — 新增 `/game-analysis?date=YYYYMMDD` GET 端點
7. `web_server.py` — WebSocket 路由新增 `game_analysis_` 前綴判斷

**驗證**:
- TigerBot 對話輸入「遊戲分析」→ 回傳摘要 + 儀表板連結
- 瀏覽器開啟 `http://localhost:3000/game-analysis` → 顯示 HTML 儀表板
- 輸入「營收」→ 仍走 REVENUE 路徑（不被 GAME_ANALYSIS 攔截）
- 輸入「產生儀表板」→ 仍走 DASHBOARD 路徑

---

### Phase 4: Skill 文件與收尾

**交付物**: SKILL.md 完善、memory.md 更新、game_data_contract.md 確認

**前置**: Phase 3 完成

**實作步驟**:
1. 確認 `SKILL.md` 內容與實際實作一致（觸發詞、執行方式、輸出路徑）
2. 確認 `references/game_data_contract.md` 與實際 JSON 結構一致
3. 更新 `.kiro/steering/memory.md` — 新增 game-analysis-dashboard 記錄
4. 驗證所有端點與意圖路由正常運作
5. 重啟 TigerBot Web Server 確認無啟動錯誤

---

## ✅ 4. 驗證與測試指南

### 4.1 功能性測試（Phase 1 + 2）

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| CLI 預設日期 | `py scripts/generate_game_dashboard.py` | 產出最新日期的 JSON + HTML 至 `data/game_analysis/` |
| CLI 指定日期 | `py scripts/generate_game_dashboard.py --date 20260316` | 產出 `data/game_analysis/game_analysis_20260316.json` + `.html` |
| CLI 指定輸出 | `py scripts/generate_game_dashboard.py --output ./test_output` | 檔案產出至 test_output/ |
| 測試帳號排除 | 檢查 JSON 中的 users 數 | 不含 App_Pig.dbo.GameAccount 中的 UserID |
| 遊戲名稱對照 | 檢查 slot_games[0].game_name | 非空字串，非 "Game_xxx" 格式 |
| RTP 計算 | 檢查 slot_games[0].rtp | = total_win / total_bet * 100，保留兩位小數 |
| 日環比 | 檢查 kpi_cards[0].trend | 格式為 "+X.XX%" 或 "-X.XX%" 或 "N/A" |

### 4.2 格式與相容性測試

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| JSON 編碼 | 開啟 `data/game_analysis/` 下的 JSON 檔案 | UTF-8 編碼，中文正常顯示 |
| HTML 完整性 | 開啟 `data/game_analysis/` 下的 HTML 檔案 | 以 `<!DOCTYPE html>` 開頭，以 `</html>` 結尾 |
| HTML 離線開啟 | 用瀏覽器直接開啟 HTML 檔案 | CSS fallback 生效，版面不崩壞 |
| 數值格式 | 檢查 kpi_cards value | 押注量/贏分量以兆為單位（如 1.23T），玩家數含千分位逗號 |

### 4.3 整合測試（Phase 3）

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| 意圖 — 遊戲分析 | TigerBot 輸入「遊戲分析」 | intent = GAME_ANALYSIS |
| 意圖 — 押注分析 | TigerBot 輸入「押注分析」 | intent = GAME_ANALYSIS |
| 意圖 — 營收不被攔截 | TigerBot 輸入「昨日營收」 | intent = REVENUE |
| 意圖 — 儀表板不被攔截 | TigerBot 輸入「產生儀表板」 | intent = DASHBOARD |
| Web 端點 | GET `/game-analysis` | 回傳最新 game_analysis HTML，200 OK |
| Web 端點帶日期 | GET `/game-analysis?date=20260316` | 回傳指定日期 HTML |
| Web 端點無資料 | GET `/game-analysis?date=19990101` | 回傳 404 + 提示訊息 |
| WebSocket 路由 | 對話觸發遊戲分析 | dashboard_url 為 `/game-analysis?date=YYYYMMDD` |
| 既有功能不受影響 | 輸入「昨日營收」 | 營收儀表板正常產出 |
| 既有功能不受影響 | 輸入「產生儀表板」 | Canvas 儀表板正常產出 |

### 4.4 Skill 編排驗證

| 測試案例 | 操作 | 預期結果 |
|:---|:---|:---|
| ① sqlserver-data-exporter 模式 | 檢查腳本 DB 連線 | 讀取 sqlserver/config/db.yaml，使用 DRIVER={SQL Server} |
| ② 樣板套用模式 | 檢查 HTML 產出 | 讀取 assets/dashboard_template.html，注入 JSON 資料，不呼叫 Gemini |
| ③ arkbot-generator 模式 | 檢查 TigerBot 整合 | 意圖路由 + arkbot_core 分支 + web 端點三者一致 |
| ④ 數值格式 | 檢查 KPI 卡片 | 押注量/贏分量以兆（T）為單位 |

---

## 🐛 5. 已知問題與修正紀錄

| # | 問題 | 狀態 | 修正方式 |
|---|---|---|---|
| 1 | `DimGame_ID` 表不存在於 SQL Server | ✅ 已修正 | 改用 `MobileDW_Pig.dbo.DimScene`，從 SceneCode 提取 GameID + SceneName 中文名。變體 GameID（10xxx/30xxx/50xxx/101xxx）回退到基礎 GameID 查找。匹配率 100%（30/30 款顯示遊戲） |
| 2 | `f_FishSessionBetWinLog` 查詢超時（365M 筆） | ✅ 已修正 | 使用 threading + 90 秒超時保護，超時時 graceful skip（fish_games=[]）。加 NOLOCK hint + TOP 50 限制。目前仍超時，需 DBA 加索引才能根治 |
| 3 | 遊戲名稱對照表 `DimGame_ID` 在 BigQuery 有但 SQL Server 沒有 | ✅ 已記錄 | BigQuery 與 SQL Server 的維度表不完全同步，`DimScene` 是 SQL Server 端的替代方案 |
| 4 | Gemini 每次產出 HTML 品質不一致，偶爾截斷 | ✅ v2.0 已修正 | 改為固定樣板策略：開發階段用 Gemini 產出草稿，調整後固定為 `dashboard_template.html`，執行時僅注入 JSON |
| 5 | 押注量數值過大不易閱讀 | ✅ v2.0 已修正 | KPI cards 改用兆（T）為單位顯示 |
| 6 | `generate_html()` 仍呼叫 Gemini API（v1.0 模式） | ⬜ 待修正 | Task 6.2 + 6.3：產出固定樣板 + 改寫為 `template.replace()` 注入模式 |
| 7 | `build_report_json()` KPI value 仍用 `$` 格式 | ⬜ 待修正 | Task 6.3：改用 `format_value()` 函式，`>=1T` 顯示 `X.XXT`，`>=1B` 顯示 `X.XXB` |
| 8 | JSON title 仍寫「遊戲行為分析儀表板」 | ⬜ 待修正 | Task 6.3：改為「遊戲分析儀表板」 |

---

## 📎 附錄

### A. 樣板策略說明

#### 為什麼從 Gemini 動態產出改為固定樣板？

| 問題 | v1.0（Gemini 動態） | v2.0（固定樣板） |
|:---|:---|:---|
| 品質穩定性 | 每次產出不同，偶爾截斷或版面異常 | 固定版面，品質一致 |
| 執行速度 | 需等 Gemini API 回應（5-15 秒） | 本地樣板注入（< 1 秒） |
| 外部依賴 | 需要 GOOGLE_API_KEY | 不需要（僅開發階段用） |
| 可調整性 | 需修改 prompt 再重新產出 | 直接編輯 HTML 樣板 |
| 離線可用 | 否（需 API 連線） | 是 |

#### 樣板更新流程

當需要調整儀表板版面時：
1. 編輯 `.kiro/skills/game-analysis-dashboard/assets/dashboard_template.html`
2. 確認 `/*__DASHBOARD_DATA__*/` 佔位符仍存在
3. 用 CLI 重新產出 HTML 驗證
4. 若需大幅改版，可重新呼叫 Gemini 產出新草稿再調整

### B. 未來擴展 — 是否需要佈署流程 Skill？

### 現狀評估

目前「把新分析功能掛進 TigerBot」的流程是固定的三步：
1. `intent_router.py` — 加關鍵字 + 意圖判斷
2. `arkbot_core.py` — 加處理分支
3. `web_server.py` — 加端點 + WebSocket 路由

這個模式已在 REVENUE、DASHBOARD、GAME_ANALYSIS 三次重複驗證。

### 建議

**目前不需要**獨立的佈署 Skill，原因：
- 修改範圍固定（3 個檔案、3 個位置），不值得自動化
- 每次新增的業務邏輯不同（SQL 查詢、資料處理），無法完全模板化
- 本規格文件的「2.2 TigerBot 整合清單」已足夠作為標準化指引

**未來考慮建立的時機**：
- 當分析類 Skill 超過 5 個，且整合模式完全穩定
- 當需要非開發人員（如 PM）自助掛載新分析功能
- 屆時可建立 `tigerbot-integrator` Skill，自動修改三個檔案

---

> ═══ Part II：執行計畫 ═══

## 📊 6. 任務分解與時間估算

### Task 6.1: SQL 查詢與 JSON 產出驗證

**對應 Phase**: Phase 1
**預估時間**: 5 min
**前置任務**: —

**執行步驟**:
1. 執行 `py .kiro/skills/game-analysis-dashboard/scripts/generate_game_dashboard.py`
2. 檢查 JSON 結構完整性（kpi_cards / slot_games / vip / country）
3. 確認遊戲名稱匹配率、測試帳號排除

**交付物**: `tigerbot/data/game_analysis/game_analysis_{YYYYMMDD}.json`

---

### Task 6.2: HTML 樣板產出與調整

**對應 Phase**: Phase 2
**預估時間**: 15 min
**前置任務**: Task 6.1

**執行步驟**:
1. 用 Task 6.1 的樣本 JSON 呼叫 Gemini API 產出 HTML 草稿
2. 人工檢視 HTML 草稿，調整版面、配色、圖表樣式
3. 將 JSON 資料區塊替換為 `/*__DASHBOARD_DATA__*/` 佔位符
4. 確認數值格式使用兆（T）為單位
5. 確認 Chart.js / CSS 正確，離線可開啟
6. 儲存為 `.kiro/skills/game-analysis-dashboard/assets/dashboard_template.html`

**交付物**: `assets/dashboard_template.html`（固定樣板）

---

### Task 6.3: generate_game_dashboard.py 改為樣板套用

**對應 Phase**: Phase 2 → Phase 3 銜接
**預估時間**: 10 min
**前置任務**: Task 6.2

**執行步驟**:
1. 修改 `generate_html()` — 從呼叫 Gemini API 改為讀取固定樣板 + 注入 JSON
2. 移除 `_slim_data_for_gemini()`、`load_prompt_template()`、Gemini API 呼叫相關程式碼
3. 修改 `build_report_json()` — KPI cards value 改用兆（T）為單位格式化
4. 執行 CLI 驗證產出 HTML 正確

**交付物**: 更新後的 `generate_game_dashboard.py`

---

### Task 6.4: TigerBot 整合驗證

**對應 Phase**: Phase 3
**預估時間**: 5 min
**前置任務**: Task 6.3

**執行步驟**:
1. 確認 `intent_router.py` GAME_ANALYSIS 意圖正常
2. 確認 `arkbot_core.py` GAME_ANALYSIS 分支正常
3. 確認 `web_server.py` `/game-analysis` 端點正常
4. 重啟 TigerBot Web Server + Telegram Bot

**交付物**: TigerBot 可對話觸發遊戲分析 + 網頁瀏覽

---

### Task 6.5: 端對端整合測試

**對應 Phase**: Phase 3
**預估時間**: 10 min
**前置任務**: Task 6.4

**執行步驟**:
1. Web 端點測試（GET `/game-analysis`、帶日期、無資料 404）
2. 意圖路由測試（遊戲分析 / 押注分析 / 營收不被攔截）
3. 既有功能回歸測試（營收 / Canvas / 爬蟲 / 閒聊）

**交付物**: 測試結果記錄

---

### Task 6.6: 文件收尾

**對應 Phase**: Phase 4
**預估時間**: 5 min
**前置任務**: Task 6.5

**執行步驟**:
1. 確認 SKILL.md 與實際實作一致
2. 確認 game_data_contract.md 與 JSON 結構一致
3. 更新 memory.md
4. 更新本規格文件的 Checklist 與狀態

**交付物**: 文件全部同步

---

### 6.7 時間總表

| Task | 工項 | 預估時間 | 前置任務 | 狀態 |
|:---|:---|:---|:---|:---|
| 6.1 | SQL 查詢與 JSON 產出驗證 | 5 min | — | ✅ 已完成 |
| 6.2 | HTML 樣板產出與調整 | 15 min | 6.1 | ⬜ 待執行（關鍵路徑） |
| 6.3 | 腳本改為樣板套用 + 兆單位 | 10 min | 6.2 | ⬜ 待執行（關鍵路徑） |
| 6.4 | TigerBot 整合驗證 | 5 min | 6.3 | 🔄 需重新驗證（v1.0→v2.0） |
| 6.5 | 端對端整合測試 | 10 min | 6.4 | ⏳ 待人工測試 |
| 6.6 | 文件收尾 | 5 min | 6.5 | 🔄 進行中 |
| **合計** | | **~50 min** | | |

> Task 6.1 在 v1.0 階段已完成。Task 6.4 的 TigerBot 整合（意圖路由 + 端點 + WebSocket）已完成，但目前仍走 v1.0 Gemini 模式，需在 6.3 完成後重新驗證。
> **關鍵路徑：6.2 → 6.3** — 產出固定樣板 + 改寫腳本為樣板套用模式。

---

## ☑️ 7. 執行 Checklist

### Checklist: Task 6.1 — SQL 查詢與 JSON 產出

- [x] 腳本無報錯，正常執行完畢
- [x] 產出 `tigerbot/data/game_analysis/game_analysis_20260316.json`
- [x] JSON 含 kpi_cards（4 張）
- [x] JSON 含 slot_games（30 款，TOP 30）
- [x] JSON 含 vip_distribution（10 級）
- [x] JSON 含 country_distribution（6 個市場）
- [x] 遊戲名稱 100% 匹配（30/30 款皆有中文名，改用 DimScene 對照）
- [x] 測試帳號已排除
- [ ] ~~JSON 含 fish_games~~ → 捕魚機查詢超時（365M 筆），graceful skip，fish_games=[]

**實際執行結果** (2026-03-17):
> 📊 查詢日期: 20260316 / 🎮 遊戲名稱對照: 145 筆 / 🎰 老虎機: 337 款 → TOP 30 / 🐟 捕魚機: 超時跳過 / 👑 VIP: 10 級 / 🌍 國家: 6 市場

---

### Checklist: Task 6.2 — HTML 樣板產出與調整

- [ ] 用 Gemini 產出 HTML 草稿
- [ ] 版面佈局合理（KPI 卡片 + 圖表 + 表格）
- [ ] 替換為 `/*__DASHBOARD_DATA__*/` 佔位符
- [ ] KPI 卡片讀取 `DASHBOARD_DATA.kpi_cards`
- [ ] 遊戲表格讀取 `DASHBOARD_DATA.slot_games`
- [ ] VIP 分佈圖讀取 `DASHBOARD_DATA.vip_distribution`
- [ ] 國家分佈圖讀取 `DASHBOARD_DATA.country_distribution`
- [ ] 押注量/贏分量以兆（T）為單位顯示
- [ ] 離線開啟版面正常（CSS fallback）
- [ ] 儲存至 `assets/dashboard_template.html`

**實際執行結果**: （待執行）

---

### Checklist: Task 6.3 — 腳本改為樣板套用

- [ ] `generate_html()` 改為讀取固定樣板 + 注入 JSON
- [ ] 移除 Gemini API 呼叫相關程式碼
- [ ] `build_report_json()` KPI value 改用兆（T）格式
- [ ] CLI 執行產出 HTML 正確
- [ ] HTML 以 `<!DOCTYPE html>` 開頭，以 `</html>` 結尾
- [ ] HTML 中 KPI 數值顯示兆單位

**實際執行結果**: （待執行）

---

### Checklist: Task 6.4 — TigerBot 整合驗證

- [x] `intent_router.py` GAME_ANALYSIS_KEYWORDS 正確
- [x] `arkbot_core.py` GAME_ANALYSIS 分支正確
- [x] `web_server.py` `/game-analysis` 端點正確
- [x] `web_server.py` WebSocket `game_analysis_` 路由正確
- [x] getDiagnostics 無語法錯誤
- [ ] 確認 arkbot_core.py 呼叫的是 v2.0 樣板模式（非 Gemini 動態模式）← 待 6.3 完成後驗證

**實際執行結果** (2026-03-17):
> 三個檔案修改完畢，語法檢查通過。意圖路由 + 端點 + WebSocket 已掛載，但目前腳本仍走 v1.0 Gemini 模式。

---

### Checklist: Task 6.5 — 端對端整合測試

- [ ] GET `/game-analysis` → 200 OK ← 待人工驗證
- [ ] GET `/game-analysis?date=20260316` → 200 OK ← 待人工驗證
- [ ] GET `/game-analysis?date=19990101` → 404 ← 待人工驗證
- [ ] 對話「遊戲分析」→ GAME_ANALYSIS 意圖 ← 待人工驗證
- [ ] 對話「昨日營收」→ REVENUE 意圖（不被攔截） ← 待人工驗證
- [ ] 對話「產生儀表板」→ DASHBOARD 意圖（不被攔截） ← 待人工驗證
- [ ] 營收儀表板正常（`/dashboard`） ← 待人工驗證
- [ ] Canvas 儀表板正常（`/canvas`） ← 待人工驗證

**實際執行結果**: （待人工測試）

---

### Checklist: Task 6.6 — 文件收尾

- [x] SKILL.md 觸發詞與 intent_router 一致
- [x] SKILL.md 執行方式與 CLI 參數一致
- [x] memory.md 已更新至 v7.0.0
- [ ] 本規格文件 Checklist 全部更新
- [ ] game_data_contract.md 與 JSON 結構一致

**實際執行結果**: （進行中）

---

## ⚠️ 8. 風險管理與應對

| 風險 | 機率 | 影響 | 狀態 | 應對策略 |
|:---|:---|:---|:---|:---|
| f_FishSessionBetWinLog 查詢超時（365M 筆） | 高 | 中 | ✅ 已處理 | threading 90 秒超時 + graceful skip，需 DBA 加索引根治 |
| Gemini API 產出 HTML 品質不穩定 | 中 | 高 | ✅ v2.0 已解決 | 改為固定樣板策略，開發階段一次性產出後固定 |
| 意圖衝突（GAME_ANALYSIS vs CANVAS） | 低 | 中 | ✅ 已處理 | GAME_ANALYSIS 優先順序高於 CANVAS |
| DimGame_ID 不存在於 SQL Server | — | 高 | ✅ 已修正 | 改用 DimScene + 變體 GameID 回退，匹配率 100% |
| 樣板佔位符被意外覆蓋 | 低 | 高 | ⬜ 待預防 | 樣板檔案加入版本控制，修改前備份 |
| 押注量數值過大不易閱讀 | — | 中 | ✅ v2.0 已解決 | KPI cards 改用兆（T）為單位 |

---

**文件版本**: v2.1
**維護者**: paddyyang
**最後更新**: 2026-03-18
