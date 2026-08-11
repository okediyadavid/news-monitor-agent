import os
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from scraper import WebScraper
from rss import RSSParser

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = '2016570012'  # Joshua's chat ID

# Get Joshua's sources
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM sources WHERE user_id = 3')
sources = cursor.fetchall()
conn.close()

print(f"Checking {len(sources)} sources for Joshua...")

scraper = WebScraper()
rss_parser = RSSParser()

total_articles = 0

for source in sources:
    source_id = source[0]
    source_name = source[2]
    source_url = source[3]
    source_type = source[4]
    
    print(f"Checking {source_name}...")
    
    try:
        articles = []
        
        if source_type == 'rss':
            articles = rss_parser.parse_rss(source_url)
        else:
            articles = scraper.scrape_articles(source_url, source_name)
        
        print(f"Found {len(articles)} articles from {source_name}")
        
        # Save articles to database for Joshua
        conn = sqlite3.connect('data/news_monitor.db')
        cursor = conn.cursor()
        
        for article in articles:
            # Check if article already exists
            url_hash = hash(article['url'])
            cursor.execute('SELECT 1 FROM articles WHERE url_hash = ? AND user_id = 3', (str(url_hash),))
            if cursor.fetchone():
                continue
            
            # Handle None values for title and summary
            title = article.get('title') or 'No title'
            summary = article.get('summary') or ''
            
            # Insert article
            cursor.execute('''
                INSERT INTO articles (user_id, source_id, title, url, url_hash, summary, publication_date, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                3,
                source_id,
                title,
                article.get('url', ''),
                str(url_hash),
                summary,
                article.get('publication_date'),
                hash(title + summary)
            ))
            total_articles += 1
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error checking {source_name}: {e}")

print(f"Total articles saved for Joshua: {total_articles}")

# Now send articles to Joshua
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT a.*, s.name as source_name 
    FROM articles a 
    JOIN sources s ON a.source_id = s.id 
    WHERE a.user_id = 3 
    ORDER BY a.created_at DESC 
    LIMIT 10
''')
articles = cursor.fetchall()
conn.close()

print(f"Sending {len(articles)} articles to Joshua...")

api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

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
        print(f"Sent: {article[3][:50]}...")
    else:
        print(f"Error: {result}")
    
    import time
    time.sleep(1)

print(f"Finished sending {len(articles)} articles to Joshua")
