from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests

from dotenv import load_dotenv
import os

load_dotenv() 

TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
#groq
API_KEY = os.getenv('GROQ_API')

def draft_message(content, role='user'):
    return {
        'role': role,
        'content': content
    }

messages_llama = [
    {
        'role': 'system',
        'content': 'content'
    }
]

client = Groq(api_key=API_KEY)

prompt = "only give me the date and time from the text i provide without any additional text in YYYY-MM-DD and hour:minute format, take 2024 as default if not specified. here is the text: "



chat_id_final = os.getenv('CHAT_ID_FINAL')
# message_id_final = os.getenv('MESSAGE_ID_FINAL')
message_id_final = os.getenv('MESSAGE_ID_FINAL')


chat_id_current = ""

scheduler = BackgroundScheduler()

print("BOT_TOKEN:", os.getenv('BOT_TOKEN'))
print("BOT_USERNAME:", os.getenv('BOT_USERNAME'))
print("GROQ_API:", os.getenv('GROQ_API'))
print("CHAT_ID_FINAL:", os.getenv('CHAT_ID_FINAL'))
print("MESSAGE_ID_FINAL:", os.getenv('MESSAGE_ID_FINAL'))
print("API_URL_FINAL:", os.getenv('API_URL_FINAL'))


# to send scheduled messages
def send_message(message, chat_id, message_id):
    API_URL = os.getenv('API_URL_FINAL')
    try:
        response = requests.post(API_URL, json={"chat_id": chat_id, "message_thread_id": message_id, "text": message})
        print(response.text)

    except Exception as e:
        print(e)

# Define conversation states
GET_REMINDER_TEXT = 0

messages = ["here are the reminders: \n"]

def getMessages(messages):
    string = ""
    for mess in messages:
        string += mess + '\n'
    return string


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_current = update.effective_chat.id  # This gets the chat ID of the current chat, including topics
    print(f"Received message from chat ID: {chat_id_current}")
    await update.message.reply_text('Hello, thanks for being here!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, please type your reminder. type /add, then reply to the bot to add your reminder. type /cancel to cancel the reminder')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please enter the reminder text:')
    return GET_REMINDER_TEXT

async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(getMessages(messages))


async def get_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data['reminder_text'] = user_text
    messages.append(user_text)
    messages_llama.append(draft_message(prompt + user_text))
    print(messages_llama)

    chat_completion = client.chat.completions.create (
    temperature = 1.0,
    n=1,
    model="llama3-8b-8192",
    max_tokens=1000,
    messages=messages_llama
    )

    date_to_run = chat_completion.choices[0].message.content
    # use the above to apschedule using schedular library
    # then have another function to schedule, send messages etc
    # see how to make it work with the handler.

    run_time = datetime.strptime(date_to_run, '%Y-%m-%d %H:%M')
    scheduler.add_job(send_message, 'date', run_date=run_time, args=["REMINDER: " + user_text, chat_id_final, message_id_final])

    await update.message.reply_text(f'Reminder added: {user_text}')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Reminder addition cancelled.')
    return ConversationHandler.END

def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'
    if 'how are you' in processed:
        return 'I am good!'
    return 'I do not understand what you wrote...'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    # dont want it to respond to group unless tagged

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response:str = handle_response(new_text)
        else:
            return
        
    else:
        response: str = handle_response(text)

    print('Bot: ', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':

    scheduler.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('get', get_command))

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_command)],
        states={GET_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reminder_text)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(conversation_handler)
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error)
    app.run_polling()

