import sqlite3

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", [table[0] for table in tables])

# Check if users table exists and has structure
if any('users' in table for table in tables):
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("Users table structure:", columns)
else:
    print("Users table does not exist!")

conn.close()
