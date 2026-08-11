"""
Script to make a user an admin
"""
import sqlite3
import os

db_path = "data/news_monitor.db"

# Recreate database with new schema
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed existing database: {db_path}")

# Initialize database
from database import DatabaseManager
db = DatabaseManager(db_path)
print("Database initialized with admin role support")

# Update user to admin (chat_id: 1287986887)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if user exists
cursor.execute("SELECT id, email FROM users WHERE telegram_chat_id = ?", ('1287986887',))
user = cursor.fetchone()

if user:
    user_id, email = user
    cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
    conn.commit()
    print(f"✅ User {email} (ID: {user_id}) is now an admin")
else:
    print("❌ User not found. Please register first with the bot.")

conn.close()
