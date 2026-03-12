# 🎮 Agent Skills — GDD 自動生成器

利用 `.agent/skills/` 下的專業技能定義，搭配 Gemini API，自動產出遊戲設計文件（GDD）。

## 核心概念

```
SKILL.md（劇本）  +  Gemini API（演員）  =  GDD 自動產出
       ↑                    ↑                      ↑
  定義角色規範          執行生成任務           結構化 Markdown
```

**Skills 是「劇本」，Gemini 是「演員」，gdd_generator.py 是「導演」。**

程式從 `.agent/skills/{skill-name}/SKILL.md` 讀取技能定義，將全文注入 Prompt 作為系統指令，
讓 Gemini 按照技能規範的角色、格式、品質標準來產出內容。

## 鏈式工作流程

```
使用者輸入主題（例：火山要塞）
        │
        ▼
┌─ Step 1: @level-designer ──────────────────────┐
│  載入 .agent/skills/level-designer/SKILL.md     │
│  注入 Prompt → Gemini 產出環境設計               │
│  輸出：環境氛圍 + 三大危險要素 + 玩家目標        │
└────────────────────┬───────────────────────────┘
                     │ 上下文傳遞
                     ▼
┌─ Step 2: @character-creator ───────────────────┐
│  載入 .agent/skills/character-creator/SKILL.md  │
│  注入 Prompt + Step 1 輸出 → Gemini 產出 Boss   │
│  輸出：Boss 名稱 + 技能（對應環境危險）+ 動機    │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
┌─ Step 3: GDD 組裝 ────────────────────────────┐
│  合併 Step 1 + Step 2 → reports/GDD_{主題}.md  │
└────────────────────────────────────────────────┘
```

## 目錄結構

```
agent_skills/
├── src/
│   ├── gdd_generator.py   # 核心：鏈式 GDD 生成器（導演）
│   └── loader.py           # 技能掃描器（掃描 .agent/skills/）
├── tests/
│   ├── test_api.py         # Gemini API 連通測試
│   ├── list_models.py      # 列出可用模型
│   └── qa_validator.py     # GDD 品質校準（AI 審計）
├── reports/                # GDD 產出與品質報告
├── docs/
│   ├── agent_skills_v1.0.md         # 規格書
│   └── implementation_plan_v1.0.md  # 實作計畫
├── scripts/                # 維運腳本
└── backup/                 # 重構備份
```

## 快速開始

### 前置需求
- Python 3.12+（Windows 使用 `py` 指令）
- `.env` 設定於專案根目錄

### 1. 安裝套件
```bash
py -m pip install google-genai python-dotenv
```

### 2. 設定環境變數
根目錄 `.env`：
```env
GOOGLE_API_KEY=你的_API_金鑰
SKILL_PATH=.agent/skills
```

### 3. 驗證 API 連通
```bash
py agent_skills/tests/test_api.py
```

### 4. 掃描可用技能
```bash
py agent_skills/src/loader.py
```
預期輸出：
```
📋 獨立技能：
  🟢 character-creator
  🟢 level-designer
  🟢 skill-creator
  ...

📚 技能庫：
  📦 antigravity-awesome-skills (1223 個子技能)
```

### 5. 生成 GDD
```bash
py agent_skills/src/gdd_generator.py "火山要塞"
```
產出：`reports/GDD_火山要塞_2026-03-11.md`

### 6. 品質校準（可選）
```bash
py agent_skills/tests/qa_validator.py "火山要塞"
```

## 技能與 Gemini 的關係

| 元件 | 角色 | 職責 |
|:---|:---|:---|
| `SKILL.md` | 劇本 | 定義 AI 角色、產出規範、格式要求、品質檢核標準 |
| `Gemini API` | 演員 | 接收含技能定義的 Prompt，按規範生成內容 |
| `gdd_generator.py` | 導演 | 載入技能 → 組裝 Prompt → 呼叫 Gemini → 串接上下文 → 組裝 GDD |
| `loader.py` | 管理員 | 掃描 `.agent/skills/` 目錄，列出可用技能與技能庫 |

## 使用的技能

| 技能 | 路徑 | 用途 |
|:---|:---|:---|
| level-designer | `.agent/skills/level-designer/` | 關卡環境設計（氛圍、危險要素、玩家目標） |
| character-creator | `.agent/skills/character-creator/` | Boss 角色設計（名稱、技能、敘事動機） |
| skill-creator | `.agent/skills/skill-creator/` | 建立新技能的工具 |

## 相關文件

- [規格書](docs/agent_skills_v1.0.md)
- [實作計畫](docs/implementation_plan_v1.0.md)

---
*作者：paddyyang | 2026-03-11*

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
