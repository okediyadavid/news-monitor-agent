import os
import sqlite3
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Users
users = [
    {'name': 'Dave', 'user_id': 1, 'chat_id': '1287986887'},
    {'name': 'Joshua', 'user_id': 3, 'chat_id': '2016570012'}
]

api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

today = datetime.now().strftime('%Y-%m-%d')

for user in users:
    user_id = user['user_id']
    chat_id = user['chat_id']
    name = user['name']
    
    print(f"\nSending morning message to {name}...")
    
    # Send good morning message
    morning_message = f"☀️ Good morning, {name}!\n\n"
    morning_message += f"Hope you have a productive day ahead! 🚀\n\n"
    morning_message += f"Here are your news articles for {today}:"
    
    data = {'chat_id': chat_id, 'text': morning_message}
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Morning message sent to {name}")
    else:
        print(f"❌ Error sending morning message to {name}: {result}")
    
    # Get today's articles
    conn = sqlite3.connect('data/news_monitor.db')
    cursor = conn.cursor()
    
    threshold = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    cursor.execute('''
        SELECT a.*, s.name as source_name 
        FROM articles a 
        JOIN sources s ON a.source_id = s.id 
        WHERE a.user_id = ? AND a.created_at >= ?
        ORDER BY a.created_at DESC
        LIMIT 5
    ''', (user_id, threshold.strftime('%Y-%m-%d %H:%M:%S')))
    
    articles = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(articles)} articles for {name} today")
    
    if articles:
        for article in articles:
            message = f"*New Article*\n\n"
            message += f"📍 Source: {article[7]}\n"
            message += f"📝 Title: {article[3]}\n"
            
            pub_date = article[5]
            if pub_date:
                try:
                    if isinstance(pub_date, str):
                        dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    else:
                        dt = pub_date
                    message += f"🕐 Published: {dt.strftime('%Y-%m-%d %H:%M')}\n"
                except:
                    message += f"🕐 Published: {pub_date}\n"
            
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
                print(f"Sent to {name}: {article[3][:50]}...")
            else:
                print(f"Error sending to {name}: {result}")
            
            import time
            time.sleep(1)
    else:
        # If no today's articles, get latest articles
        conn = sqlite3.connect('data/news_monitor.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, s.name as source_name 
            FROM articles a 
            JOIN sources s ON a.source_id = s.id 
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
            LIMIT 5
        ''', (user_id,))
        
        articles = cursor.fetchall()
        conn.close()
        
        if articles:
            message = f"📰 Here are the latest articles ({len(articles)}):"
            data = {'chat_id': chat_id, 'text': message}
            requests.post(api_url, json=data)
            
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
                    print(f"Sent to {name}: {article[3][:50]}...")
                else:
                    print(f"Error sending to {name}: {result}")
                
                time.sleep(1)
        else:
            no_articles = "📰 No articles available at the moment."
            data = {'chat_id': chat_id, 'text': no_articles}
            requests.post(api_url, json=data)
            print(f"No articles for {name}")

print("\n✅ Morning messages and articles sent to both users")
