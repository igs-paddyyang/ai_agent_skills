# Conventional Commits 規範詳解

本文件詳細說明 Conventional Commits 規範，以及如何在團隊中導入。

## 規範概述

Conventional Commits 是一種 commit 訊息的撰寫規範，讓 commit 歷史可被機器解析。
規範基於 [conventionalcommits.org](https://www.conventionalcommits.org/)。

## 完整格式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Header（必填）

```
feat(auth): 新增 Google OAuth2 登入
│     │      │
│     │      └─ description: 簡短描述（祈使句、不加句號）
│     └─ scope: 影響範圍（選填）
└─ type: 變更類型
```

### Body（選填）

提供更多背景資訊，解釋「為什麼」而非「做了什麼」。

```
feat(auth): 新增 Google OAuth2 登入

原本只支援帳號密碼登入，使用者反映希望能用 Google 帳號快速登入。
新增 OAuth2 流程，支援 Google 和 GitHub 兩種 provider。
```

### Footer（選填）

用於 Breaking Change 或關聯 issue。

```
feat(auth): 新增 Google OAuth2 登入

BREAKING CHANGE: 移除舊的 session-based 認證，改用 JWT token。
所有 API 呼叫需要在 Header 加上 Authorization: Bearer <token>。

Closes #123
```

## Type 完整列表

| Type | 說明 | 範例 |
|------|------|------|
| feat | 新功能 | `feat: 新增使用者搜尋` |
| fix | Bug 修復 | `fix: 修復分頁查詢錯誤` |
| docs | 文件 | `docs: 更新 API 文件` |
| style | 格式（不影響邏輯） | `style: 修正縮排` |
| refactor | 重構（不改功能） | `refactor: 提取共用函式` |
| perf | 效能改善 | `perf: 快取查詢結果` |
| test | 測試 | `test: 新增登入測試` |
| build | 建置系統 | `build: 升級 Python 到 3.12` |
| ci | CI/CD | `ci: 新增 GitHub Actions` |
| chore | 雜務 | `chore: 更新 .gitignore` |
| revert | 還原 | `revert: 還原 feat: 新增搜尋` |

## Scope 建議

Scope 用來標示影響範圍，建議與專案模組對應：

```
# ArkBot 專案
feat(core): ...        # arkbot_core
feat(telegram): ...    # bot_main
feat(web): ...         # web_server
feat(skill): ...       # skill runtime
feat(db): ...          # 資料庫

# Kiro Skills 專案
feat(skill-creator): ...
feat(tdd-workflow): ...
docs(steering): ...
```

## 團隊導入指南

### 第一步：建立規範文件

在專案根目錄建立 `.gitmessage` 範本：

```
# <type>(<scope>): <description>
#
# Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
# Scope: 影響的模組名稱（選填）
# Description: 簡短描述，祈使句，不加句號
#
# Body: 解釋為什麼做這個變更（選填）
#
# Footer: BREAKING CHANGE / Closes #issue（選填）
```

設定 git 使用此範本：

```bash
git config commit.template .gitmessage
```

### 第二步：設定 commit-msg hook（選用）

```bash
# .git/hooks/commit-msg
#!/bin/sh
PATTERN='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?(!)?: .+'
if ! grep -qE "$PATTERN" "$1"; then
    echo "錯誤：commit 訊息不符合 Conventional Commits 格式"
    echo "格式：<type>(<scope>): <description>"
    exit 1
fi
```

### 第三步：漸進式導入

1. 先從新的 commit 開始遵循規範
2. 不要求回溯修改歷史 commit
3. 團隊 code review 時檢查 commit 訊息格式
4. 一個月後評估導入效果

## 常見問題

| 問題 | 建議 |
|------|------|
| 一個 commit 包含多種變更 | 拆成多個 commit，每個只做一件事 |
| 不確定用 feat 還是 fix | feat = 新行為，fix = 修正既有行為 |
| refactor 和 fix 的界線 | refactor 不改變外部行為，fix 修正錯誤行為 |
| scope 要多細 | 對應到模組或功能區域，不要太細（如檔案名） |
| 中文還是英文 | 團隊統一即可，本專案建議中文 description |
