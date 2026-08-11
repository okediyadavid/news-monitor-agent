import sqlite3

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Remove punchng (ID: 5) and Linkedin (ID: 6) from Dave (user_id: 1)
cursor.execute('DELETE FROM sources WHERE user_id = 1 AND id IN (5, 6)')

conn.commit()
conn.close()

print("✅ Removed punchng and Linkedin from Dave's sources")
