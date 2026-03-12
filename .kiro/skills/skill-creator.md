---
inclusion: manual
---

# skill-creator（Kiro 技能建立器）

當使用者要求建立新的 Kiro skill 時，遵循此流程在 `.kiro/skills/` 下建立技能檔案。

## 觸發情境

- 使用者說「建立新 skill」、「新增 Kiro 技能」、「打造一個 skill」
- 使用者想要擴充 `.kiro/skills/` 技能庫
- 使用者想讓 Kiro 在特定情境下自動遵循某套流程

## Kiro Skill 是什麼

一個 `.kiro/skills/{name}.md` 檔案，用來指導 Kiro 在特定任務中如何行動。
- 單一 Markdown 檔案，不需要子目錄
- front-matter 設定注入模式（`manual` 或 `auto`）
- 使用者在對話中用 `#` 引用 manual skill

## 工作流程

### 步驟 1：需求確認

向使用者確認以下資訊：

1. **技能名稱**：kebab-case 格式（例如 `code-reviewer`）
2. **用途**：一句話描述這個 skill 要指導 Kiro 做什麼
3. **注入模式**：
   - `manual`（預設）— 使用者用 `#` 手動引用
   - `auto` — 每次對話自動載入
4. **主要步驟**：這個 skill 的工作流程有哪些關鍵步驟

### 步驟 2：建立 Skill 檔案

在 `.kiro/skills/` 下建立 `{skill-name}.md`，結構如下：

```markdown
---
inclusion: manual
---

# {skill-name}（技能中文名稱）

一句話說明此 skill 的用途。

## 觸發情境

- 列出 3-5 個使用者會說的觸發短語

## 工作流程

### 步驟 1：{步驟名稱}
{具體指引，告訴 Kiro 該做什麼}

### 步驟 2：{步驟名稱}
{具體指引}

...依此類推

## 品質標準（如適用）

| 項目 | 要求 |
|---|---|
| ... | ... |
```

### 步驟 3：驗證與完成

1. 確認檔案已建立在 `.kiro/skills/{skill-name}.md`
2. 確認 front-matter 的 `inclusion` 設定正確
3. 提醒使用者：manual skill 需在對話中用 `#` 引用才會生效

## 撰寫原則

- 精簡可操作：每個步驟都是 Kiro 可以直接執行的具體指引
- 步驟清晰：用編號步驟，避免模糊的描述
- 語言：繁體中文
- 避免冗長：skill 不是文件，是行動指南
- 一個 skill 專注一件事，不要把多個不相關的任務塞在同一個 skill 裡

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
