"""html_exporter 單元測試。

測試 HTML 對話匯出功能：
- 空訊息產生有效 HTML
- 單則訊息包含 timestamp、sender、content
- 程式碼區塊包裹在 pre/code 標籤中
- 多則訊息全部出現在輸出中
- HTML 為自包含結構（html, head, body, style）
"""

from __future__ import annotations

from kiro_agent.html_exporter import export_chat_html


# ---------------------------------------------------------------------------
# 空訊息
# ---------------------------------------------------------------------------


def test_empty_messages_produces_valid_html() -> None:
    """空訊息清單應產生有效的自包含 HTML。"""
    result = export_chat_html("test-agent", [])

    assert "<!DOCTYPE html>" in result
    assert "<html" in result
    assert "<head>" in result
    assert "<body>" in result
    assert "<style>" in result
    assert "</html>" in result
    assert "test-agent" in result


# ---------------------------------------------------------------------------
# 單則訊息
# ---------------------------------------------------------------------------


def test_single_message_includes_timestamp_sender_content() -> None:
    """單則訊息的 timestamp、sender、content 都應出現在 HTML 中。"""
    messages = [
        {
            "timestamp": "2025-01-15T10:30:00Z",
            "sender": "user",
            "content": "Hello, agent!",
        }
    ]
    result = export_chat_html("my-agent", messages)

    assert "2025-01-15T10:30:00Z" in result
    assert "user" in result
    assert "Hello, agent!" in result


# ---------------------------------------------------------------------------
# 程式碼區塊
# ---------------------------------------------------------------------------


def test_code_blocks_wrapped_in_pre_code() -> None:
    """Markdown 程式碼區塊應轉換為 <pre><code> 標籤。"""
    messages = [
        {
            "timestamp": "2025-01-15T11:00:00Z",
            "sender": "agent",
            "content": "Here is code:\n```python\nprint('hello')\n```\nDone.",
        }
    ]
    result = export_chat_html("dev-agent", messages)

    assert "<pre>" in result
    assert "<code" in result
    assert "print(&#x27;hello&#x27;)" in result
    assert 'language-python' in result


def test_code_block_without_language() -> None:
    """無語言標記的程式碼區塊也應正確包裹。"""
    messages = [
        {
            "timestamp": "2025-01-15T11:00:00Z",
            "sender": "agent",
            "content": "Example:\n```\nfoo bar\n```",
        }
    ]
    result = export_chat_html("dev-agent", messages)

    assert "<pre><code>" in result
    assert "foo bar" in result


# ---------------------------------------------------------------------------
# 多則訊息
# ---------------------------------------------------------------------------


def test_multiple_messages_all_appear() -> None:
    """多則訊息應全部出現在輸出 HTML 中。"""
    messages = [
        {"timestamp": "T1", "sender": "alice", "content": "First message"},
        {"timestamp": "T2", "sender": "bob", "content": "Second message"},
        {"timestamp": "T3", "sender": "alice", "content": "Third message"},
    ]
    result = export_chat_html("team-chat", messages)

    assert "First message" in result
    assert "Second message" in result
    assert "Third message" in result
    assert "alice" in result
    assert "bob" in result
    assert "T1" in result
    assert "T2" in result
    assert "T3" in result


# ---------------------------------------------------------------------------
# 自包含 HTML 結構
# ---------------------------------------------------------------------------


def test_html_is_self_contained() -> None:
    """匯出的 HTML 應包含完整的 html/head/body/style/script 結構。"""
    result = export_chat_html("agent-x", [])

    assert "<html" in result
    assert "<head>" in result
    assert "</head>" in result
    assert "<body>" in result
    assert "</body>" in result
    assert "<style>" in result
    assert "</style>" in result
    assert "<script>" in result
    assert "</script>" in result
    assert '<meta charset="UTF-8">' in result


# ---------------------------------------------------------------------------
# HTML 跳脫安全性
# ---------------------------------------------------------------------------


def test_html_escapes_special_characters() -> None:
    """特殊字元應被正確跳脫，避免 XSS。"""
    messages = [
        {
            "timestamp": "T1",
            "sender": "<script>alert(1)</script>",
            "content": "a < b & c > d",
        }
    ]
    result = export_chat_html("<evil>", messages)

    assert "&lt;evil&gt;" in result
    assert "&lt;script&gt;" in result
    assert "a &lt; b &amp; c &gt; d" in result


# ---------------------------------------------------------------------------
# Instance 名稱顯示在標題
# ---------------------------------------------------------------------------


def test_instance_name_in_title() -> None:
    """Instance 名稱應出現在 HTML <title> 中。"""
    result = export_chat_html("my-cool-agent", [])

    assert "<title>my-cool-agent - Chat Export</title>" in result
