import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from scraper import WebScraper
from rss import RSSParser

load_dotenv()

# Get all users
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, telegram_chat_id FROM users')
users = cursor.fetchall()

print(f"Found {len(users)} users")
print("=" * 60)

scraper = WebScraper()
rss_parser = RSSParser()

# 48 hours ago
forty_eight_hours_ago = datetime.now() - timedelta(hours=48)

for user in users:
    user_id, user_name, chat_id = user
    print(f"\nProcessing {user_name}...")
    
    # Get user's sources
    cursor.execute('SELECT id, name, url FROM sources WHERE user_id = ? AND enabled = 1', (user_id,))
    sources = cursor.fetchall()
    
    print(f"  Found {len(sources)} sources")
    
    for source in sources:
        source_id, source_name, source_url = source
        print(f"\n  Fetching from {source_name}...")
        
        try:
            # Use web scraping directly
            articles = scraper.scrape_articles(source_url, source_name)
            
            if articles:
                new_articles_count = 0
                for article in articles:
                    article_url = article.get('url', '')
                    url_hash = hashlib.md5(article_url.encode()).hexdigest()
                    
                    # Check if article already exists
                    cursor.execute('''
                        SELECT id FROM articles 
                        WHERE user_id = ? AND url_hash = ?
                    ''', (user_id, url_hash))
                    
                    existing = cursor.fetchone()
                    
                    if not existing:
                        cursor.execute('''
                            INSERT INTO articles (user_id, source_id, url, url_hash, title, summary, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                        ''', (user_id, source_id, article_url, url_hash,
                              article.get('title', ''), article.get('summary', '')))
                        new_articles_count += 1
                
                print(f"    ✅ Fetched {len(articles)} articles ({new_articles_count} new)")
            else:
                print(f"    ⚠️ No articles found")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")

conn.commit()

# Now send articles from past 48 hours
print("\n" + "=" * 60)
print("Sending articles from past 48 hours...")

import requests
import time

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

for user in users:
    user_id, user_name, chat_id = user
    
    print(f"\nProcessing {user_name}...")
    
    # Get articles from past 48 hours
    cursor.execute('''
        SELECT a.*, s.name as source_name 
        FROM articles a 
        JOIN sources s ON a.source_id = s.id 
        WHERE a.user_id = ? AND a.created_at >= ?
        ORDER BY a.created_at DESC
    ''', (user_id, forty_eight_hours_ago.isoformat()))
    
    articles = cursor.fetchall()
    
    print(f"  Found {len(articles)} articles from past 48 hours")
    
    if articles:
        # Send header message
        header_message = f"📰 **Fresh Articles (Past 48 Hours)** ({len(articles)} articles)\n\n"
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
        print(f"  No articles found from past 48 hours")

conn.close()

print("\n" + "=" * 60)
print("✅ Fresh articles fetched and sent to all users")
