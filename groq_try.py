from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv() 

API_KEY = os.getenv('GROQ_API')

def draft_message(content, role='user'):
    return {
        'role': role,
        'content': content
    }

messages_llama = [

]

client = Groq(api_key=API_KEY)

prompt = 'only give me the date and time without any additional text in DD/MM/YYYY and hour:minute format, take 2024 as default if not specified. here is the text: remind me to schedule my timetable on 5th June at 5pm'
messages_llama.append(draft_message(prompt))

prompt = 'on the first line give the reminder asked by the user, on the second line only give me the date and time without any additional text in DD/MM/YYYY and hour:minute format, take 2024 as default if not specified. here is the text: '
messages_llama.append(draft_message(prompt + "remind me to go for cvwo on 13th May 9 pm"))
print(messages_llama)

chat_completion = client.chat.completions.create (
    temperature = 1.0,
    n=1,
    model="llama3-8b-8192",
    max_tokens=1000,
    messages=messages_llama


)

print(chat_completion.usage.total_tokens)
print(type(chat_completion.choices[0].message.content))

# why does this only print for the last one