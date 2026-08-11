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

for user in users:
    name = user['name']
    chat_id = user['chat_id']
    
    print(f"Sending evening checkup to {name}...")
    
    message = f"🌅 Good evening, {name}!\n\n"
    message += f"I hope you're having a great day! 🌟\n\n"
    message += f"How did you find today's articles? Were they helpful and relevant to your interests?\n\n"
    message += f"📝 Quick feedback questions:\n"
    message += f"• Were the topics interesting?\n"
    message += f"• Were the summaries useful?\n"
    message += f"• Would you like more/less articles?\n"
    message += f"• Any specific topics you'd like more of?\n\n"
    message += f"⏰ Note: There might be a slight delay in tomorrow's article delivery due to system maintenance. I'll make sure you still get your daily news updates!\n\n"
    message += f"Feel free to share your thoughts or use any of the bot commands:\n"
    message += f"• /interest - Mark articles you like\n"
    message += f"• /myinterests - View your saved articles\n"
    message += f"• /exportdaily - Export your interests as Word document\n"
    message += f"• /help - See all available commands\n\n"
    message += f"Have a wonderful evening! 🌙"
    
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Evening checkup sent to {name}")
    else:
        print(f"❌ Error sending to {name}: {result}")

print("\n✅ Evening checkups sent to both users")
