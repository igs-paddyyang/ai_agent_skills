import re

# 作者: paddyyang
# 最後修改日期: 2026-03-11

def escape_markdown_v2(text):
    """
    Escapes Telegram MarkdownV2 special characters.
    Helper to prevent 'Bad Request: can't parse entities' errors.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_summary_message(title, summary, url):
    """
    Formats the final message for Telegram.
    """
    header = f"🚀 *智庫獵取成功*\n\n"
    title_line = f"📌 *標題*: {escape_markdown_v2(title)}\n"
    url_line = f"🔗 *來源*: [點擊前往]({url})\n\n"
    body = f"🧠 *分析摘要*:\n{escape_markdown_v2(summary)}"
    
    return f"{header}{title_line}{url_line}{body}"
