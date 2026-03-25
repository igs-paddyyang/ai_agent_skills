---
name: skill-creator
description: "建立新技能、修改與改進現有技能、量測技能效能。當使用者想要從零建立技能、編輯或優化現有技能、執行 eval 測試技能、以變異數分析進行效能基準測試、或優化技能描述以提升觸發準確度時，請使用此技能。"
---

# 技能建立器（Skill Creator）

一個用於建立新技能並迭代改進的技能。

## 整體流程

高層次來看，建立技能的流程如下：

- 決定技能要做什麼，以及大致的實作方式
- 撰寫技能草稿
- 建立幾個測試提示詞，用帶有技能的 agent 執行
- 協助使用者定性與定量評估結果
  - 在背景執行測試的同時，草擬定量 eval（若已有則審閱或修改）。向使用者說明
  - 使用 `eval-viewer/generate_review.py` 腳本展示結果供使用者檢視
- 根據使用者的評估回饋重寫技能（也根據定量基準測試中明顯的缺陷）
- 重複直到滿意
- 擴大測試集，再次嘗試更大規模

你的工作是判斷使用者目前在這個流程的哪個階段，然後跳入協助他們推進。例如，使用者可能說「我想做一個 X 技能」，你可以協助釐清意圖、撰寫草稿、撰寫測試案例、決定評估方式、執行所有提示詞，然後重複。

另一方面，使用者可能已經有技能草稿。這種情況可以直接進入 eval/迭代的部分。

當然，保持彈性——如果使用者說「我不需要跑一堆評估，跟我一起 vibe 就好」，那就照做。

技能完成後（順序可彈性調整），也可以執行技能描述優化器來優化觸發效果。

## 與使用者溝通

技能建立器的使用者可能涵蓋各種程式素養程度。請注意上下文線索來調整溝通方式：

- 「evaluation」和「benchmark」屬於邊界用語，但可以使用
- 「JSON」和「assertion」需要先確認使用者理解再使用
- 有疑慮時簡短解釋術語即可

---

## 第一部分：快速建立技能

### 進度追蹤

在整個工作流程中，於每個階段開始前顯示視覺化進度條：

```
[████████████░░░░░░] 60% - 步驟 3/5：建立 SKILL.md
```

### 階段 1：意圖捕捉與腦力激盪（20%）

```
[████░░░░░░░░░░░░░░] 20% - 步驟 1/5：腦力激盪與規劃
```

先理解使用者的意圖。如果對話中已包含使用者想捕捉的工作流程（例如「把這個變成技能」），先從對話歷史中提取答案。

需要釐清的問題：
1. 這個技能要讓 AI 做什麼？
2. 何時應該觸發？（什麼使用者短語/情境）
3. 預期的輸出格式是什麼？
4. 是否需要設定測試案例？（有客觀可驗證輸出的技能適合測試案例；主觀輸出的技能通常不需要）

主動詢問邊界案例、輸入/輸出格式、範例檔案、成功標準和依賴項。

### 階段 2：提詞增強（40%，選用）

```
[████████░░░░░░░░░░] 40% - 步驟 2/5：提詞增強
```

詢問使用者是否要使用 prompt-engineer 技能來精煉技能描述。若選擇是，調用後與使用者一起審閱增強後的輸出。

### 階段 3：檔案產生（60%）

```
[████████████░░░░░░] 60% - 步驟 3/5：檔案產生
```

#### 技能安裝路徑偵測

根據工作區環境自動決定技能的建立位置：

| 條件 | 安裝路徑 | 說明 |
|------|---------|------|
| 存在 `.kiro/` 目錄 | `.kiro/skills/` | 研發系統（使用 Kiro IDE 開發技能） |
| 僅存在 `.agent/skills/` | `.agent/skills/` | 正式環境（無 Kiro IDE，技能直接部署使用） |

偵測優先順序：`.kiro/skills/` > `.agent/skills/`。使用者也可透過 `--path` 參數手動指定。

可使用初始化腳本快速建立骨架：

```bash
# 自動偵測路徑（優先 .kiro/skills/，fallback 到 .agent/skills/）
python scripts/init_skill.py <skill-name>

# 手動指定路徑
python scripts/init_skill.py <skill-name> --path .kiro/skills
python scripts/init_skill.py <skill-name> --path .agent/skills
```

或手動建立。產生的技能結構：

```
<skills-path>/your-skill-name/
├── SKILL.md              # 主要技能指令
├── README.md             # 技能說明文件（含版本號與變更紀錄）
├── references/           # 詳細指南
├── scripts/              # 可執行腳本
└── assets/               # 範本、圖片等
```

#### 撰寫 SKILL.md

根據使用者訪談，填入以下組件：

- **name**：技能識別碼（kebab-case）
- **description**：何時觸發、做什麼。這是主要觸發機制——同時包含技能功能和使用情境。為了對抗「觸發不足」的傾向，描述應稍微「積極」一些。例如，不要寫「建立簡單的資料儀表板」，而是寫「建立簡單的資料儀表板。當使用者提到儀表板、資料視覺化、內部指標，或想要顯示任何類型的資料時，請務必使用此技能。」
- **compatibility**：所需工具、依賴項（選用，很少需要）

#### 技能結構

```
skill-name/
├── SKILL.md（必要）
│   ├── YAML 前置資料（name、description 必要）
│   └── Markdown 指令
├── README.md（必要）
│   ├── 版本資訊表格
│   ├── 功能說明
│   ├── 使用方式
│   ├── 檔案結構
│   └── 變更紀錄
└── 附帶資源（選用）
    ├── scripts/    - 確定性/重複性任務的可執行程式碼
    ├── references/ - 按需載入上下文的文件
    └── assets/     - 用於輸出的檔案（範本、圖示、字型）
```

#### 撰寫 README.md

每個技能都必須包含 README.md，作為技能的對外說明文件。README 使用 `templates/readme.md` 範本產生，包含以下必要區塊：

1. **版本資訊表格** — 以表格呈現版本號、建立日期、最後更新、平台、語言
2. **功能說明** — 簡述技能的核心功能
3. **使用方式** — 列出觸發語句範例
4. **檔案結構** — 技能的目錄結構
5. **變更紀錄** — 以 Semantic Versioning 記錄每次變更

#### 版本號管理

技能採用 [Semantic Versioning](https://semver.org/) 管理版本，格式為 `MAJOR.MINOR.PATCH`：

| 版本位 | 何時遞增 | 範例 |
|--------|---------|------|
| MAJOR | 技能行為有不相容的重大變更（如觸發條件大改、輸出格式變更） | 1.0.0 → 2.0.0 |
| MINOR | 新增功能或擴充支援場景，向下相容 | 1.0.0 → 1.1.0 |
| PATCH | 修正錯誤、調整措辭、小幅優化 | 1.0.0 → 1.0.1 |

版本號規則：
- 新建技能從 `0.1.0` 開始（表示初始開發階段）
- 經過 eval 測試驗證穩定後，升級為 `1.0.0`
- 每次修改技能時，必須同步更新 README.md 中的：
  - 版本資訊表格中的「版本」和「最後更新」
  - 變更紀錄區塊，新增對應版本的條目
- 變更紀錄格式：`### vX.Y.Z（YYYY-MM-DD）` + 變更項目列表

#### 漸進式揭露

技能使用三層載入系統：
1. **中繼資料**（name + description）— 永遠在上下文中（~100 字）
2. **SKILL.md 本體** — 技能觸發時載入（理想 <500 行）
3. **附帶資源** — 按需載入（無限制，腳本可不載入直接執行）

關鍵模式：
- SKILL.md 保持在 500 行以內；接近上限時，增加層次結構並提供明確指引
- 從 SKILL.md 清楚引用參考檔案，說明何時讀取
- 大型參考檔案（>300 行）包含目錄

#### 寫作風格

指令偏好使用祈使句形式。試著解釋事情為什麼重要，而非堆砌嚴格的 MUST。運用心智理論，讓技能通用而非過度針對特定範例。先寫草稿，再以新鮮眼光審視改進。

#### 無意外原則

技能不得包含惡意軟體、漏洞利用程式碼或任何可能危害系統安全的內容。技能的內容在描述時不應讓使用者感到意外。

### 階段 4：驗證（80%）

```
[████████████████░░] 80% - 步驟 4/5：驗證
```

執行驗證腳本（路徑依偵測結果而定）：

```bash
python scripts/quick_validate.py <skills-path>/<skill-name>
```

驗證項目：YAML 前置資料格式、必要欄位、名稱格式（kebab-case）、描述長度（上限 1024 字元）、允許的屬性白名單。

### 階段 5：安裝（100%）

```
[████████████████████] 100% - 步驟 5/5：安裝
```

詢問使用者安裝方式：
- **僅工作區** — 檔案在 `.kiro/skills/`（在此工作區使用）
- **全域安裝** — 在 `~/.kiro/skills/` 建立符號連結（任何地方都可使用）
- **兩者皆是**（建議）

完成後顯示摘要，包含建立的檔案清單（含 README.md 版本號）和後續步驟。

---

## 第二部分：測試與迭代

### 測試案例

撰寫技能草稿後，想出 2-3 個真實的測試提示詞。與使用者分享：「這裡有幾個我想嘗試的測試案例，看起來對嗎？還是你想加更多？」然後執行。

將測試案例儲存到 `evals/evals.json`。先不寫 assertion——只寫提示詞。在執行期間再草擬 assertion。

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "使用者的任務提示詞",
      "expected_output": "預期結果描述",
      "files": []
    }
  ]
}
```

完整 schema 請參閱 `references/schemas.md`。

### 執行與評估測試案例

將結果放在 `<skill-name>-workspace/`，與技能目錄同層。在工作區內按迭代組織（`iteration-1/`、`iteration-2/` 等），每個測試案例一個目錄（`eval-0/`、`eval-1/` 等）。

#### 步驟 1：同時啟動所有執行（with-skill 和 baseline）

對每個測試案例，在同一輪啟動兩個 subagent——一個帶技能，一個不帶。同時啟動所有執行，讓它們大約同時完成。

#### 步驟 2：執行期間草擬 assertion

不要只等執行完成——利用這段時間草擬定量 assertion 並向使用者說明。好的 assertion 是客觀可驗證的，且有描述性名稱。

#### 步驟 3：執行完成時捕捉計時資料

當 subagent 任務完成時，將 `total_tokens` 和 `duration_ms` 儲存到 `timing.json`。

#### 步驟 4：評分、聚合、啟動檢視器

1. **評分** — 啟動 grader subagent，讀取 `agents/grader.md` 評估每個 assertion。結果存到 `grading.json`。
2. **聚合** — 執行聚合腳本：
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
3. **分析** — 讀取 benchmark 資料，找出聚合統計可能隱藏的模式。參閱 `agents/analyzer.md`。
4. **啟動檢視器**：
   ```bash
   python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json
   ```
   無顯示環境時使用 `--static <output_path>` 產生獨立 HTML。

#### 步驟 5：讀取回饋

使用者完成後，讀取 `feedback.json`。空回饋表示使用者認為沒問題。專注改進有具體抱怨的測試案例。

### 改進技能

這是循環的核心。改進思路：

1. **從回饋中泛化** — 不要過度擬合特定範例，而是泛化到更廣泛的使用者意圖類別
2. **保持精簡** — 移除沒有貢獻的部分。閱讀逐字稿，不只是最終輸出
3. **解釋為什麼** — 解釋每個指令背後的原因，而非堆砌嚴格的 MUST/NEVER
4. **尋找重複工作** — 如果所有測試案例都獨立寫了類似的腳本，那就把它打包進 `scripts/`

改進後：重新執行所有測試案例到新的 `iteration-<N+1>/` 目錄，啟動檢視器，等待使用者審閱，重複。

每次改進技能後，記得更新 README.md 的版本號與變更紀錄。根據改動幅度選擇遞增 MAJOR、MINOR 或 PATCH。

---

## 第三部分：進階功能

### 盲測比較

需要更嚴格比較兩個版本時，使用盲測比較系統。詳見 `agents/comparator.md` 和 `agents/analyzer.md`。

### 描述優化

description 欄位是決定技能是否被觸發的主要機制。詳細流程：

1. **產生觸發 eval 查詢** — 建立 20 個 eval 查詢（should-trigger 和 should-not-trigger 混合）
2. **與使用者審閱** — 使用 `assets/eval_review.html` 模板展示
3. **執行優化循環**：
   ```bash
   python -m scripts.run_loop \
     --eval-set <path-to-trigger-eval.json> \
     --skill-path <path-to-skill> \
     --model <model-id> \
     --max-iterations 5 \
     --verbose
   ```
4. **套用結果** — 將 `best_description` 更新到 SKILL.md 前置資料

### 打包與發布

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

---

## 附帶資源

### agents/
- `agents/grader.md` — 如何評估 assertion 與輸出
- `agents/comparator.md` — 如何進行盲測 A/B 比較
- `agents/analyzer.md` — 如何分析為什麼某版本勝出

### references/
- `references/schemas.md` — evals.json、grading.json、benchmark.json 等的 JSON 結構
- `references/output-patterns.md` — 輸出模式指南
- `references/workflows.md` — 工作流程模式指南

### scripts/
- `scripts/init_skill.py` — 從範本初始化新技能
- `scripts/quick_validate.py` — 快速驗證技能結構
- `scripts/package_skill.py` — 打包為可分發的 .skill 檔案
- `scripts/run_eval.py` — 觸發率測試
- `scripts/run_loop.py` — eval + improve 自動迭代循環
- `scripts/aggregate_benchmark.py` — benchmark 統計聚合
- `scripts/generate_report.py` — HTML 報告生成
- `scripts/improve_description.py` — 描述優化
- `scripts/utils.py` — 共用工具函式

---

核心循環重申：

- 搞清楚技能是關於什麼的
- 草擬或編輯技能
- 用帶有技能的 agent 執行測試提示詞
- 與使用者一起評估輸出
- 重複直到滿意
- 打包最終技能
