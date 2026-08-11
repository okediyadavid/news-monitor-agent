import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Get the timestamp for 48 hours ago
forty_eight_hours_ago = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

# First, check what articles will be deleted
cursor.execute('''
    SELECT a.id, a.title, s.name as source_name, a.created_at
    FROM articles a
    JOIN sources s ON a.source_id = s.id
    WHERE a.user_id = 1 
    AND (s.name LIKE '%punch%' OR s.name LIKE '%linkedin%')
    AND a.created_at >= ?
    ORDER BY a.created_at DESC
''', (forty_eight_hours_ago,))

articles_to_delete = cursor.fetchall()

print(f"Found {len(articles_to_delete)} articles from punchng/linkedin in past 48 hours:")
for article in articles_to_delete:
    print(f"ID: {article[0]}, Title: {article[1]}, Source: {article[2]}, Created: {article[3]}")

if articles_to_delete:
    # Delete the articles
    article_ids = [str(article[0]) for article in articles_to_delete]
    placeholders = ','.join(['?' for _ in article_ids])
    
    cursor.execute(f'''
        DELETE FROM articles 
        WHERE id IN ({placeholders}) AND user_id = 1
    ''', article_ids)
    
    conn.commit()
    print(f"\n✅ Deleted {len(articles_to_delete)} articles from punchng/linkedin")
else:
    print("\nNo articles found to delete")

conn.close()
