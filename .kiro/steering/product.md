---
inclusion: always
# 📌 注入模式：永遠自動注入
# 📋 用途：產品定位與核心概念，讓 AI 了解這個專案是什麼
# ✏️ 維護：新增教學模組或功能時更新
---

# 產品：AI Agent Skills Workshop（AI 代理技能工作坊）

本專案是一個 AI Agent 開發教學工作坊，透過實作三大模組，展示如何利用 `.agent/skills/` 技能定義搭配 Gemini API 進行自動化內容生成。

## 核心概念

```
SKILL.md（劇本）  +  Gemini API（演員）  =  自動化產出
```

Skills 定義 AI 的角色與規範，Gemini 負責執行生成，Python 腳本負責編排流程。

## 三大教學模組

| 模組 | 路徑 | 說明 |
|---|---|---|
| Agent Skills | `agent_skills/` | 鏈式 GDD 自動生成器（level-designer → character-creator → 組裝） |
| ClawdBot | `clawdbot/` | Telegram Bot，含智慧意圖路由與爬蟲技能 |
| Gemini Canvas | `gemini_canvas/` | FastAPI 資料儀表板，HTML 視覺化渲染 |

## 技能庫

`.agent/skills/` 下有 13 個技能定義，涵蓋遊戲設計、文件撰寫、行銷文案等領域。每個技能包含 `SKILL.md` 定義檔，部分附帶 `references/` 參考資料。

## 目標受眾

學習 AI Agent 開發的開發者，透過實作理解「技能定義驅動 LLM 生成」的模式。

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
