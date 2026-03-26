# skill.yaml Schema 規格

Agent Skill Package 的 runtime metadata 定義。

## 共通必填欄位

```yaml
type: skill                    # 固定值
name: {kebab-case}             # 技能名稱（≤64 字元）
version: 1.0.0                 # SemVer
skill_id: {kebab-case}        # 與 name 相同
runtime: python|mcp|ai|composite  # 執行模式
intent:                        # 對應的意圖（list 格式）
  - {UPPER_SNAKE_CASE}
description: "{說明}"          # 一句話描述
```

## 共通選填欄位

```yaml
examples:                      # 觸發範例（建議 3-5 個）
  - "範例句子 1"
  - "範例句子 2"
tags:                          # 標籤（用於搜尋和分類）
  - tag1
  - tag2
priority: 5                    # 優先順序（1-10，越高越優先）
enabled: true                  # 啟用狀態
response_type: text            # 回應類型（text / dashboard）
```

## Python Runtime 額外欄位

```yaml
execution:
  mode: async                  # async（in-process）或 subprocess
  entry: skill.py              # 入口檔案（相對於 skill 目錄）
  timeout: 30                  # 執行超時（秒）
```

入口檔案必須包含 `run(user_input: str)` 或 `run_async(user_input: str)` 函式。

## MCP Runtime 額外欄位

```yaml
mcp:
  server: mssql-server         # config/mcp.json 中的 server key
  tool: execute_sql            # MCP tool 名稱（必須實測確認）
  param_mapping:               # 參數映射
    query: "{user_input}"      # {user_input} 會被替換為使用者輸入
```

不需要 skill.py，由 MCPAdapter 直接呼叫 MCP tool。

## AI Runtime 額外欄位

```yaml
ai:
  model: gemini-2.5-flash      # LLM 模型名稱
  prompt_file: prompt.txt      # prompt 檔案路徑（相對於 skill 目錄）
  fallback_skill: chat         # 失敗時 fallback 的 skill_id（選用）
```

prompt.txt 中可使用 `{user_input}` 佔位符。

## Composite Runtime 額外欄位

```yaml
steps:
  - skill_id: revenue-query    # 第一步：呼叫的 skill
    input: "SELECT ..."        # 傳入的輸入
  - skill_id: dashboard        # 第二步
    input: "{prev.result}"     # 引用上一步結果
  - skill_id: notify           # 第三步
    input: "{prev.result}"
    params:                    # 額外參數（選用）
      route: daily_revenue
    condition: "prev.success == true"  # 執行條件（選用）
```

Composite Skill 放在 `skills/workflows/{skill_id}/` 子目錄。

## 驗證規則

| 欄位 | 規則 |
|------|------|
| name / skill_id | kebab-case，≤64 字元，不能以 `-` 開頭/結尾 |
| intent | UPPER_SNAKE_CASE，list 格式 |
| description | ≤1024 字元 |
| runtime | 必須是 python / mcp / ai / composite 之一 |
| mcp.server | 必須存在於 config/mcp.json 且未 disabled |
| steps[].skill_id | 必須存在於 skills/ 目錄 |
