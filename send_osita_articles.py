import os
import sqlite3
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Get Osita's user info
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, telegram_chat_id FROM users WHERE name = "Osita Nwana"')
user = cursor.fetchone()

if user:
    user_id, user_name, chat_id = user
    print(f"Processing {user_name}...")
    
    # Get latest 10 articles
    cursor.execute('''
        SELECT a.*, s.name as source_name 
        FROM articles a 
        JOIN sources s ON a.source_id = s.id 
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT 10
    ''', (user_id,))
    
    articles = cursor.fetchall()
    
    print(f"  Found {len(articles)} recent articles")
    
    if articles:
        # Send header message
        header_message = f"📰 **Today's Articles** ({len(articles)} articles)\n\n"
        header_message += f"Here are your latest news articles for today:"
        
        data = {'chat_id': chat_id, 'text': header_message}
        response = requests.post(api_url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print(f"  ✅ Header sent")
        else:
            print(f"  ❌ Error sending header: {result}")
        
        import time
        time.sleep(1)
        
        # Send articles
        for article in articles:
            message = f"*New Article*\n\n"
            message += f"📍 Source: {article[7]}\n"
            message += f"📝 Title: {article[3]}\n"
            
            if article[4]:
                message += f"📄 Summary: {article[4][:200]}...\n\n"
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
                print(f"  Sent: {article[3][:50]}...")
            else:
                print(f"  Error sending: {result}")
            
            time.sleep(1)
    else:
        print(f"  No articles found for today")
else:
    print("❌ User Osita Nwana not found")

conn.close()
