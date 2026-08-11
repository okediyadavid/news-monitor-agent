import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Users to check up on
users = [
    {'name': 'Joshua', 'chat_id': '2016570012'},
    {'name': 'Dave', 'chat_id': '1287986887'}
]

api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

for user in users:
    name = user['name']
    chat_id = user['chat_id']
    
    message = f"Hey {name}! 👋\n\n"
    message += "Hope you found today's articles useful and informative! 📰\n\n"
    message += "I'm here to keep you updated with the latest news that matters to you. "
    message += "Feel free to let me know if there are specific topics you'd like me to focus on more! 🎯\n\n"
    message += "Remember, you can always use commands like:\n"
    message += "• /checknow - Get fresh articles immediately\n"
    message += "• /search [topic] - Find specific topics\n"
    message += "• /mysources - See your news sources\n"
    message += "• /help - See all available commands\n\n"
    message += "Have a great day! 🌟"
    
    data = {
        'chat_id': chat_id,
        'text': message
    }
    
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Check-up message sent to {name}")
    else:
        print(f"❌ Error sending to {name}: {result}")
