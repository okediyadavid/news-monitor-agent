import sqlite3

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Check all users and their sources
cursor.execute('''
    SELECT u.id, u.name, s.name as source_name, s.url, s.rss_url, s.enabled
    FROM users u
    JOIN sources s ON u.id = s.user_id
    ORDER BY u.id, s.name
''')

user_sources = cursor.fetchall()

print("User Sources Configuration:")
print("=" * 60)

current_user = None
for row in user_sources:
    user_id = row[0]
    user_name = row[1]
    source_name = row[2]
    source_url = row[3]
    rss_url = row[4]
    enabled = row[5]
    
    if user_name != current_user:
        print(f"\n{user_name} (ID: {user_id}):")
        current_user = user_name
    
    status = "✓ Enabled" if enabled else "✗ Disabled"
    print(f"  - {source_name} [{status}]")
    if rss_url:
        print(f"    RSS: {rss_url}")
    else:
        print(f"    URL: {source_url}")

conn.close()
