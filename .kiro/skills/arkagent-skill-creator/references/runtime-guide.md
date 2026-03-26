# Runtime 指南

4 種 runtime 的使用場景、選擇指南與注意事項。

## 選擇決策樹

```
Skill 需要什麼？
│
├── 自訂邏輯（爬蟲、格式化、計算）
│   → python runtime
│   → 產出：config/skill.yaml + scripts/skill.py
│
├── 呼叫外部資料庫或工具（SQL / BigQuery / MSSQL）
│   → mcp runtime
│   → 產出：config/skill.yaml（無 skill.py）
│
├── LLM 推理（分析、摘要、判斷）
│   → ai runtime
│   → 產出：config/skill.yaml + assets/prompt.txt
│
└── 串接多個 Skill 的工作流程
    → composite runtime
    → 產出：config/skill.yaml（放在 workflows/ 子目錄）
```

## Python Runtime

最通用的 runtime，適合需要自訂邏輯的場景。

特點：
- 有 skill.py 執行入口（run + run_async）
- 支援 subprocess 隔離或 in-process async 兩種模式
- 可存取 PROJECT_ROOT 下的所有模組

適用場景：
- 爬蟲（crawler）
- 資料格式化（dashboard、notify）
- 閒聊（chat，呼叫 Gemini API）
- 任何需要 Python 邏輯的功能

注意事項：
- skill.py 的 `sys.path` 需要加入 COMPAT_DIR（src 或 compat）
- subprocess 模式需要 `encoding="utf-8"` 避免 cp950 問題
- timeout 預設 30 秒，長時間任務需調高

## MCP Runtime

透過 MCP Controller 呼叫外部 MCP Server，不需要寫 Python 程式碼。

特點：
- 只需 config/skill.yaml（無 skill.py）
- MCPAdapter 自動處理連線、呼叫、回應解析
- 支援 TOOL_ALIASES 和 PARAM_ALIASES 解決命名差異

適用場景：
- SQL 查詢（sqlite-server / mssql-server）
- BigQuery 查詢（bigquery-server）
- 檔案系統操作（filesystem server）
- 任何有 MCP Server 的外部工具

注意事項：
- mcp.server 必須在 config/mcp.json 中設定且未 disabled
- mcp.tool 名稱必須實測確認（不同 server 命名風格不同）
- 首次連線可能較慢（uvx 需要下載套件）

## AI Runtime

LLM 推理驅動，適合需要分析、判斷、摘要的場景。

特點：
- 用 prompt.txt 定義推理指令
- AIAdapter 自動呼叫 Gemini API
- 支援 fallback_skill（失敗時切換到其他 Skill）

適用場景：
- KPI 異常分析
- 資料摘要
- 自然語言判斷

注意事項：
- prompt.txt 中用 `{user_input}` 佔位符
- 需要 GOOGLE_API_KEY 環境變數
- fallback_skill 避免 AI 失敗時無回應

## Composite Runtime

串接多個 Skill 的工作流程，適合多步驟任務。

特點：
- steps[] 定義執行順序
- `{prev.result}` 引用上一步結果
- 支援條件執行（condition）

適用場景：
- 每日報告（查詢 → 儀表板 → 通報）
- 異常偵測（儀表板 → KPI 分析）
- 任何需要串接多個 Skill 的流程

注意事項：
- 放在 `skills/workflows/{skill_id}/` 子目錄
- steps 引用的 skill_id 必須已存在
- 某步驟失敗會中止後續步驟（除非有 condition）
