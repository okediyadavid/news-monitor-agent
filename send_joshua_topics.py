import os
import sqlite3
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = '2016570012'  # Joshua's chat ID

# Keywords to search for
keywords = ['tech', 'bitcoin', 'money', 'jobs', 'AI', 'artificial intelligence', 'finance', 'crypto', 'employment', 'career']

# Get articles from past 24 hours
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

cursor.execute('''
    SELECT a.*, s.name as source_name 
    FROM articles a 
    JOIN sources s ON a.source_id = s.id 
    WHERE a.user_id = 3 
    AND a.created_at >= ?
    ORDER BY a.created_at DESC
''', (twenty_four_hours_ago,))

all_articles = cursor.fetchall()
conn.close()

print(f"Found {len(all_articles)} articles from past 24 hours")

# Filter articles by keywords
filtered_articles = []
for article in all_articles:
    title = article[3].lower()
    summary = article[4].lower() if article[4] else ''
    
    for keyword in keywords:
        if keyword.lower() in title or keyword.lower() in summary:
            filtered_articles.append(article)
            break

print(f"Found {len(filtered_articles)} articles matching keywords")

# Remove duplicates
seen_urls = set()
unique_articles = []
for article in filtered_articles:
    url = article[2]
    if url not in seen_urls:
        seen_urls.add(url)
        unique_articles.append(article)

print(f"Found {len(unique_articles)} unique articles")

# Send articles to Joshua
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

for article in unique_articles[:15]:  # Limit to 15 articles
    message = f"*Article*\n\n"
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
        print(f"Sent: {article[3][:50]}...")
    else:
        print(f"Error: {result}")
    
    import time
    time.sleep(1)

print(f"Finished sending {len(unique_articles[:15])} articles to Joshua")
