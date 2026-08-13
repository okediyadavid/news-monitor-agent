import os
import sqlite3
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Get all users
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, telegram_chat_id FROM users')
users = cursor.fetchall()

print(f"Found {len(users)} users")
print("=" * 60)

# Get articles from past 3 days to include recent articles
today = datetime.now()
three_days_ago = today - timedelta(days=3)

for user in users:
    user_id = user[0]
    user_name = user[1]
    chat_id = user[2]
    
    print(f"\nProcessing {user_name}...")
    
    # Get articles from the past 3 days
    cursor.execute('''
        SELECT a.*, s.name as source_name 
        FROM articles a 
        JOIN sources s ON a.source_id = s.id 
        WHERE a.user_id = ? AND a.created_at >= ?
        ORDER BY a.created_at DESC
    ''', (user_id, three_days_ago.isoformat()))
    
    articles = cursor.fetchall()
    
    print(f"  Found {len(articles)} articles from past day")
    
    if articles:
        # Send header message
        header_message = f"📰 **Latest Articles** ({len(articles)} articles)\n\n"
        header_message += f"Here are your latest news articles:"
        
        data = {'chat_id': chat_id, 'text': header_message}
        response = requests.post(api_url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print(f"  ✅ Header sent")
        else:
            print(f"  ❌ Error sending header: {result}")
        
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
        print(f"  No recent articles found")

conn.close()

print("\n" + "=" * 60)
print("✅ Latest articles sent to all users")
