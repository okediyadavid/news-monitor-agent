import sqlite3

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Find and delete duplicate articles (keep the oldest one)
cursor.execute('''
    DELETE FROM articles 
    WHERE id NOT IN (
        SELECT MIN(id) 
        FROM articles 
        GROUP BY url_hash
    )
''')

deleted_count = cursor.rowcount
print(f"Deleted {deleted_count} duplicate articles")

# Check for articles with NULL source_id
cursor.execute('''
    SELECT COUNT(*) FROM articles WHERE source_id IS NULL
''')
null_source_count = cursor.fetchone()[0]
print(f"Found {null_source_count} articles with NULL source_id")

conn.commit()
conn.close()

print("✅ Database cleanup completed")
