
設計目標：
讓學員從 **Prompt → Skill → CLI → Automation → Agent Workflow** 完整理解。

---

# AI Agent Skills Workshop（2 小時版投影片）

---

# Slide 1 — Title

**AI Agent Skills Workshop**

Build AI Automation Tools with CLI and Skills

內容：

* AI Skills
* CLI Automation
* AI Workflow
* Agent Thinking

---

# Slide 2 — Workshop Goal

本課程你將學會

* 什麼是 AI Skill
* 如何建立 Skill
* 如何使用 CLI 自動化
* 如何把 AI 變成工具
* 如何設計簡單 Agent Workflow

---

# Slide 3 — AI 的三個階段

AI 應用演進

```
Prompt
↓
Tool
↓
Agent
```

說明：

* Prompt：與 AI 對話
* Tool：AI 使用工具
* Agent：AI 自動完成任務

---

# Slide 4 — Prompt 的限制

單純 Prompt 的問題：

* 無法重複使用
* 無法標準化
* 無法整合工具
* 無法建立流程

所以需要：

```
AI Skill
```

---

# Slide 5 — 什麼是 AI Skill

AI Skill 是：

```
Reusable Prompt
```

可以被

* AI
* Agent
* Workflow

重複使用。

---

# Slide 6 — Skill Concept

Skill 的結構

```
Role
Task
Rules
Output Format
```

範例：

```
Role: marketing expert
Task: generate campaign ideas
Rules: short and clear
```

---

# Slide 7 — Skill Library

當 Skill 變多時

```
skills/
   email-writer
   slide-generator
   report-writer
```

就形成：

```
Skill Library
```

---

# Slide 8 — Skill → Tool

AI Skill 可以搭配工具

```
Skill
 ↓
Tool
 ↓
Output
```

例如：

```
AI → CLI → PPT
```

---

# Slide 9 — CLI Automation

CLI 是什麼？

Command Line Interface

例子：

```
python main.py generate outline.md
```

功能：

```
Markdown → PowerPoint
```

---

# Slide 10 — Automation Concept

Automation 流程

```
Input
 ↓
Process
 ↓
Output
```

AI 可以負責：

```
Process
```

---

# Slide 11 — Demo Architecture

本課程 Demo 架構

```
User
 ↓
AI
 ↓
Skill
 ↓
CLI Tool
 ↓
PowerPoint
```

---

# Slide 12 — Demo Project Structure

專案結構

```
ai-agent-workshop

ai_cli/
skills/
examples/
outputs/
```

---

# Slide 13 — Outline Format

我們用 Markdown 定義簡報

```
# Title

## Slide Title
Bullet
Bullet
Bullet
```

優點：

* 簡單
* 可版本管理
* AI 容易生成

---

# Slide 14 — CLI Demo

生成 PPT

```
python main.py generate examples/outline.md
```

輸出：

```
outputs/presentation.pptx
```

---

# Slide 15 — AI Automation

AI 生成簡報流程

```
Topic
 ↓
AI Outline
 ↓
CLI
 ↓
PPT
```

---

# Slide 16 — AI Command

指令：

```
python main.py ai "AI Agent Introduction"
```

流程：

```
Topic
 ↓
AI
 ↓
Outline
 ↓
Slides
```

---

# Slide 17 — Create Skill

建立 Skill

```
skills/my-skill/
```

裡面包含：

```
SKILL.md
```

---

# Slide 18 — Skill Example

範例

```
Role:
You are a presentation expert

Task:
Create a presentation outline

Rules:
Each slide has 3 bullets
```

---

# Slide 19 — Agent Workflow

Agent 的基本流程

```
User Request
 ↓
Planner
 ↓
Skill
 ↓
Tools
 ↓
Result
```

---

# Slide 20 — Real World Use Cases

企業常見 AI Skill

* Email Writer
* Report Generator
* Slide Creator
* Meeting Summary
* Data Analyzer

---

# Slide 21 — Lab Exercise

實作題目

建立 AI 簡報

Topic：

```
AI for Marketing
```

---

# Slide 22 — Lab Command

執行：

```
python main.py ai "AI for Marketing"
```

結果：

```
AI 自動生成簡報
```

---

# Slide 23 — Key Takeaway

最重要概念

```
Prompt
 ↓
Skill
 ↓
Tool
 ↓
Automation
 ↓
Agent
```

---

# Slide 24 — Next Step

可以進一步學習：

* Workflow Automation
* AI Agents
* Skill Libraries
* Enterprise AI Tools

---

# 建議投影片數量

| 課程長度 | 投影片    |
| ---- | ------ |
| 90分鐘 | 15頁    |
| 2小時  | 20~25頁 |

這份 **24頁剛好適合 2 小時課程**。

---

