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

TOKEN: Final = os.getenv('BOT_TOKEN')
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')
#groq
API_KEY: Final = os.getenv('GROQ_API')

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

prompt = "only give me the date and time from the text i provide without any additional text in YYYY-MM-DD and \
    hour:minute format, take 2024 as default if not specified. here is the text: "



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

def send_personal(message, chat_id):
    API_URL = os.getenv('API_URL_FINAL')
    try:
        response = requests.post(API_URL, json={"chat_id": chat_id, "text": message})
        print(response.text)

    except Exception as e:
        print(e)

# Define conversation states
GET_REMINDER_TEXT = 0

# messages = ["here are the reminders: \n"]

# dictionary to store messages
# can segregate by userid also if needed for better segregation
messages_userid = {

}

# def getMessages(messages):
#     string = ""
#     for mess in messages:
#         string += mess + '\n'
#     return string

def getMessages_dict(messages):
    string = ""
    for user in messages:
        for mess in messages[user]:
            string += mess + '\n'
        string += '\n'
    return string


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_current = update.effective_chat.id  # This gets the chat ID of the current chat
    print(f"Received message from chat ID: {chat_id_current}")
    await update.message.reply_text('Hello, thanks for being here!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, please type your reminder. type /add, then reply to the bot to add your reminder. type /cancel to cancel the reminder')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please enter the reminder text:')
    return GET_REMINDER_TEXT

async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(getMessages_dict(messages_userid))


async def get_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    username = update.message.from_user.username
    userid = update.message.from_user.id # maybe send reminder to the person?

    user_text = update.message.text
    context.user_data['reminder_text'] = user_text

    if userid not in messages_userid:
        messages_userid[userid] = [("USERNAME: " + username + "\n")]
        
    messages_userid[userid].append(user_text)

    # messages.append("USERNAME: " + username + "\n REMINDER: " + user_text)
    date_time = update.message.date.strftime('%Y-%m-%d %H:%M:%S')
    print(date_time)
    messages_llama.append(draft_message(prompt + user_text + " . now, ONLY if date not specified in the prev text, take today's date from: " + date_time
                                        + ",remember, only provide date and time, in the format. if time and date are specified in prev text, then take those"))
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
    scheduler.add_job(send_message, 'date', run_date=run_time, args=["USERNAME: " + username + "\n REMINDER: " + user_text, chat_id_final, message_id_final])
    scheduler.add_job(send_personal, 'date', run_date=run_time, args=["REMINDER: " + user_text, userid])

    await update.message.reply_text(f'Reminder added: {user_text} \n Scheduled for: {date_to_run}')
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

