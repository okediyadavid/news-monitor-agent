import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

chat_id = '1287986887'

print("Sending more articles to Dave...")

# Get latest articles for Dave
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT a.*, s.name as source_name 
    FROM articles a 
    JOIN sources s ON a.source_id = s.id 
    WHERE a.user_id = 1
    ORDER BY a.created_at DESC
    LIMIT 5
''')

articles = cursor.fetchall()
conn.close()

print(f"Found {len(articles)} latest articles for Dave")

if articles:
    for article in articles:
        message = f"*New Article*\n\n"
        message += f"📍 Source: {article[7]}\n"
        message += f"📝 Title: {article[3]}\n"
        
        if article[4]:
            message += f"📄 Summary: {article[4]}\n\n"
        else:
            message += "\n"
        
        message += f"🔗 [Read more]({article[2]})"
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(api_url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print(f"Sent to Dave: {article[3][:50]}...")
        else:
            print(f"Error sending to Dave: {result}")
        
        import time
        time.sleep(1)

print("✅ More articles sent to Dave")
