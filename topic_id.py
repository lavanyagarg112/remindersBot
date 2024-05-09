from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv() 

async def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id  # This gets the chat ID of the current chat, including topics
    print(f"Received message from chat ID: {chat_id}")
    await update.message.reply_text(f"Chat ID: {chat_id}")

if __name__ == '__main__':
    TOKEN = os.getenv('BOT_TOKEN')
    app = Application.builder().token(TOKEN).build()

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Start the bot
    app.run_polling()
