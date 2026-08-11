import sqlite3
from datetime import datetime
import os

# Get today's date
today = datetime.now().strftime('%Y-%m-%d')

print(f"Testing interest feature for {today}")

# Get recent articles for Dave (user_id = 1)
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT a.id, a.title, a.summary, s.name as source_name
    FROM articles a
    JOIN sources s ON a.source_id = s.id
    WHERE a.user_id = 1
    ORDER BY a.created_at DESC
    LIMIT 5
''')

dave_articles = cursor.fetchall()

print(f"\nDave's recent articles ({len(dave_articles)}):")
for article in dave_articles:
    print(f"ID: {article[0]}, Title: {article[1][:50]}...")

# Get recent articles for Joshua (user_id = 3)
cursor.execute('''
    SELECT a.id, a.title, a.summary, s.name as source_name
    FROM articles a
    JOIN sources s ON a.source_id = s.id
    WHERE a.user_id = 3
    ORDER BY a.created_at DESC
    LIMIT 5
''')

joshua_articles = cursor.fetchall()

print(f"\nJoshua's recent articles ({len(joshua_articles)}):")
for article in joshua_articles:
    print(f"ID: {article[0]}, Title: {article[1][:50]}...")

# Mark 2 articles for Dave
if dave_articles:
    for i in range(min(2, len(dave_articles))):
        article_id = dave_articles[i][0]
        title = dave_articles[i][1]
        summary = dave_articles[i][2]
        
        cursor.execute('''
            INSERT INTO user_interests (user_id, article_id, summary)
            VALUES (?, ?, ?)
        ''', (1, article_id, summary))
        
        print(f"✅ Marked Dave's article {article_id} as interesting: {title[:50]}...")

# Mark 2 articles for Joshua
if joshua_articles:
    for i in range(min(2, len(joshua_articles))):
        article_id = joshua_articles[i][0]
        title = joshua_articles[i][1]
        summary = joshua_articles[i][2]
        
        cursor.execute('''
            INSERT INTO user_interests (user_id, article_id, summary)
            VALUES (?, ?, ?)
        ''', (3, article_id, summary))
        
        print(f"✅ Marked Joshua's article {article_id} as interesting: {title[:50]}...")

conn.commit()
conn.close()

print(f"\n✅ Test articles marked as interesting for both users")
