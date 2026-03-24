---
name: changelog-generator
description: "從 git commits 自動產生結構化的變更紀錄（changelog），支援 Conventional Commits 格式解析、版本號自動推導與 Markdown 輸出。可整合到 README.md 的變更紀錄區塊。當使用者提到 changelog、變更紀錄、更新日誌、release notes、版本紀錄、git log 整理、產生 changelog、自動 changelog、版本號推導、conventional commits 時，請務必使用此技能。"
---

# 變更紀錄產生器（Changelog Generator）

手動維護 changelog 很痛苦，而且容易忘記。
這份指引幫你從 git commits 自動產生結構化的變更紀錄。

## 使用時機

- 需要產生專案的 changelog
- 需要整理 git log 為可讀格式
- 準備發布新版本，需要 release notes
- 需要更新 README.md 的變更紀錄區塊
- 需要推導下一個版本號

## 核心流程

```
git log → 解析 commits → 分類 → 產生 Markdown → 輸出
```

## Conventional Commits 格式

每個 commit 訊息遵循以下格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Type 分類

| Type | 說明 | Changelog 分類 | 版本影響 |
|------|------|---------------|---------|
| feat | 新功能 | ✨ 新功能 | MINOR |
| fix | Bug 修復 | 🐛 修復 | PATCH |
| docs | 文件更新 | 📝 文件 | — |
| refactor | 重構 | ♻️ 重構 | — |
| perf | 效能改善 | ⚡ 效能 | PATCH |
| test | 測試 | 🧪 測試 | — |
| chore | 雜務 | 🔧 維護 | — |
| style | 格式調整 | 💄 樣式 | — |
| ci | CI/CD | 👷 CI | — |
| build | 建置 | 📦 建置 | — |

### Breaking Change

在 footer 加上 `BREAKING CHANGE:` 或在 type 後加 `!`：

```
feat!: 重新設計 API 介面

BREAKING CHANGE: /api/v1/users 改為 /api/v2/users，回傳格式變更
```

Breaking Change → MAJOR 版本升級。

## 版本號推導規則

基於 Semantic Versioning（MAJOR.MINOR.PATCH）：

```
有 BREAKING CHANGE → MAJOR + 1（x.0.0）
有 feat           → MINOR + 1（0.x.0）
只有 fix/perf     → PATCH + 1（0.0.x）
其他              → 不升版
```

### 推導範例

```
目前版本：1.2.3

commits:
- feat: 新增使用者搜尋功能
- fix: 修復登入逾時問題
- docs: 更新 API 文件

→ 有 feat → MINOR + 1 → 1.3.0
```

```
目前版本：1.2.3

commits:
- feat!: 重新設計認證流程

→ 有 BREAKING CHANGE → MAJOR + 1 → 2.0.0
```

## 產生 Changelog 的步驟

### 步驟 1：取得 git log

```bash
# 取得上次 tag 到現在的 commits
git log v1.2.3..HEAD --oneline

# 取得所有 commits（無 tag 時）
git log --oneline

# 取得詳細格式
git log --format="%H|%s|%an|%ai" v1.2.3..HEAD
```

### 步驟 2：解析 commits

將每個 commit 訊息解析為結構化資料：

```python
import re

PATTERN = r'^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<desc>.+)$'

def parse_commit(message: str) -> dict | None:
    match = re.match(PATTERN, message)
    if not match:
        return None
    return {
        "type": match.group("type"),
        "scope": match.group("scope"),
        "breaking": bool(match.group("breaking")),
        "description": match.group("desc"),
    }
```

### 步驟 3：分類與排序

```python
CATEGORY_ORDER = ["feat", "fix", "perf", "refactor", "docs", "test", "chore"]
CATEGORY_EMOJI = {
    "feat": "✨ 新功能",
    "fix": "🐛 修復",
    "perf": "⚡ 效能",
    "refactor": "♻️ 重構",
    "docs": "📝 文件",
    "test": "🧪 測試",
    "chore": "🔧 維護",
}

def group_commits(commits: list[dict]) -> dict[str, list]:
    groups = {}
    for commit in commits:
        category = commit["type"]
        groups.setdefault(category, []).append(commit)
    return groups
```

### 步驟 4：產生 Markdown

```python
def generate_changelog(version: str, date: str, groups: dict) -> str:
    lines = [f"## {version}（{date}）\n"]

    # Breaking Changes 優先
    breaking = [c for commits in groups.values() for c in commits if c["breaking"]]
    if breaking:
        lines.append("### ⚠️ Breaking Changes\n")
        for commit in breaking:
            lines.append(f"- {commit['description']}")
        lines.append("")

    # 按分類輸出
    for category in CATEGORY_ORDER:
        commits = groups.get(category, [])
        non_breaking = [c for c in commits if not c["breaking"]]
        if non_breaking:
            emoji = CATEGORY_EMOJI.get(category, category)
            lines.append(f"### {emoji}\n")
            for commit in non_breaking:
                scope = f"**{commit['scope']}**: " if commit["scope"] else ""
                lines.append(f"- {scope}{commit['description']}")
            lines.append("")

    return "\n".join(lines)
```

## 輸出格式範例

```markdown
## v1.3.0（2026-03-24）

### ✨ 新功能

- **auth**: 新增 OAuth2 登入支援
- 新增使用者搜尋功能

### 🐛 修復

- **api**: 修復分頁查詢回傳空陣列的問題
- 修復登入逾時未正確處理的問題

### 📝 文件

- 更新 API 文件
- 新增部署指南
```

## 整合到 README.md

將產生的 changelog 插入到 README.md 的變更紀錄區塊：

```markdown
## 變更紀錄

<!-- changelog-start -->
（自動產生的內容會插入這裡）
<!-- changelog-end -->
```

## 非 Conventional Commits 的處理

如果 commit 訊息不符合 Conventional Commits 格式：

1. 嘗試從訊息推斷類型（含「fix」→ fix、含「add」→ feat）
2. 無法推斷的歸類為「其他」
3. 建議團隊採用 Conventional Commits 規範

## 附帶資源

| 檔案 | 用途 | 何時載入 |
|------|------|---------|
| references/conventional-commits.md | Conventional Commits 規範詳解與團隊導入指南 | 需要了解規範細節或導入團隊時 |
