import sqlite3

# Add Nairametrics to both users
conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Add to Dave (user_id = 1)
cursor.execute('''
    INSERT INTO sources (user_id, name, url, type, category, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
''', (1, 'Nairametrics', 'https://nairametrics.com/', 'website', 'Finance', 1))

# Add to Joshua (user_id = 3)
cursor.execute('''
    INSERT INTO sources (user_id, name, url, type, category, enabled)
    VALUES (?, ?, ?, ?, ?, ?)
''', (3, 'Nairametrics', 'https://nairametrics.com/', 'website', 'Finance', 1))

conn.commit()
conn.close()

print("✅ Nairametrics added to both Dave and Joshua")
