import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Check all articles with their dates
cursor.execute('''
    SELECT a.id, a.user_id, a.title, a.created_at, s.name as source_name
    FROM articles a 
    JOIN sources s ON a.source_id = s.id 
    ORDER BY a.created_at DESC
    LIMIT 20
''')

articles = cursor.fetchall()

print(f"Total articles in database: {len(articles)}")
print("\nRecent articles:")
for article in articles:
    user_id = article[1]
    user_name = "Dave" if user_id == 1 else "Joshua" if user_id == 3 else "Unknown"
    print(f"User: {user_name} | Source: {article[4]} | Title: {article[2][:50]}... | Date: {article[3]}")

conn.close()
