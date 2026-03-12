---
# 作者: paddyyang
# 最後修改日期: 2026-03-12
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
backgroundImage: url('linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)')
header: 'AI Agent Skills Workshop | 2026'
footer: '© 2026 paddyyang | Confidential & Proprietary'
style: |
  section {
    font-family: 'Inter', 'Segoe UI', 'Microsoft JhengHei', sans-serif;
    color: #2d3436;
  }
  h1 {
    color: #0984e3;
    font-size: 2.5em;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
  }
  h2 {
    color: #6c5ce7;
    border-bottom: 3px solid #6c5ce7;
    padding-bottom: 10px;
  }
  code {
    background: #2d3436;
    color: #fab1a0;
    padding: 2px 8px;
    border-radius: 4px;
  }
  blockquote {
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(10px);
    border-left: 10px solid #0984e3;
    padding: 20px;
    border-radius: 0 15px 15px 0;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
  }
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }
  .card {
     background: rgba(255, 255, 255, 0.6);
     backdrop-filter: blur(8px);
     padding: 20px;
     border-radius: 15px;
     border: 1px solid rgba(255, 255, 255, 0.3);
     box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  }
---

<!-- _class: lead -->
<!-- _backgroundImage: linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.55)), url('./images/hero.png') -->
<!-- _backgroundSize: cover -->
<!-- _color: white -->
<!-- _header: '' -->
<!-- _footer: '' -->

# AI Agent Skills Workshop
### 從 Prompt 到 CLI 自動化與 Agent 工作流

**講師：paddyyang**
*2026 AI 技術工作坊*

---

## 🎯 本次工作坊目標
#### 讓你掌握從「對話」到「自動化」的核心路徑

- **掌握核心概念**：理解 AI Skill 與一般 Prompt 的差異
- **動手實作**：建立屬於自己的可重複使用技能庫
- **工具化能力**：學會使用 CLI 自動化簡報生成流程
- **架構思維**：設計簡單且高效的 AI Agent 工作流 (Workflow)

---

## 🚀 AI 應用的三個演進階段
#### 從被動回覆到主動完成任務

![bg right:40% contain](./images/evolution.png)

<div class="columns">
<div class="card">

### 1. Prompt (提詞)
單純與 AI 對話，依賴單次輸入與情境。
</div>

<div class="card">

### 2. Tool (工具化)
AI 開始具備「雙手」，能操作 API、CLI 或資料庫。
</div>

<div class="card">

### 3. Agent (代理人)
具備自主規劃、決策與自我修正能力的系統。
</div>
</div>

---

## ⚠️ 單純 Prompt 的侷限性
#### 為什麼我們需要「技能化 (Skill-ized)」？

> [!CAUTION]
> **碎片化 (Fragmentation)**: 無法在不同專案間輕鬆共享。
> **不可控 (Inherit Risk)**: 輸出格式隨機，難以被程式解析。
> **低效率 (Low Reuse)**: 每次都要重複寫背景與規則。

---

## 💡 什麼是 AI Skill？
#### 定義：可重複使用的「智能模組」

AI Skill = **[ Role + Context + Task + Rules + Constraints ]**

- **封裝性**：將複雜流程打包成一個簡單指令
- **標準化**：統一輸出 JSON 或 Markdown 等機器可讀格式
- **組合性**：可以像樂高一樣被 Agent 呼叫

---

## 🏗️ AI Skill 的標準結構
#### 以 `level-designer/SKILL.md` 為例

```markdown
# SKILL.md — 關卡設計師
- **Role**: 資深遊戲關卡設計師
- **Context**: 根據主題設計遊戲關卡環境
- **Task**: 產出環境氛圍、三大危險要素、玩家目標
- **Rules**: 繁體中文、Markdown 格式、含設計理由
- **Output**: 結構化 Markdown，供下游 character-creator 接續
```

---

## 📚 建立你的技能庫 (Skill Library)
#### 本專案已有 13 個技能定義

<div class="columns">
<div>

- 🎮 `character-creator`、`level-designer`
- 📝 `document-summarizer`、`sop-writer`
- 📧 `email-writer`、`social-media-writer`
- 📊 `market-analyzer`、`marketing-copywriter`

</div>
<div class="card">

#### 優勢
<span style="font-size:0.85em">

1. **一致性**：跨團隊輸出風格統一
2. **可維護性**：改一行規則，所有 Agent 同步更新
3. **可測試性**：用 `qa_validator.py` 進行 AI 審計

</span>

</div>
</div>

---

## 🛠️ Skill → CLI Automation
#### 當技能遇上命令列工具：GDD 自動生成器

AI Skill 提供「腦力」，CLI 提供「體力」。本專案的真實案例：

```bash
# 一行指令，自動產出遊戲設計文件
py agent_skills/src/gdd_generator.py "火山要塞"
```

---

## 🛠️ Skill → CLI Automation
#### 運作原理（Skill-First 模式）：
1. `gdd_generator.py`（導演）載入 `.agent/skills/level-designer/SKILL.md`
2. 將技能定義注入 Prompt → Gemini 產出環境設計
3. 再載入 `character-creator/SKILL.md` + 上一步輸出 → 產出 Boss 設計
4. 組裝為 `reports/GDD_火山要塞_2026-03-11.md`

---

## 📐 本課程 Demo 架構
#### 鏈式 GDD 生成的運行邏輯

![w:800 GDD 鏈式生成流程](./images/gdd_flow.png)

每一步都是：載入 SKILL.md → 注入 Prompt → Gemini 生成 → 傳遞上下文

---

## 📂 專案結構
#### 本工作坊的實際目錄結構

```bash
.agent/skills/                    # 技能定義層（劇本）
├── level-designer/SKILL.md       # 關卡環境設計
├── character-creator/SKILL.md    # Boss 角色設計
└── ... (共 13 個技能)

agent_skills/                     # 模組 1：GDD 自動生成器
├── src/
│   ├── gdd_generator.py          # 鏈式生成器（導演）
│   └── loader.py                 # 技能掃描器
├── tests/
│   └── qa_validator.py           # 品質校準（AI 審計）
└── reports/                      # GDD 產出
```

---

## ⚡ 實戰示範：GDD 自動生成
#### 從主題到遊戲設計文件，僅需一個指令

<div class="card">

### 操作步驟
1. **輸入主題**：`"火山要塞"`
2. **Step 1 — @level-designer**：Gemini 根據技能定義產出環境設計（氛圍、危險要素、玩家目標）
3. **Step 2 — @character-creator**：接收環境上下文，產出 Boss 設計（名稱、技能、動機）
4. **GDD 組裝**：合併兩步產出 → `reports/GDD_火山要塞_2026-03-11.md`

</div>

---

## 🛠️ Step-by-Step CLI 指令

```bash
# 0. 測試 API 連通與可用模型
py agent_skills/tests/list_models.py

# 1. 掃描可用技能（確認 level-designer、character-creator 已就緒）
py agent_skills/src/loader.py

# 2. 生成 GDD（鏈式：level-designer → character-creator → 組裝）
py agent_skills/src/gdd_generator.py "火山要塞"

# 3. 品質校準（AI 審計：檢查 Boss 技能是否對齊環境危險要素）
# 產出：reports/qa_analysis_火山要塞_2026-03-12.md
py agent_skills/tests/qa_validator.py "火山要塞"
```

---

## 🧠 設計高品質 Skill 的秘訣（1/2）
#### 讓 SKILL.md 成為 AI 的精準劇本

<div class="columns">
<div class="card">

#### 1. 定義邊界（Constraints）
明確告訴 AI「什麼不要做」

<small>📌 `level-designer`：「不要設計角色，只負責環境與危險要素」</small>

</div>
<div class="card">

#### 2. 結構化輸出（Output Format）
<small>指定 Markdown / JSON 格式，讓下游程式可解析

📌 `character-creator`：「輸出必須含 Boss 名稱、技能列表、敘事動機」</small>

</div>
</div>

---

## 🧠 設計高品質 Skill 的秘訣（2/2）


<div class="columns">
<div class="card">

#### 3. 上下文注入（Context Passing）
<small>前一步的輸出作為下一步的輸入，確保邏輯一致

📌 `gdd_generator`：level-designer 的「三大危險要素」→ character-creator 的 Boss 技能設計依據</small>

</div>
<div class="card">

#### 4. 品質檢核（Quality Checklist）
<small>在 SKILL.md 末尾加入自我檢查清單

📌 `qa_validator`：「Boss 技能是否對齊環境危險要素？火山地圖的 Boss 不該有冰凍攻擊」</small>

</div>
</div>

---

## 🤖 Agent Workflow 深度解析
#### 什麼才是真正的「代理人」？以 ClawdBot 為例

<div class="columns">
<div class="card">

#### 傳統腳本
<small> 
輸入 A → 產出 B（固定邏輯）
</small> 
</div>

<div class="card">

#### ClawdBot（本專案實例）
<small> 
使用者訊息 → **Gemini 意圖路由** → 判斷 RESEARCH / CASUAL → **選取技能**（爬蟲 / 閒聊）→ **執行** → **格式化回傳**
</small> 
</div>
</div>

```bash
# 啟動 ClawdBot（需設定 TELEGRAM_TOKEN）
py clawdbot/src/bot_main.py
```

---

## 🏢 企業級應用場景
#### 本專案技能庫的延伸應用

- **自動週報**：用 `document-summarizer` 技能讀取資料，自動生成結構化摘要
- **客戶服務**：用 `customer-support-agent` 技能，根據產品手冊即時回覆
- **數據儀表板**：用 `gemini_canvas` 模組，FastAPI + HTML 即時視覺化

---

## ✍️ 實作練習（1/3）：建立你的第一個 Skill
#### Step 1 — 建立技能目錄與 SKILL.md

<small>

任務：建立 `marketing-pro` 技能，讓 AI 能根據產品名稱產出「痛點分析報告」。

```bash
# 建立技能目錄
mkdir .agent/skills/marketing-pro
```

在 `.agent/skills/marketing-pro/SKILL.md` 中填入以下內容：
`./agent_skills/docs/marketing-pro.md` 的內容

AI對話 : 建立 `marketing-pro` 技能，讓 AI 能根據產品名稱產出「痛點分析報告」，使用skill-creator建立，並套用'./agent_skills/docs/marketing-pro.md'的內容。

</small>

---

## ✍️ 實作練習（2/3）：驗證與測試
#### Step 2 — 確認技能被掃描到，並進行簡單測試

```bash
# 掃描技能庫，確認 marketing-pro 出現在清單中
py agent_skills/src/loader.py
```

預期輸出：
```
📋 獨立技能：
  🟢 marketing-copywriter
  🟢 marketing-pro        ← 你剛建立的技能
  🟢 meeting-minutes-writer
  ...
```
---

接著用 Python 快速測試技能是否能被 Gemini 正確執行：

<small>

```python
# 存為 agent_skills/tests/test_marketing.py，進行測試
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# 載入你的技能定義
with open(".agent/skills/marketing-pro/SKILL.md", "r", encoding="utf-8") as f:
    skill_prompt = f.read()

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"{skill_prompt}\n\n請針對產品「AI 寫作助手」進行痛點分析。"
)
print(response.text)
```
</small>

---

## ✍️ 實作練習（3/3）：進階挑戰 🏆
#### Step 3 — 修改規則，觀察產出差異

<div class="columns">
<div class="card">

### 挑戰 A：調整 Rules
修改 `SKILL.md` 的產出規範：
- 把痛點數量從 3 改為 5
- 加入「競品對比」欄位
- 重新執行，觀察產出變化

</div>
<div class="card">

### 挑戰 B：鏈式串接
嘗試將 `marketing-pro` 的輸出，餵給 `email-writer` 技能：
1. 先產出痛點分析
2. 將分析結果作為上下文
3. 讓 `email-writer` 產出對應的行銷信件

</div>
</div>

> 💡 這就是 Agent Skills 的核心威力：**改一行規則，產出全面升級；串接兩個技能，能力指數成長。**

---

## 🏁 結語：從 AI 工具人到 AI 建築師
#### 掌握核心，主導自動化浪潮

- **Prompt** 是溝通的起點
- **Skill** 是能力的封裝
- **Tool** 是身體的延伸
- **Workflow** 是靈魂的佈排

**現在，開始建立你的第一項 AI Skill 吧！**

---

<!-- _class: lead -->

# Q&A / 實作交流
#### 讓我們一起把想法變成自動化工具

> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
