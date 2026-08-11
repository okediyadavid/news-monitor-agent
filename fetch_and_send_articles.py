import os
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from scraper import WebScraper

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Users
users = [
    {'name': 'Dave', 'user_id': 1, 'chat_id': '1287986887'},
    {'name': 'Joshua', 'user_id': 3, 'chat_id': '2016570012'}
]

scraper = WebScraper()

for user in users:
    user_id = user['user_id']
    chat_id = user['chat_id']
    name = user['name']
    
    print(f"\nFetching articles for {name}...")
    
    # Get user's sources
    conn = sqlite3.connect('data/news_monitor.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sources WHERE user_id = ? AND enabled = 1', (user_id,))
    sources = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(sources)} sources for {name}")
    
    total_new_articles = 0
    
    for source in sources:
        source_id = source[0]
        source_name = source[2]
        source_url = source[3]
        
        print(f"Checking {source_name}...")
        
        try:
            articles = scraper.scrape_articles(source_url, source_name)
            print(f"Found {len(articles)} articles from {source_name}")
            
            # Save articles to database
            conn = sqlite3.connect('data/news_monitor.db')
            cursor = conn.cursor()
            
            for article in articles:
                # Check if article already exists
                url_hash = hash(article['url'])
                cursor.execute('SELECT 1 FROM articles WHERE url_hash = ? AND user_id = ?', (str(url_hash), user_id))
                if cursor.fetchone():
                    continue
                
                # Handle None values
                title = article.get('title') or 'No title'
                summary = article.get('summary') or ''
                
                # Insert article
                cursor.execute('''
                    INSERT INTO articles (user_id, source_id, title, url, url_hash, summary, publication_date, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    source_id,
                    title,
                    article.get('url', ''),
                    str(url_hash),
                    summary,
                    article.get('publication_date'),
                    hash(title + summary)
                ))
                total_new_articles += 1
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error checking {source_name}: {e}")
    
    print(f"Total new articles for {name}: {total_new_articles}")
    
    # Get recent articles to send
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
    
    # Send articles to user
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    if articles:
        message = f"📰 Here are the latest articles for you ({len(articles)}):"
        data = {'chat_id': chat_id, 'text': message}
        requests.post(api_url, json=data)
        
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
        print(f"No articles to send to {name}")

print("\n✅ Finished fetching and sending articles to all users")
