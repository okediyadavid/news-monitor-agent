import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Users
users = [
    {'name': 'Dave', 'chat_id': '1287986887'},
    {'name': 'Joshua', 'chat_id': '2016570012'}
]

message = """⚠️ **Please ignore the previous message**

The bot is now live and running 24/7 on Render!

To get started:
1. Send /start to begin
2. Send /register [your name] to create your account
3. Add your news sources with /addsource

The bot will automatically send you news articles every 6 hours from your configured sources."""

for user in users:
    chat_id = user['chat_id']
    name = user['name']
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Correction sent to {name}")
    else:
        print(f"❌ Error sending to {name}: {result}")

print("\n✅ Correction message sent to all users")
