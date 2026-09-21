import sqlite3

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Check articles with source info
cursor.execute('''
    SELECT a.id, u.name as user_name, s.name as source_name, a.title, a.url, a.created_at
    FROM articles a
    JOIN users u ON a.user_id = u.id
    LEFT JOIN sources s ON a.source_id = s.id
    ORDER BY a.created_at DESC
    LIMIT 20
''')

articles = cursor.fetchall()

print("Recent articles with source info:")
print("=" * 80)
for article in articles:
    article_id, user_name, source_name, title, url, created_at = article
    print(f"ID: {article_id} | User: {user_name} | Source: {source_name or 'NONE'}")
    print(f"Title: {title[:60]}...")
    print(f"URL: {url[:60]}...")
    print(f"Created: {created_at}")
    print("-" * 80)

# Check for duplicate URLs
cursor.execute('''
    SELECT url, COUNT(*) as count
    FROM articles
    GROUP BY url
    HAVING count > 1
    ORDER BY count DESC
    LIMIT 10
''')

duplicates = cursor.fetchall()

print("\nDuplicate URLs found:")
print("=" * 80)
for url, count in duplicates:
    print(f"URL: {url[:60]}... | Count: {count}")

conn.close()
