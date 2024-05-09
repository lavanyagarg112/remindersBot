from dotenv import load_dotenv
import os

load_dotenv()
print("MESSAGE_ID_FINAL:", os.getenv('MESSAGE_ID_FINAL'))
