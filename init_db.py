import os
from database import DatabaseManager

# Remove existing database
db_path = "data/news_monitor.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed existing database: {db_path}")

# Create new database with updated schema
db = DatabaseManager(db_path)
print("Database initialized with new schema")

# Verify users table exists
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables created: {tables}")

if 'users' in tables:
    print("✓ Users table created successfully")
else:
    print("✗ Users table NOT created")

conn.close()
