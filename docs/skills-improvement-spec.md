# 🚀 Skills 體系長期改進計畫 (v1.0)

**目標：** 將 21 個 Kiro Skills 從「可用」提升至「成熟穩定」，補強能力缺口，建立持續改進機制
**作者**: paddyyang
**日期**: 2026-03-25
**版本**: v1.0

---

## ═══ Part I：規格設計 ═══

## 📋 1. 需求分析

### 1.1 核心功能需求

本計畫涵蓋五大改進方向：

1. **v0.1.0 技能成熟度提升** — 13 個停在初版的技能需要迭代驗證，逐步升級至穩定版
2. **知識指南類技能合併評估** — 5 個純參考文件型技能（prompt-engineering-guide / software-architecture-guide / mcp-builder-guide / tdd-workflow / d3-visualization-guide）觸發頻率與維護成本評估
3. **fish-spec-writer 泛化** — 從捕魚機專用擴展為通用遊戲機台規格撰寫器
4. **測試執行能力補強** — 目前 tdd-workflow 只提供指引，缺少實際執行測試的能力
5. **CI 自動化技能** — 缺少部署與持續整合的自動化流程

### 1.2 Skill 編排需求

- `skill-creator` 的 eval 框架用於驗證技能成熟度提升
- `skill-spec-writer` 產出泛化規格 → `skill-creator` 執行改造
- `skill-sync` 在每次技能修改後同步至 `.agent/skills/`
- `changelog-generator` 記錄每次版本變更

### 1.3 技術約束與驗證指標

| 模組 | 前置需求 | 獨立性 | 驗證指標 |
|:---|:---|:---|:---|
| v0.1.0 成熟度提升 | skill-creator eval 框架 | **高度獨立**（每個技能可獨立迭代） | 技能觸發後產出符合 SKILL.md 規範，eval pass_rate ≥ 80% |
| 知識指南合併評估 | 觸發頻率數據 | **高度獨立** | 產出評估報告，含合併/保留建議與理由 |
| fish-spec-writer 泛化 | game-design-document-writer 參考 | **中度獨立** | 泛化後能產出老虎機、棋牌等至少 3 種遊戲類型的規格 |
| 測試執行能力 | Python pytest 環境 | **中度獨立** | 能自動執行測試並回報結果（pass/fail/coverage） |
| CI 自動化 | GitHub Actions 或等效 | **低度獨立**（依賴前四項穩定） | push 後自動執行 lint + validate + sync |

### 1.4 測試支援要求

- 每個技能升級後需通過 `quick_validate.py` 驗證
- 泛化後的 game-spec-writer 需用至少 3 種遊戲類型測試
- CI pipeline 需在本地可模擬執行（`py scripts/ci_local.py`）

---

## 🏗️ 2. 系統設計

### 2.1 架構設計

```
改進計畫執行流程：

Phase 1: 成熟度提升（13 技能）
  ├── 批次 A（高頻使用）：document-summarizer, websearch-summarizer, changelog-generator
  ├── 批次 B（開發工具）：env-setup-installer, env-smoke-test, skill-seeker, skill-spec-writer
  └── 批次 C（領域專用）：game-design-document-writer, fish-spec-writer, 其餘 4 個指南類

Phase 2: 知識指南評估
  └── 分析 5 個指南 → 決定合併或保留

Phase 3: fish-spec-writer → game-spec-writer 泛化
  └── 擴展 references/ 支援多遊戲類型

Phase 4: 測試執行能力
  └── tdd-workflow 增加 scripts/run_tests.py

Phase 5: CI 自動化
  └── 新增 ci-automation skill 或 GitHub Actions workflow
```

### 2.2 數據結構設計

技能成熟度評估表：

```markdown
| 技能 | 當前版本 | 觸發測試 | eval pass_rate | 目標版本 | 狀態 |
|:---|:---|:---|:---|:---|:---|
| document-summarizer | 0.1.0 | ⬜ | — | 0.2.0 | ⬜ 待執行 |
| ... | ... | ... | ... | ... | ... |
```

### 2.3 目錄結構

```
改進計畫不新增頂層目錄，變更集中在：

.kiro/skills/
├── game-spec-writer/          # fish-spec-writer 泛化後重命名
│   ├── SKILL.md               # 通用遊戲機台規格
│   ├── README.md
│   └── references/
│       ├── fish-game.md       # 捕魚機專用指南
│       ├── slot-machine.md    # 老虎機專用指南
│       └── card-game.md       # 棋牌專用指南
│
├── tdd-workflow/
│   └── scripts/
│       └── run_tests.py       # 新增：測試執行腳本
│
└── ci-automation/             # 新增技能（Phase 5）
    ├── SKILL.md
    ├── README.md
    └── scripts/
        └── ci_local.py        # 本地 CI 模擬
```

---

## 🛠️ 3. 實作路徑

### Phase 1: v0.1.0 技能成熟度提升

**交付物**：13 個技能升級至 ≥ v0.2.0
**方法**：對每個技能執行「觸發測試 → 檢視產出 → 修正 SKILL.md → 更新 README 版本」循環

批次 A（高頻使用，優先）：
- `document-summarizer` — 測試長文件摘要品質
- `websearch-summarizer` — 測試 URL 抓取與摘要結構
- `changelog-generator` — 測試 git log 解析完整性

批次 B（開發工具）：
- `env-setup-installer` — 測試安裝引導完整性
- `env-smoke-test` — 測試 4 階段煙霧測試
- `skill-seeker` — 測試文件轉技能草稿品質
- `skill-spec-writer` — 測試規格文件結構完整性

批次 C（領域專用 + 指南類）：
- `game-design-document-writer` — 測試 GDD 產出
- `fish-spec-writer` — 測試機台規格產出（Phase 3 前先驗證現狀）
- 5 個知識指南 — 觸發測試（Phase 2 評估用）

**驗證**：每個技能 eval pass_rate ≥ 80%，README 版本號遞增

### Phase 2: 知識指南合併評估

**交付物**：評估報告（保留在 `docs/guide-skills-evaluation.md`）
**方法**：
1. 對 5 個指南各觸發 3 次，記錄觸發準確度與產出品質
2. 分析 description 關鍵字重疊度
3. 評估合併為 `dev-guides`（用 references/ 分章節）vs 維持獨立的利弊
4. 產出建議與執行方案

**驗證**：評估報告含量化數據（觸發率、關鍵字重疊度）和明確建議

### Phase 3: fish-spec-writer 泛化為 game-spec-writer

**交付物**：`game-spec-writer` 技能（取代 `fish-spec-writer`）
**方法**：
1. 分析 fish-spec-writer 的 SKILL.md，提取通用遊戲機台規格框架
2. 將捕魚機專用內容移至 `references/fish-game.md`
3. 新增 `references/slot-machine.md`（老虎機）和 `references/card-game.md`（棋牌）
4. SKILL.md 改為通用框架，根據遊戲類型載入對應 reference
5. 重命名目錄 `fish-spec-writer` → `game-spec-writer`
6. 更新 structure.md、product.md、memory.md

**驗證**：分別用「捕魚機」「老虎機」「棋牌」三種類型觸發，檢查產出是否符合各自規格

### Phase 4: 測試執行能力補強

**交付物**：`tdd-workflow/scripts/run_tests.py` + SKILL.md 更新
**方法**：
1. 在 tdd-workflow 新增 `scripts/run_tests.py`，封裝 pytest 執行
2. 支援參數：`--path`（測試目錄）、`--coverage`（覆蓋率報告）、`--verbose`
3. 更新 SKILL.md 加入「執行測試」步驟（不只是指引）
4. 更新 README 版本號

**驗證**：`py .kiro/skills/tdd-workflow/scripts/run_tests.py --path tests/` 能正確執行並回報結果

### Phase 5: CI 自動化技能

**交付物**：`ci-automation` 技能 或 `.github/workflows/ci.yml`
**方法**：
1. 評估需求：lint（ruff/flake8）+ validate（quick_validate.py）+ sync（skill-sync）
2. 方案 A：GitHub Actions workflow（`.github/workflows/ci.yml`）
3. 方案 B：新增 `ci-automation` Kiro skill + `scripts/ci_local.py` 本地模擬
4. 建議採方案 B + A 並行：skill 提供指引和本地模擬，Actions 提供自動化

**驗證**：`py scripts/ci_local.py` 能在本地模擬完整 CI 流程（lint → validate → sync）

---

## ✅ 4. 驗證與測試指南

### 4.1 功能性測試

| 測試項目 | 操作 | 預期結果 |
|:---|:---|:---|
| 技能成熟度 | 對每個技能觸發 3 次 | 產出結構完整、格式正確，pass_rate ≥ 80% |
| game-spec-writer 泛化 | 分別用 3 種遊戲類型觸發 | 各自產出對應類型的完整規格 |
| 測試執行 | `run_tests.py --path tests/` | 正確執行 pytest 並回報 pass/fail |
| CI 本地模擬 | `ci_local.py` | lint + validate + sync 全部通過 |

### 4.2 格式與相容性測試

- 所有升級後的 README.md 符合版本資訊表格格式
- SKILL.md YAML 前置資料通過 `quick_validate.py`
- game-spec-writer 重命名後 skill-sync 能正確同步

### 4.3 整合測試

- skill-sync 全量同步後 `.agent/skills/` 與 `.kiro/skills/` 一致
- changelog-generator 能正確記錄版本變更
- structure.md 和 product.md 技能清單與實際目錄一致

### 4.4 Skill 編排驗證

- `skill-spec-writer` → `skill-creator` 鏈式流程：產出的 spec 能被 skill-creator 正確消費
- `tdd-workflow` + `run_tests.py`：指引 + 執行的完整閉環

---

## 🐛 5. 已知問題與修正紀錄

| # | 問題 | 狀態 | 修正方式 |
|---|---|---|---|
| 1 | skill-creator README 版本格式不一致 | ✅ 已修正 | 統一為表格式（v2.1.0） |
| 2 | product.md 技能數量過時（19→21） | ✅ 已修正 | 補 fish-spec-writer + dashboard-skill-generator |
| 3 | dashboard 兩技能無交叉引用 | ✅ 已修正 | 互相加入使用場景差異說明 |
| 4 | 13 個技能停在 v0.1.0 | ✅ 已修正 | 全部通過 quick_validate，版本升至 v0.x.1 |
| 5 | 知識指南類觸發頻率不明 | ✅ 已評估 | 維持獨立，不合併（docs/guide-skills-evaluation.md） |
| 6 | fish-spec-writer 過度特化 | ✅ 已修正 | 泛化為 game-spec-writer（支援捕魚機/老虎機/棋牌） |
| 7 | 無測試執行能力 | ✅ 已修正 | tdd-workflow 新增 scripts/run_tests.py |
| 8 | 無 CI 自動化 | ✅ 已修正 | 新增 ci-automation 技能 + scripts/ci_local.py |

---

## ═══ Part II：執行計畫 ═══

## 📊 6. 任務分解與時間估算

### Task 6.1: 批次 A 技能成熟度提升（高頻使用）

**對應 Phase**: Phase 1
**負責人**: paddyyang + AI
**預估時間**: 60 分鐘
**前置任務**: 無

**執行步驟**:
1. 對 `document-summarizer` 觸發 3 次不同長度文件，檢視摘要品質
2. 對 `websearch-summarizer` 觸發 3 次不同 URL，檢視結構化摘要
3. 對 `changelog-generator` 用本 repo git log 測試，檢視解析完整性
4. 根據測試結果修正各技能 SKILL.md
5. 更新各技能 README.md 版本號至 v0.2.0 + 變更紀錄

**交付物**: 3 個技能升級至 v0.2.0

---

### Task 6.2: 批次 B 技能成熟度提升（開發工具）

**對應 Phase**: Phase 1
**負責人**: paddyyang + AI
**預估時間**: 60 分鐘
**前置任務**: 無（可與 6.1 並行）

**執行步驟**:
1. 對 `env-setup-installer` 觸發，檢視安裝引導完整性
2. 對 `env-smoke-test` 觸發，檢視 4 階段測試覆蓋度
3. 對 `skill-seeker` 用一份 Markdown 文件測試轉換品質
4. 對 `skill-spec-writer` 用一個簡單需求測試規格產出
5. 修正 SKILL.md + 更新 README 版本號

**交付物**: 4 個技能升級至 v0.2.0

---

### Task 6.3: 批次 C 技能成熟度提升（領域專用）

**對應 Phase**: Phase 1
**負責人**: paddyyang + AI
**預估時間**: 45 分鐘
**前置任務**: 無（可與 6.1、6.2 並行）

**執行步驟**:
1. 對 `game-design-document-writer` 觸發，檢視 GDD 產出品質
2. 對 `fish-spec-writer` 觸發，記錄現狀作為 Phase 3 基線
3. 對 5 個知識指南各觸發 1 次，記錄觸發準確度（Phase 2 用）
4. 修正有明顯問題的 SKILL.md
5. 更新 README 版本號

**交付物**: 剩餘技能升級至 v0.2.0，知識指南觸發數據

---

### Task 6.4: 知識指南合併評估

**對應 Phase**: Phase 2
**負責人**: paddyyang + AI
**預估時間**: 30 分鐘
**前置任務**: Task 6.3（需要觸發數據）

**執行步驟**:
1. 彙整 5 個指南的觸發測試數據
2. 分析 description 關鍵字重疊度（用文字比對）
3. 評估合併方案（dev-guides + references/）vs 維持獨立
4. 撰寫評估報告 `docs/guide-skills-evaluation.md`
5. 根據結論決定是否執行合併

**交付物**: `docs/guide-skills-evaluation.md` 評估報告

---

### Task 6.5: fish-spec-writer 泛化為 game-spec-writer

**對應 Phase**: Phase 3
**負責人**: paddyyang + AI
**預估時間**: 45 分鐘
**前置任務**: Task 6.3（需要 fish-spec-writer 基線數據）

**執行步驟**:
1. 分析 fish-spec-writer SKILL.md，提取通用框架
2. 將捕魚機專用內容移至 `references/fish-game.md`
3. 撰寫 `references/slot-machine.md`（老虎機指南）
4. 撰寫 `references/card-game.md`（棋牌指南）
5. 重寫 SKILL.md 為通用遊戲機台規格框架
6. 重命名目錄 `fish-spec-writer` → `game-spec-writer`
7. 用 3 種遊戲類型觸發驗證
8. 更新 structure.md、product.md、memory.md

**交付物**: `game-spec-writer` 技能 v0.2.0，取代 `fish-spec-writer`

---

### Task 6.6: tdd-workflow 測試執行能力補強

**對應 Phase**: Phase 4
**負責人**: paddyyang + AI
**預估時間**: 30 分鐘
**前置任務**: 無

**執行步驟**:
1. 在 `tdd-workflow/scripts/` 新增 `run_tests.py`
2. 實作 pytest 封裝：`--path`、`--coverage`、`--verbose` 參數
3. 更新 SKILL.md 加入「執行測試」工作流步驟
4. 更新 README 版本號至 v0.2.0
5. 用一個簡單測試案例驗證腳本

**交付物**: `run_tests.py` + tdd-workflow v0.2.0

---

### Task 6.7: CI 自動化技能建立

**對應 Phase**: Phase 5
**負責人**: paddyyang + AI
**預估時間**: 45 分鐘
**前置任務**: Task 6.6（需要測試執行能力）

**執行步驟**:
1. 用 `skill-spec-writer` 產出 ci-automation 技能規格
2. 用 `skill-creator` 建立 `ci-automation` 技能骨架
3. 實作 `scripts/ci_local.py`：lint（ruff）→ validate → sync 流程
4. 撰寫 `.github/workflows/ci.yml`（GitHub Actions）
5. 本地測試 `ci_local.py`
6. 更新 structure.md、product.md、memory.md

**交付物**: `ci-automation` 技能 v0.1.0 + GitHub Actions workflow

---

### Task 6.8: 全量同步與文件更新

**對應 Phase**: 收尾
**負責人**: paddyyang + AI
**預估時間**: 15 分鐘
**前置任務**: Task 6.1 ~ 6.7 全部完成

**執行步驟**:
1. 執行 `skill-sync` 全量同步
2. 更新 structure.md 技能清單
3. 更新 product.md 技能數量與描述
4. 更新 memory.md 完成狀態
5. Git commit + push

**交付物**: 所有文件同步完成，推送至 GitHub

---

### 6.X 時間總表

| Task | 工項 | 預估時間 | 前置任務 | 狀態 |
|:---|:---|:---|:---|:---|
| 6.1 | 批次 A 成熟度提升（3 技能） | 60 min | — | ✅ 已完成 |
| 6.2 | 批次 B 成熟度提升（4 技能） | 60 min | — | ✅ 已完成 |
| 6.3 | 批次 C 成熟度提升（6 技能） | 45 min | — | ✅ 已完成 |
| 6.4 | 知識指南合併評估 | 30 min | 6.3 | ✅ 已完成 |
| 6.5 | fish → game-spec-writer 泛化 | 45 min | 6.3 | ✅ 已完成 |
| 6.6 | tdd-workflow 測試執行補強 | 30 min | — | ✅ 已完成 |
| 6.7 | CI 自動化技能建立 | 45 min | 6.6 | ✅ 已完成 |
| 6.8 | 全量同步與文件更新 | 15 min | 6.1~6.7 | ✅ 已完成 |
| | **合計** | **330 min（~5.5 hr）** | | |

---

## ☑️ 7. 執行 Checklist

### Checklist: Task 6.1 — 批次 A 成熟度提升

- [ ] document-summarizer 觸發 3 次，產出結構完整
- [ ] websearch-summarizer 觸發 3 次，摘要含來源引用
- [ ] changelog-generator 用本 repo git log 測試通過
- [ ] 3 個技能 SKILL.md 已修正（若有問題）
- [ ] 3 個技能 README.md 版本升至 v0.2.0

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.2 — 批次 B 成熟度提升

- [ ] env-setup-installer 觸發測試通過
- [ ] env-smoke-test 4 階段測試覆蓋完整
- [ ] skill-seeker 文件轉技能草稿品質合格
- [ ] skill-spec-writer 規格產出結構完整
- [ ] 4 個技能 README.md 版本升至 v0.2.0

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.3 — 批次 C 成熟度提升

- [ ] game-design-document-writer GDD 產出品質合格
- [ ] fish-spec-writer 現狀基線已記錄
- [ ] 5 個知識指南觸發數據已記錄
- [ ] 有明顯問題的 SKILL.md 已修正
- [ ] README.md 版本號已更新

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.4 — 知識指南合併評估

- [ ] 5 個指南觸發數據已彙整
- [ ] description 關鍵字重疊度已分析
- [ ] 合併 vs 獨立利弊已評估
- [ ] `docs/guide-skills-evaluation.md` 已撰寫
- [ ] 結論已明確（合併/保留/部分合併）

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.5 — fish → game-spec-writer 泛化

- [ ] 通用框架已從 fish-spec-writer 提取
- [ ] `references/fish-game.md` 已建立
- [ ] `references/slot-machine.md` 已建立
- [ ] `references/card-game.md` 已建立
- [ ] SKILL.md 已改為通用框架
- [ ] 目錄已重命名為 `game-spec-writer`
- [ ] 捕魚機觸發測試通過
- [ ] 老虎機觸發測試通過
- [ ] 棋牌觸發測試通過
- [ ] structure.md / product.md / memory.md 已更新

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.6 — tdd-workflow 測試執行補強

- [ ] `scripts/run_tests.py` 已建立
- [ ] 支援 `--path` 參數
- [ ] 支援 `--coverage` 參數
- [ ] 支援 `--verbose` 參數
- [ ] SKILL.md 已加入執行測試步驟
- [ ] README.md 版本升至 v0.2.0
- [ ] 簡單測試案例驗證通過

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.7 — CI 自動化技能建立

- [ ] ci-automation 技能規格已產出
- [ ] 技能骨架已建立（SKILL.md + README.md）
- [ ] `scripts/ci_local.py` 已實作
- [ ] lint 步驟正常（ruff 或 flake8）
- [ ] validate 步驟正常（quick_validate.py）
- [ ] sync 步驟正常（skill-sync）
- [ ] `.github/workflows/ci.yml` 已建立
- [ ] 本地 `ci_local.py` 測試通過

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

### Checklist: Task 6.8 — 全量同步與文件更新

- [ ] skill-sync 全量同步成功（所有技能）
- [ ] structure.md 技能清單已更新
- [ ] product.md 技能數量與描述已更新
- [ ] memory.md 完成狀態已更新
- [ ] Git commit + push 完成

**實際執行結果**:
> （執行後填寫）

**遇到的問題**:
> （執行後填寫）

---

## ⚠️ 8. 風險管理與應對

| 風險 | 機率 | 影響 | 狀態 | 應對策略 |
|:---|:---|:---|:---|:---|
| v0.1.0 技能修正後破壞現有觸發行為 | 中 | 中 | ⬜ | 修改前先記錄基線產出，修改後比對 |
| 知識指南合併後觸發準確度下降 | 中 | 低 | ⬜ | 合併前先用 eval 測試，不合格則保留獨立 |
| fish-spec-writer 重命名導致引用斷裂 | 低 | 高 | ⬜ | 全專案搜尋 fish-spec-writer 引用，逐一更新 |
| CI pipeline 在 GitHub Actions 環境差異 | 中 | 低 | ⬜ | 先用 ci_local.py 本地驗證，再推 Actions |
| ruff/flake8 未安裝導致 CI 失敗 | 低 | 低 | ⬜ | 加入 requirements-dev.txt 或 CI 步驟自動安裝 |
| 改進計畫耗時超出預估 | 中 | 低 | ⬜ | Phase 1~3 為核心，Phase 4~5 可延後 |

---

**文件版本**: v1.0
**維護者**: paddyyang
**最後更新**: 2026-03-25
