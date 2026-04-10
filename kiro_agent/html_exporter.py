"""HTML 對話匯出模組。

將 chat_history.jsonl 的對話記錄匯出為自包含 HTML 檔案，
內嵌 CSS 與 JS，保留時間戳記、發送者標識與程式碼區塊格式。
"""

from __future__ import annotations

import html
import re

# 匹配 markdown 風格的程式碼區塊：```lang\n...\n```
_CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)


def _format_content(content: str) -> str:
    """將訊息內容中的程式碼區塊轉換為 <pre><code> 標籤。

    非程式碼部分做 HTML 跳脫並保留換行。
    """
    parts: list[str] = []
    last_end = 0

    for m in _CODE_BLOCK_RE.finditer(content):
        # 程式碼區塊之前的文字
        before = content[last_end:m.start()]
        if before:
            parts.append(html.escape(before).replace("\n", "<br>"))

        lang = html.escape(m.group(1))
        code = html.escape(m.group(2))
        lang_attr = f' class="language-{lang}"' if lang else ""
        parts.append(
            f'<div class="code-wrapper">'
            f"<pre><code{lang_attr}>{code}</code></pre>"
            f'<button class="copy-btn" onclick="copyCode(this)">Copy</button>'
            f"</div>"
        )
        last_end = m.end()

    # 剩餘文字
    tail = content[last_end:]
    if tail:
        parts.append(html.escape(tail).replace("\n", "<br>"))

    return "".join(parts)


def export_chat_html(instance_name: str, messages: list[dict]) -> str:
    """將對話記錄匯出為自包含 HTML（內嵌 CSS + JS）。

    Args:
        instance_name: Agent Instance 名稱，顯示於標題。
        messages: 訊息清單，每則包含 timestamp、sender、content 欄位。

    Returns:
        完整的 HTML 字串。
    """
    escaped_name = html.escape(instance_name)

    # 組裝訊息 HTML
    msg_parts: list[str] = []
    for msg in messages:
        ts = html.escape(str(msg.get("timestamp", "")))
        sender = html.escape(str(msg.get("sender", "")))
        content = _format_content(str(msg.get("content", "")))
        msg_parts.append(
            f'<div class="message">'
            f'<div class="meta">'
            f'<span class="sender">{sender}</span>'
            f'<span class="timestamp">{ts}</span>'
            f"</div>"
            f'<div class="content">{content}</div>'
            f"</div>"
        )
    messages_html = "\n".join(msg_parts)

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        '<meta charset="UTF-8">\n'
        f"<title>{escaped_name} - Chat Export</title>\n"
        "<style>\n"
        "body{font-family:system-ui,sans-serif;margin:0;padding:20px;background:#f5f5f5;color:#222}\n"
        "h1{margin:0 0 16px}\n"
        ".message{background:#fff;border-radius:8px;padding:12px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.1)}\n"
        ".meta{display:flex;gap:12px;margin-bottom:6px;font-size:.85em;color:#666}\n"
        ".sender{font-weight:700;color:#333}\n"
        ".code-wrapper{position:relative;margin:8px 0}\n"
        "pre{background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:6px;overflow-x:auto;margin:0}\n"
        ".copy-btn{position:absolute;top:6px;right:6px;background:#555;color:#fff;border:none;border-radius:4px;padding:2px 8px;cursor:pointer;font-size:.75em}\n"
        ".copy-btn:hover{background:#777}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        f"<h1>{escaped_name}</h1>\n"
        f"{messages_html}\n"
        "<script>\n"
        "function copyCode(btn){const code=btn.parentElement.querySelector('code');navigator.clipboard.writeText(code.textContent).then(()=>{btn.textContent='Copied!';setTimeout(()=>btn.textContent='Copy',1500)})}\n"
        "</script>\n"
        "</body>\n"
        "</html>"
    )
