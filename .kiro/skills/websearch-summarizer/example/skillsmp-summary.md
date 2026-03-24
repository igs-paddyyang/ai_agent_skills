# SkillsMP — Agent Skills Marketplace 文件摘要

**來源**: [https://skillsmp.com](https://skillsmp.com/zh)
**版本**: v0.1.0
**授權**: 免費社群平台（非 Anthropic / OpenAI 官方）
**技能數量**: 530,778+（截至 2026-03-19 頁面顯示）
**整理日期**: 2026-03-19

---

## 一句話摘要

SkillsMP 是目前最大的 Agent Skills 聚合市集，從 GitHub 公開倉庫自動抓取並分類索引超過 53 萬個 SKILL.md 格式的 AI Agent 技能，支援 Claude Code、OpenAI Codex CLI 和 ChatGPT。

---

## 核心概念

SkillsMP 是一個獨立社群專案，透過爬蟲定期掃描 GitHub 上所有符合 SKILL.md 開放標準的倉庫，自動聚合、分類並建立搜尋索引。平台本身不託管技能程式碼，而是作為發現層（Discovery Layer），幫助開發者在海量技能中快速找到需要的能力。所有技能都遵循 Anthropic 於 2025 年 12 月發布的 Agent Skills 開放標準格式。

---

## 分類總覽

| 分類 | 技能數量 | 說明 |
|------|---------|------|
| Tools | 128,767 | 工具類技能 |
| Business | 94,216 | 商業流程 |
| Development | 92,191 | 開發與技術 |
| Data & AI | 57,298 | 資料處理與 AI |
| Testing & Security | 54,599 | 測試與安全 |
| DevOps | 48,743 | 部署與維運 |
| Documentation | 38,451 | 文件撰寫 |
| Content & Media | 35,192 | 內容與媒體 |
| Research | 18,047 | 研究類 |
| Lifestyle | 7,575 | 生活類 |
| Databases | 7,356 | 資料庫 |
| Blockchain | 5,527 | 區塊鏈 |

---

## 平台特色

| 特色 | 說明 |
|------|------|
| 智慧搜尋 | 支援 AI 語意搜尋和關鍵字搜尋 |
| 分類瀏覽 | 12 大分類，可按 Stars 或最近更新排序 |
| 品質過濾 | 最低 2 stars 門檻，掃描基本品質指標 |
| 跨平台相容 | Claude Code、OpenAI Codex CLI、ChatGPT |
| GitHub 同步 | 定期爬蟲同步，技能卡片顯示最後更新時間 |
| Manus 整合 | 與 Manus AI 合作，支援一鍵執行技能 |
| 多語言 | 支援中文（/zh）和英文（/en）介面 |

---

## 安裝方式

| 平台 | 安裝路徑 |
|------|---------|
| Claude Code（個人） | `~/.claude/skills/` |
| Claude Code（專案） | `.claude/skills/` |
| OpenAI Codex CLI | `~/.codex/skills/` |

安裝方式：從 GitHub 克隆技能倉庫，將技能資料夾複製到對應目錄。AI 會自動發現並載入。

---

## 熱門技能來源

頁面上排名靠前的技能主要來自 `openclaw/openclaw` 倉庫（318.4k stars），包含：

| 技能 | 功能 |
|------|------|
| parallels-discord-roundtrip | macOS Parallels 煙霧測試 + Discord 端對端驗證 |
| acp-router | 多 Agent 路由（Pi、Claude Code、Codex、Gemini CLI） |
| diffs | 產生可分享的 diff 檔案 |
| feishu-doc/drive/perm/wiki | 飛書文件、雲端儲存、權限、知識庫操作 |
| prose | OpenProse VM 多 Agent 工作流程 |
| 1password | 1Password CLI 設定與密碼管理 |

---

## 競品比較

| 平台 | 技能數量 | 特色 |
|------|---------|------|
| SkillsMP | 530,778+ | 最大聚合市集，免費，GitHub 爬蟲 |
| Skills.sh（Vercel） | 未知 | CLI 一鍵安裝（`npx skills add`），排行榜 |
| MCP Market Skills | 未知 | 聚焦 Claude/ChatGPT/Codex，安裝指南 |
| anthropics/skills（官方） | ~數十個 | Anthropic 官方範例 + 文件技能 |
| antigravity-awesome-skills | 1,272+ | 社群精選清單 |

---

## 與本專案的關係

| 面向 | SkillsMP | 我們的 Kiro Skills |
|------|---------|-------------------|
| 格式標準 | SKILL.md（Agent Skills 開放標準） | SKILL.md（相同格式） |
| 定位 | 技能發現與聚合平台 | 技能開發工廠（建立 / 測試 / 打包） |
| 技能來源 | GitHub 公開倉庫爬蟲 | 自行開發（skill-creator） |
| 品質控制 | 最低 2 stars + 基本掃描 | eval 測試框架 + 人工驗證 |
| 分發方式 | GitHub → SkillsMP 索引 | skill-sync（.kiro → .agent） |
| 目標平台 | Claude Code / Codex CLI / ChatGPT | Kiro IDE |

SkillsMP 是消費端（找技能用的），我們是生產端（做技能用的）。如果未來要將 Kiro Skills 發布到更廣的生態系，SkillsMP 會是一個重要的曝光管道。

---

## 行動建議

1. 在 SkillsMP 上搜尋與我們 10 個技能同類的技能，了解市場上的競品實作方式和品質水準
2. 考慮將成熟的 Kiro Skills（如 gemini-canvas-dashboard v1.0.0）發布到 GitHub 公開倉庫，讓 SkillsMP 自動索引
3. 研究 SkillsMP 的分類體系（12 大類），評估是否適合作為我們技能分類的參考標準
4. 關注 Manus AI 的一鍵執行整合模式，評估類似的「技能即服務」分發方式是否適用於 ArkBot
