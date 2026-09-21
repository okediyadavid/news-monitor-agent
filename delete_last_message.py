import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"

# Users
users = [
    {'name': 'Dave', 'chat_id': '1287986887'},
    {'name': 'Joshua', 'chat_id': '2016570012'}
]

# Note: To delete a message, we need the message_id from the original send
# Since we don't have the message_id from the previous send, we cannot delete it programmatically
# The user will need to delete it manually in Telegram

print("Cannot delete message programmatically without message_id.")
print("Please delete the message manually in Telegram.")
