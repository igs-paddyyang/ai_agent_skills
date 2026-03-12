---
inclusion: manual
---

# slide-generator（投影片生成器）

引導 Kiro 開發一個「Markdown 大綱 → PPTX 投影片」的 CLI 工具，支援手動大綱與 AI 自動生成大綱兩種模式。

## 觸發情境

- 使用者說「建立投影片生成器」、「開發 slide generator」
- 使用者想從 Markdown 大綱自動產出 PPTX
- 使用者想用 AI 生成投影片大綱再轉成 PPTX

## 技術棧

- Python 3.12+，Windows 使用 `py` 載入器
- `python-pptx`：PPTX 生成
- `typer` + `rich`：CLI 框架
- `google-genai`：AI 大綱生成（Gemini 2.5 Flash Lite）
- `python-dotenv`：環境變數

## 工作流程

### 步驟 1：建立目錄結構

在專案根目錄下建立：

```
slide_generator/
├── src/
│   ├── __init__.py
│   ├── outline_parser.py      # Markdown 大綱解析器
│   ├── slide_generator.py     # PPTX 生成器
│   └── ai_outline_generator.py  # AI 大綱生成（Gemini）
├── main.py                    # CLI 入口（typer）
├── examples/
│   └── outline.md             # 範例大綱
└── outputs/                   # PPTX 產出目錄
```

### 步驟 2：實作 outline_parser.py

解析 Markdown 大綱為結構化資料：

- 輸入：Markdown 檔案路徑
- `# 標題` → 投影片標題
- 非標題行 → 該投影片的 bullet points
- 輸出：`list[dict]`，每個 dict 含 `title` 和 `bullets`

```python
def parse_outline(file_path: str) -> list[dict]:
```

### 步驟 3：實作 slide_generator.py

將結構化資料轉為 PPTX：

- 輸入：`list[dict]`（來自 outline_parser）
- 使用 `python-pptx` 的 `slide_layouts[1]`（標題 + 內容版面）
- 每張投影片設定標題與 bullet points
- 輸出至 `outputs/presentation.pptx`

```python
def create_ppt(slides: list[dict], output_path: str = "outputs/presentation.pptx") -> None:
```

### 步驟 4：實作 ai_outline_generator.py

用 Gemini 自動生成大綱：

- 輸入：主題字串
- 載入 `.agent/skills/slide-writer/SKILL.md` 作為系統指令（Skill-First）
- 呼叫 Gemini API 生成 Markdown 格式大綱
- 輸出：Markdown 字串

```python
def generate_outline(topic: str) -> str:
```

注意：使用 `google-genai` + `models/gemini-2.5-flash-lite`，不是 OpenAI。API Key 從 `.env` 的 `GOOGLE_API_KEY` 讀取。

### 步驟 5：實作 main.py CLI 入口

使用 `typer` 建立 CLI，提供兩個指令：

```bash
# 從現有大綱生成投影片
py main.py generate examples/outline.md

# AI 生成大綱再轉投影片
py main.py ai "AI Agent Introduction"
```

```python
import typer
app = typer.Typer()

@app.command()
def generate(file: str) -> None:
    """從 Markdown 大綱生成 PPTX"""

@app.command()
def ai(topic: str) -> None:
    """AI 生成大綱再轉 PPTX"""
```

### 步驟 6：建立範例大綱與測試

1. 建立 `examples/outline.md` 範例檔
2. 確保 `outputs/` 目錄存在
3. 執行 `py main.py generate examples/outline.md` 驗證
4. 執行 `py main.py ai "測試主題"` 驗證 AI 模式
5. 確認 `outputs/presentation.pptx` 正確產出

## 品質標準

| 項目 | 要求 |
|---|---|
| CLI 框架 | typer，指令有 `--help` 說明 |
| AI 模式 | 遵循 Skill-First，從 SKILL.md 載入 Prompt |
| 錯誤處理 | 檔案不存在、API 失敗時顯示友善錯誤訊息 |
| 輸出目錄 | 自動建立 `outputs/`，不需手動 mkdir |
| 編碼 | UTF-8，支援繁體中文大綱 |

---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
