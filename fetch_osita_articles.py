import os
import sqlite3
import hashlib
from dotenv import load_dotenv
from scraper import WebScraper
from rss import RSSParser

load_dotenv()

# Get Osita's user info
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name FROM users WHERE name = "Osita Nwana"')
user = cursor.fetchone()

if user:
    user_id, user_name = user
    print(f"Fetching articles for {user_name}...")
    
    # Get Osita's sources
    cursor.execute('SELECT id, name, url FROM sources WHERE user_id = ? AND enabled = 1', (user_id,))
    sources = cursor.fetchall()
    
    print(f"Found {len(sources)} sources")
    
    scraper = WebScraper()
    rss_parser = RSSParser()
    
    for source in sources:
        source_id, source_name, source_url = source
        print(f"\nFetching from {source_name}...")
        
        try:
            # Use web scraping directly (RSS feeds not available for these URLs)
            articles = scraper.scrape_articles(source_url, source_name)
            
            if articles:
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
                
                print(f"  ✅ Fetched {len(articles)} articles")
            else:
                print(f"  ⚠️ No articles found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    conn.commit()
    print(f"\n✅ Articles fetched and saved for {user_name}")
else:
    print("❌ User Osita Nwana not found")

conn.close()
