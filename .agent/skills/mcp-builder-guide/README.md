# MCP Server 建立指引（MCP Builder Guide）

> 引導建立符合 MCP 規範的 Server，涵蓋 Python SDK 快速上手、Tool/Resource/Prompt 定義與常見模式。

## 版本資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 0.1.0 |
| 作者 | paddyyang |
| 建立日期 | 2026-03-24 |
| 最後更新 | 2026-03-24 |
| 平台 | Kiro |
| 語言 | 繁體中文 |

## 功能說明

提供從零建立 MCP（Model Context Protocol）Server 的完整指引。核心內容包含 MCP 協議概念（Tools、Resources、Prompts）、Python SDK（`mcp` 套件）快速上手、Tool 定義與參數驗證（Pydantic）、常見 Server 模式（資料庫查詢、API 代理、檔案操作），以及與 ArkAgent OS Tool Gateway 的整合方式。

## 使用方式

觸發此技能的方式：

```
「幫我建立一個查詢資料庫的 MCP Server」
「MCP Tool 怎麼定義參數驗證？」
「建立一個 MCP Server」
「怎麼把 API 包裝成 MCP」
「MCP Python SDK 怎麼用」
```

## 檔案結構

```
.kiro/skills/mcp-builder-guide/
├── SKILL.md                          # 主要技能指令（MCP Server 建立流程）
├── README.md                         # 本文件
└── references/                       # 詳細指南（按需載入）
    ├── mcp-python-sdk.md             # Python MCP SDK API 參考與進階用法
    └── mcp-patterns.md               # 常見 MCP Server 模式與完整範例
```

## 設計參考

本技能參考 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 的 MCP Builder Skill，
針對本專案的 Python 環境與 ArkAgent OS Tool Gateway 進行在地化調整。

## 變更紀錄

### v0.1.0（2026-03-24）
- 初始版本建立
- MCP 協議核心概念（Tools、Resources、Prompts）
- Python SDK 快速上手與最小可用範例
- Tool 定義詳解（基本、Pydantic 驗證、非同步）
- Resource 與 Prompt 定義
- 常見 Server 模式（資料庫查詢、API 代理）
- Kiro mcp.json 配置說明
- 2 個 references 檔案（mcp-python-sdk.md、mcp-patterns.md）
