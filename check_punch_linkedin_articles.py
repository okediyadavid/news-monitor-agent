import sqlite3

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Check all punchng/linkedin articles for Dave
cursor.execute('''
    SELECT a.id, a.title, s.name as source_name, a.created_at
    FROM articles a
    JOIN sources s ON a.source_id = s.id
    WHERE a.user_id = 1 
    AND (s.name LIKE '%punch%' OR s.name LIKE '%linkedin%')
    ORDER BY a.created_at DESC
    LIMIT 20
''')

articles = cursor.fetchall()

print(f"Total punchng/linkedin articles for Dave: {len(articles)}")
if articles:
    for article in articles:
        print(f"ID: {article[0]}, Title: {article[1]}, Source: {article[2]}, Created: {article[3]}")
else:
    print("No punchng/linkedin articles found for Dave")

conn.close()
