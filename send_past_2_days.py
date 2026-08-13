import os
import sqlite3
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Users
users = [
    {'name': 'Dave', 'user_id': 1, 'chat_id': '1287986887'},
    {'name': 'Joshua', 'user_id': 3, 'chat_id': '2016570012'}
]

# Calculate date range (past 2 days)
today = datetime.now()
two_days_ago = today - timedelta(days=3)  # Include 3 days to be safe

for user in users:
    user_id = user['user_id']
    chat_id = user['chat_id']
    name = user['name']
    
    print(f"\nFetching articles for {name} from past 2 days...")
    
    # Get articles from past 2 days
    conn = sqlite3.connect('data/news_monitor.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, s.name as source_name 
        FROM articles a 
        JOIN sources s ON a.source_id = s.id 
        WHERE a.user_id = ? AND a.created_at >= ?
        ORDER BY a.created_at DESC
    ''', (user_id, two_days_ago.isoformat()))
    
    articles = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(articles)} articles for {name} from past 2 days")
    
    if articles:
        # Send header message
        header_message = f"📰 **Articles from the past 2 days** ({len(articles)} articles)\n\n"
        header_message += f"Here are your news articles from {two_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}:"
        
        data = {'chat_id': chat_id, 'text': header_message}
        response = requests.post(api_url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Header sent to {name}")
        else:
            print(f"❌ Error sending header to {name}: {result}")
        
        time.sleep(1)
        
        # Send articles
        for article in articles:
            message = f"*New Article*\n\n"
            message += f"📍 Source: {article[7]}\n"
            message += f"📝 Title: {article[3]}\n"
            
            if article[4]:
                message += f"📄 Summary: {article[4]}\n\n"
            else:
                message += "\n"
            
            message += f"🔗 [Read more]({article[2]})"
            message += f"\n\n📅 Date: {article[6]}"
            
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(api_url, json=data)
            result = response.json()
            
            if result.get('ok'):
                print(f"Sent to {name}: {article[3][:50]}...")
            else:
                print(f"Error sending to {name}: {result}")
            
            time.sleep(1)
    else:
        no_articles = f"📰 No articles found for {name} from the past 2 days."
        data = {'chat_id': chat_id, 'text': no_articles}
        requests.post(api_url, json=data)
        print(f"No articles for {name}")

print("\n✅ Articles from past 2 days sent to both users")
