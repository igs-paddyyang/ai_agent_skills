---
name: ci-automation
description: >
  引導建立持續整合（CI）自動化流程，涵蓋本地 CI 模擬腳本與 GitHub Actions workflow。
  支援 lint（ruff）、技能驗證（quick_validate）、技能同步（skill-sync）三階段流程。
  當使用者提到 CI、持續整合、自動化測試、GitHub Actions、lint、程式碼檢查、
  自動化流程、CI/CD、ci-automation、本地 CI、自動化部署、ruff、flake8 時，
  請務必使用此技能。
---

# CI 自動化（CI Automation）

引導建立持續整合流程，確保每次提交都通過 lint、驗證和同步。

## 使用時機

- 需要建立 CI pipeline（GitHub Actions 或本地模擬）
- 想在提交前自動檢查程式碼品質
- 需要確保技能驗證和同步的自動化

## CI 三階段流程

```
Stage 1: Lint（ruff check）
  ↓
Stage 2: Validate（quick_validate.py × 所有技能）
  ↓
Stage 3: Sync（skill-sync 全量同步）
```

## 本地 CI 模擬

使用 `scripts/ci_local.py` 在本地模擬完整 CI 流程：

```bash
py .kiro/skills/ci-automation/scripts/ci_local.py
py .kiro/skills/ci-automation/scripts/ci_local.py --skip-lint    # 跳過 lint
py .kiro/skills/ci-automation/scripts/ci_local.py --skip-sync    # 跳過同步
```

## GitHub Actions

建議的 workflow 配置放在 `.github/workflows/ci.yml`，觸發條件：
- push to main
- pull request to main

workflow 步驟：
1. checkout + setup Python
2. install dependencies（`pip install -r requirements.txt ruff`）
3. ruff check（lint）
4. quick_validate.py（驗證所有技能）

注意：GitHub Actions 環境不需要 skill-sync（.agent/skills/ 已在 repo 中）。

## 附帶資源

| 資源 | 用途 | 何時使用 |
|------|------|---------|
| `scripts/ci_local.py` | 本地 CI 模擬腳本 | 提交前執行，確保通過 |
