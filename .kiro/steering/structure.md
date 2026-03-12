---
inclusion: fileMatch
fileMatchPattern: "agent_skills/**,clawdbot/**,gemini_canvas/**,.agent/**"
# 📌 注入模式：條件注入（fileMatch）
# 📋 用途：專案架構與目錄規範
# 🎯 觸發條件：編輯教學模組或 .agent/ 下的檔案時自動載入
# ✏️ 維護：新增模組或技能時更新
---

# 專案結構

## 架構：技能定義層 + 三大教學模組

```
.agent/skills/（技能定義層）
  ├── level-designer/SKILL.md      ← 劇本
  └── character-creator/SKILL.md   ← 劇本

agent_skills/src/gdd_generator.py  ← 導演（載入劇本 → 呼叫 Gemini → 組裝產出）
```

## 目錄結構

```
.agent/
  context/                # 專案記憶與架構文件
    memory.md             # 進度追蹤
    ai_agent.md           # 系統架構規範
    agent_skills.md       # 技能歸類標準
  rules/                  # AI 編碼規範（被動載入）
    gemini.md             # Agent 執行規範
    ai_coding_standards.md # 代碼標準
    ai_coding_workflow.md  # 工作流規範
  skills/                 # 技能定義（13 個）
    character-creator/    # Boss 角色設計
    level-designer/       # 關卡環境設計
    skill-creator/        # 建立新技能的工具
    customer-support-agent/
    document-summarizer/
    email-writer/
    market-analyzer/
    marketing-copywriter/
    meeting-minutes-writer/
    presentation-writer/
    social-media-writer/
    sop-writer/
    task-planner/
  workflows/              # 標準 SOP（待建立）

agent_skills/             # 模組 1：GDD 自動生成器
  src/
    gdd_generator.py      # 鏈式生成器（導演）
    loader.py             # 技能掃描器
  tests/
    test_api.py           # API 連通測試
    qa_validator.py       # GDD 品質校準
    list_models.py        # 列出可用模型
  reports/                # GDD 產出
  docs/                   # 規格書與實作計畫

clawdbot/                 # 模組 2：Telegram Bot
  src/
    bot_main.py           # Bot 主程式
    intent_router.py      # 意圖路由
    crawler_skill.py      # 爬蟲技能
    format_utils.py       # 格式化工具
  scripts/
    init_db.py            # 資料庫初始化

gemini_canvas/            # 模組 3：視覺化儀表板
  src/
    server.py             # FastAPI 伺服器
  web/
    index.html            # 前端頁面
  data/
    data.json             # 資料來源
```

## 核心慣例

### 新增技能
1. 建立 `.agent/skills/{skill-name}/SKILL.md`
2. 可選：加入 `references/`（參考資料）、`scripts/`（輔助腳本）
3. 在 Python 腳本中用 `load_skill("{skill-name}")` 載入並注入 Prompt

### 新增教學模組
1. 建立 `{module-name}/` 頂層目錄
2. 子目錄遵循 `src/`、`tests/`、`docs/`、`reports/` 慣例
3. 更新 `product.md` 的模組表格與 `structure.md` 的目錄樹

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
