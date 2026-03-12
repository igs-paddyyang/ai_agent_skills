import os
import asyncio
import logging
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# 匯入我們先前開發的模組
from intent_router import ClawdBrain
from crawler_skill import ClawdCrawler
from format_utils import escape_markdown_v2, format_summary_message

# 作者: paddyyang
# 最後修改日期: 2026-03-11

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class ClawdBot:
    def __init__(self):
        # 載入根目錄的 .env
        env_path = os.path.join(os.path.dirname(__file__), "../../.env")
        load_dotenv(env_path)
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("❌ 錯誤: .env 中缺少 TELEGRAM_TOKEN")
            
        self.app = ApplicationBuilder().token(token).build()
        self.brain = ClawdBrain()
        self.crawler = ClawdCrawler()
        
        # 註冊處理器
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 注意：MarkdownV2 所有保留字元 ( ) [ ] _ * ~ ` > # + - = | { } . ! 都必須用 \ 跳脫
        # (v1.0) 的括號、！ 都是保留字元，直接寫會觸發 BadRequest: Can't parse entities
        welcome_text = (
            "🚀 *歡迎使用 ClawdBot 智庫助理 \\(v1\\.0\\)*\n\n"
            "直接發送網址給我，我會為您：\n"
            "1️⃣ 獵取網頁內容\n"
            "2️⃣ 自動轉化為 Markdown\n"
            "3️⃣ 生成智慧摘要並存入智庫\n\n"
            "讓我們開始吧\\!"
        )
        await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.MARKDOWN_V2)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        
        # 1. 意圖識別
        status_msg = await update.message.reply_text("🧠 正在思考...", parse_mode=constants.ParseMode.MARKDOWN)
        intent_data = self.brain.classify_intent(user_input)
        
        if intent_data.get("intent") == "RESEARCH" and intent_data.get("url"):
            target_url = intent_data["url"]
            
            # 2. 爬取網頁
            await status_msg.edit_text(f"🔍 偵測到網址，正在獵取中...\n`{target_url}`", parse_mode=constants.ParseMode.MARKDOWN)
            markdown_content, is_cache = self.crawler.fetch_and_save(target_url)
            
            if "Error" in markdown_content:
                await status_msg.edit_text(f"❌ 獵取失敗: {markdown_content}")
                return

            # 3. 內容分析
            await status_msg.edit_text("🧠 內容已獲取，正在進行智慧摘要與智庫封存...", parse_mode=constants.ParseMode.MARKDOWN)
            summary = self.brain.summarize_content(markdown_content, url=target_url)
            
            # 固定標題（可以從資料庫或解析中獲取更準確的）
            title = "網頁專題分析"
            if is_cache:
                title += " (來自快取)"

            # 4. 格式化回傳
            final_text = format_summary_message(title, summary, target_url)
            
            try:
                await status_msg.delete() # 刪除狀態訊息
                await update.message.reply_text(final_text, parse_mode=constants.ParseMode.MARKDOWN_V2)
            except Exception as e:
                logging.error(f"Markdown 發送失敗: {e}")
                # 備援計畫：發送純文字，避免 Bot 無回應
                await update.message.reply_text(f"⚠️ 格式渲染錯誤，改發送純文字摘要：\n\n{summary}")
        
        else:
            # 一般聊天模式：使用專屬 chat() 方法，避免 summarize_content 的摘要格式污染回應
            await status_msg.edit_text("💬 正在生成回應...")
            response = self.brain.chat(user_input)
            await status_msg.edit_text(response)

    def run(self):
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        print("ClawdBot is running, waiting for messages...")
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    bot = ClawdBot()
    bot.run()
