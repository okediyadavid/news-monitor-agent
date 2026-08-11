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

# Keywords to search for
keywords = ['tech', 'bitcoin', 'money', 'jobs', 'AI', 'artificial intelligence', 'finance', 'crypto', 'employment', 'career', 'technology', 'investment', 'startup', 'fintech']

# Get Joshua's sources
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM sources WHERE user_id = 3')
sources = cursor.fetchall()
conn.close()

print(f"Fetching fresh articles from {len(sources)} sources for Joshua...")

scraper = WebScraper()
rss_parser = RSSParser()

total_new_articles = 0

for source in sources:
    source_id = source[0]
    source_name = source[2]
    source_url = source[3]
    source_type = source[4]
    
    print(f"Fetching from {source_name}...")
    
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
            
            # Handle None values
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
            total_new_articles += 1
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error checking {source_name}: {e}")

print(f"Total new articles saved: {total_new_articles}")

# Now get all articles and filter by keywords
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT a.*, s.name as source_name 
    FROM articles a 
    JOIN sources s ON a.source_id = s.id 
    WHERE a.user_id = 3 
    ORDER BY a.created_at DESC
''')

all_articles = cursor.fetchall()
conn.close()

print(f"Total articles in database: {len(all_articles)}")

# Filter articles by keywords
filtered_articles = []
for article in all_articles:
    title = article[3].lower()
    summary = article[4].lower() if article[4] else ''
    
    for keyword in keywords:
        if keyword.lower() in title or keyword.lower() in summary:
            filtered_articles.append(article)
            break

print(f"Articles matching keywords: {len(filtered_articles)}")

# Remove duplicates
seen_urls = set()
unique_articles = []
for article in filtered_articles:
    url = article[2]
    if url not in seen_urls:
        seen_urls.add(url)
        unique_articles.append(article)

print(f"Unique articles: {len(unique_articles)}")

# Send articles to Joshua
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

sent_count = 0
for article in unique_articles[:20]:  # Limit to 20 articles
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
        sent_count += 1
    else:
        print(f"Error: {result}")
    
    import time
    time.sleep(1)

print(f"Finished sending {sent_count} articles to Joshua")
