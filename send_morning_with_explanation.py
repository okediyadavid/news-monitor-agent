import os
import sqlite3
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Users
users = [
    {'name': 'Dave', 'user_id': 1, 'chat_id': '1287986887'},
    {'name': 'Joshua', 'user_id': 3, 'chat_id': '2016570012'}
]

for user in users:
    user_id = user['user_id']
    chat_id = user['chat_id']
    name = user['name']
    
    print(f"\nSending morning message to {name}...")
    
    # Send morning message with explanation
    morning_message = f"☀️ Good morning, {name}!\n\n"
    morning_message += f"I hope you're having a great day! 🌟\n\n"
    morning_message += f"🔧 **Important Update:**\n\n"
    morning_message += f"I want to apologize for the network connectivity issues we experienced yesterday. The bot had some technical difficulties with Telegram API connectivity, which may have caused delays or missed responses to your commands.\n\n"
    morning_message += f"I'm actively working on improving the network stability and ensuring better connectivity going forward. This issue is being addressed to provide you with a more reliable experience.\n\n"
    morning_message += f"Thank you for your patience and understanding! 🙏\n\n"
    morning_message += f"Here are your news articles for today:"
    
    data = {'chat_id': chat_id, 'text': morning_message}
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Morning message sent to {name}")
    else:
        print(f"❌ Error sending morning message to {name}: {result}")
    
    # Get latest articles (at least 10)
    conn = sqlite3.connect('data/news_monitor.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, s.name as source_name 
        FROM articles a 
        JOIN sources s ON a.source_id = s.id 
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        LIMIT 15
    ''', (user_id,))
    
    articles = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(articles)} articles for {name}")
    
    # Send at least 10 articles
    articles_to_send = articles[:10] if len(articles) >= 10 else articles
    
    if articles_to_send:
        message = f"📰 Here are today's articles ({len(articles_to_send)}):"
        data = {'chat_id': chat_id, 'text': message}
        requests.post(api_url, json=data)
        
        for article in articles_to_send:
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
