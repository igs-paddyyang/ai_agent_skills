# skill-creator（技能建立器）

> 整合版 — 結合快速建立與迭代改進的 Kiro 技能開發工具。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 2.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-18 |
| 最後更新 | 2026-03-19 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

skill-creator 是一個用於建立、測試和迭代改進 Kiro 技能的完整開發工具。它整合了兩個來源的優勢：

- 來自社群版的**快速建立流程**：互動式腦力激盪、範本套用、驗證與安裝
- 來自 Anthropic 官方版的**迭代改進管線**：eval 測試、benchmark 比較、描述觸發率優化

## 主要特色

- 🎯 互動式腦力激盪 — 協作式會議，定義技能用途與範圍
- ✨ 範本自動化 — 零手動配置的自動檔案產生
- 🔍 品質驗證 — YAML 前置資料、屬性白名單、格式檢查
- 📊 視覺化進度條 — 即時進度指示器
- 🧪 Eval 測試框架 — subagent 並行測試 with_skill vs baseline
- 📈 Benchmark 分析 — 定量效能比較（pass_rate、時間、token）
- 🎯 描述優化 — 自動化觸發率優化循環
- 🔬 盲測比較 — A/B 測試消除偏見
- 📦 打包發布 — 一鍵打包為 .skill 檔案

## 使用方式

### 快速建立新技能

直接要求建立新技能：

```
「建立一個用於除錯 Python 錯誤的新技能」
「建立一個協助 git 工作流程的技能」
```

技能將以視覺化進度追蹤引導你完成 5 個階段：
1. 腦力激盪（20%）— 定義用途、觸發條件與類型
2. 提詞增強（40%，選用）— 精煉技能描述
3. 檔案產生（60%）— 從範本建立檔案
4. 驗證（80%）— 檢查品質與標準
5. 安裝（100%）— 選擇工作區、全域或兩者

### 使用腳本快速初始化

```bash
python scripts/init_skill.py my-new-skill --path .kiro/skills
```

### 驗證技能

```bash
python scripts/quick_validate.py .kiro/skills/my-skill
```

### 測試與迭代改進

建立技能後，可以進入 eval/迭代循環：

1. 撰寫測試案例到 `evals/evals.json`
2. 用 subagent 並行執行 with_skill 和 baseline
3. 用 `eval-viewer/generate_review.py` 在瀏覽器中檢視結果
4. 根據回饋改進技能
5. 重複直到滿意

### 描述觸發率優化

```bash
python -m scripts.run_loop \
  --eval-set trigger-eval.json \
  --skill-path .kiro/skills/my-skill \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

### 打包技能

```bash
python -m scripts.package_skill .kiro/skills/my-skill
```

## 檔案結構

```
.kiro/skills/skill-creator/
├── SKILL.md                    # 主要技能指令（繁中）
├── README.md                   # 本文件
├── agents/                     # subagent 指令
│   ├── grader.md               # 評分 agent
│   ├── comparator.md           # 盲測比較 agent
│   └── analyzer.md             # benchmark 分析 agent
├── assets/
│   └── eval_review.html        # eval 審閱 HTML 模板
├── eval-viewer/
│   ├── generate_review.py      # 結果檢視器生成
│   └── viewer.html             # 檢視器模板
├── references/
│   ├── schemas.md              # JSON schema 定義
│   ├── output-patterns.md      # 輸出模式指南
│   └── workflows.md            # 工作流程模式指南
├── scripts/
│   ├── __init__.py
│   ├── utils.py                # 共用工具函式
│   ├── init_skill.py           # 技能初始化
│   ├── quick_validate.py       # 快速驗證
│   ├── package_skill.py        # 打包
│   ├── run_eval.py             # 觸發率測試
│   ├── run_loop.py             # eval + improve 迭代循環
│   ├── aggregate_benchmark.py  # benchmark 聚合
│   ├── generate_report.py      # HTML 報告生成
│   └── improve_description.py  # 描述優化
├── templates/
│   ├── default.md              # 預設 SKILL.md 範本
│   └── readme.md               # 預設 README.md 範本（含版本號）
```

## 建立的技能結構

使用此工具建立的技能會有以下結構：

```
.kiro/skills/your-skill-name/
├── SKILL.md              # 主要技能指令（1.5-2k 字理想）
├── README.md             # 技能說明文件（含版本號與變更紀錄）
├── references/           # 詳細指南（按需載入）
├── scripts/              # 可執行腳本
└── assets/               # 範本、圖片等
```

## 版本號管理

所有技能採用 Semantic Versioning（`MAJOR.MINOR.PATCH`）：

| 版本位 | 何時遞增 | 範例 |
|--------|---------|------|
| MAJOR | 不相容的重大變更 | 1.0.0 → 2.0.0 |
| MINOR | 新增功能，向下相容 | 1.0.0 → 1.1.0 |
| PATCH | 修正錯誤、小幅優化 | 1.0.0 → 1.0.1 |

- 新建技能從 `0.1.0` 開始
- 經 eval 驗證穩定後升級為 `1.0.0`
- 每次修改必須同步更新 README.md 的版本資訊與變更紀錄

## 品質標準

**SKILL.md 要求：**
- 理想 500 行以內
- YAML 前置資料必須包含 name 和 description
- name 為 kebab-case，最多 64 字元
- description 最多 1024 字元
- 祈使句寫作風格
- 漸進式揭露模式

## 驗證項目

每個建立的技能都會自動驗證：
- YAML 前置資料格式與必要欄位
- 屬性白名單（name, description, license, allowed-tools, metadata, compatibility）
- 名稱格式（kebab-case）
- 描述長度限制

## 來源

此整合版結合了以下兩個來源：
- [anthropics/skills](https://github.com/anthropics/skills) — Anthropic 官方 skill-creator
- [antigravity-awesome-skills]() — 社群版 skill-creator（視覺化快速建立流程）
https://github.com/sickn33/antigravity-awesome-skills
---

---

## 變更紀錄

### v2.1.0（2026-03-19）
- 新增技能安裝路徑自動偵測：`.kiro/` 存在 → 研發系統（建在 `.kiro/skills/`），僅 `.agent/skills/` → 正式環境
- 偵測優先順序：`.kiro/skills/` > `.agent/skills/`
- 支援 `--path` 手動覆蓋
- 更新階段 3（檔案產生）、階段 4（驗證）、階段 5（安裝）使用偵測路徑

### v2.0.0（2026-03-18）
- 整合社群版快速建立流程與 Anthropic 官方迭代改進管線
- 新增 README.md 自動產出與版本號管理
- 新增實戰案例（email-writer）


---

## 實戰案例：使用 skill-creator 建立 email-writer 技能

以下以 `email-writer`（Email 撰寫師）為例，展示如何使用 skill-creator 從零建立一個完整技能。

### 步驟 1：啟動腦力激盪

對 Kiro 說：

```
幫我建立一個撰寫商務 Email 的技能
```

skill-creator 會進入腦力激盪階段，詢問你：

```
[████░░░░░░░░░░░░░░] 20% - 步驟 1/5：腦力激盪與規劃

1. 這個技能要做什麼？
   → 根據情境自動產出專業語氣的商務 Email

2. 何時應該觸發？
   → 「撰寫客戶回覆」「寫一封致歉信」「幫我寫 Email 給主管」

3. 預期的輸出格式？
   → 結構化的 Email 草稿（主旨、語氣標註、本文、署名）

4. 需要測試案例嗎？
   → 是，可以用不同情境（客訴回應、合作邀約、催款通知）來測試
```

### 步驟 2：產生技能骨架

確認意圖後，skill-creator 會自動建立目錄結構：

```
[████████████░░░░░░] 60% - 步驟 3/5：檔案產生

✅ 已建立：
   .kiro/skills/email-writer/
   ├── SKILL.md
   ├── README.md（v0.1.0）
   ├── references/
   │   └── prompt-templates.md
   ├── scripts/
   └── assets/
```

### 步驟 3：撰寫 SKILL.md

skill-creator 會根據腦力激盪的結果，撰寫 SKILL.md。關鍵部分包括：

**前置資料（觸發描述要「積極」一些）：**

```yaml
---
name: email-writer
description: "當使用者需要撰寫商務 Email、客戶回覆、投訴回應或跨部門溝通信件時，
  應使用此技能。根據情境自動產出專業語氣的信件，支援多種商務場景。"
---
```

**角色定義（解釋為什麼，而非堆砌 MUST）：**

```markdown
## 角色定義

扮演資深商務溝通專家。這個角色設定很重要，因為商務 Email 的語氣拿捏
需要豐富的實務經驗——太正式會顯得冷漠，太隨意會失去專業感。
```

**情境範本庫（用表格組織多種場景）：**

```markdown
| 情境         | 語氣         | 重點                                     |
|:-------------|:-------------|:-----------------------------------------|
| 客戶投訴回應 | 致歉 + 專業  | 致歉 → 原因說明 → 補償方案 → 追蹤承諾   |
| 合作邀約     | 正式 + 友善  | 自我介紹 → 合作效益 → 具體提案 → 會議邀請 |
| 催款通知     | 正式 + 急迫  | 款項資訊 → 到期提醒 → 付款方式 → 聯繫窗口 |
```

**參考檔案（漸進式揭露，保持 SKILL.md 精簡）：**

將詳細的 prompt 模板放在 `references/prompt-templates.md`，SKILL.md 中只引用：

```markdown
## 附帶資源
- `references/prompt-templates.md` — 各情境的詳細 prompt 模板，需要產出特定情境 Email 時載入
```

### 步驟 4：驗證

```
[████████████████░░] 80% - 步驟 4/5：驗證

🔍 正在驗證 YAML 前置資料...
✅ 技能驗證通過！
```

### 步驟 5：安裝

```
[████████████████████] 100% - 步驟 5/5：安裝

您想如何安裝此技能？
→ 選擇「僅工作區」，檔案留在 .kiro/skills/email-writer/
```

### 步驟 6（選用）：進入 Eval 迭代

如果想進一步驗證品質，可以建立測試案例：

```json
{
  "skill_name": "email-writer",
  "evals": [
    {
      "id": 1,
      "prompt": "幫我寫一封回覆客戶抱怨交貨延遲的致歉信，訂單編號 A2026-0311",
      "expected_output": "包含致歉、原因說明、補償方案的結構化 Email"
    },
    {
      "id": 2,
      "prompt": "寫一封邀請 ABC 公司技術長參加產品展示會的 Email",
      "expected_output": "正式友善的合作邀約信，包含時間地點和議程"
    },
    {
      "id": 3,
      "prompt": "幫我催一下供應商的尾款，已經逾期 15 天了",
      "expected_output": "正式急迫的催款通知，包含款項資訊和付款方式"
    }
  ]
}
```

然後用 subagent 並行執行 with_skill 和 without_skill，在瀏覽器中比較結果，根據回饋迭代改進技能。

### 最終成果

經過建立和迭代後，你會得到一個能夠：
- 自動識別 Email 情境並選擇適當語氣
- 產出結構化的專業商務 Email（主旨、語氣標註、本文、CTA、署名）
- 支援多版本模式和回覆串模式
- 涵蓋客訴回應、合作邀約、催款通知等常見商務場景

的完整技能。整個過程從腦力激盪到可用技能，大約 10-15 分鐘。
