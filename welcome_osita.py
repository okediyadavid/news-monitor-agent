import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Get Osita's chat ID
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, telegram_chat_id FROM users WHERE name = "Osita Nwana"')
user = cursor.fetchone()

if user:
    user_id, name, chat_id = user
    print(f"Found user: {name} (ID: {user_id}, Chat ID: {chat_id})")
    
    # Send welcome message
    welcome_message = f"""🎉 Welcome to the News Monitor Bot, {name}!

I'm your personal news assistant that will keep you updated with the latest articles from your favorite news sources.

**How it works:**
• I automatically fetch news articles every 6 hours
• You'll receive updates directly on Telegram
• You can add more news sources anytime

**Getting started:**
• Your sources are already configured
• I'll start sending you news articles soon
• Use /help to see all available commands

If you have any questions, feel free to ask! 📰"""
    
    data = {
        'chat_id': chat_id,
        'text': welcome_message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Welcome message sent to {name}")
    else:
        print(f"❌ Error sending welcome message: {result}")
else:
    print("❌ User Osita Nwana not found in database")

conn.close()
