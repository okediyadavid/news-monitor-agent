import sqlite3

# New source details
new_source = {
    'name': 'AllAfrica',
    'url': 'https://allafrica.com/',
    'type': 'website',
    'category': 'News'
}

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Get all users
cursor.execute('SELECT id, name FROM users')
users = cursor.fetchall()

print(f"Adding AllAfrica source to {len(users)} users...")

for user in users:
    user_id, user_name = user
    print(f"\nProcessing {user_name}...")
    
    # Check if source already exists for this user
    cursor.execute('''
        SELECT id FROM sources 
        WHERE user_id = ? AND name = ?
    ''', (user_id, new_source['name']))
    
    existing = cursor.fetchone()
    
    if not existing:
        # Add the source
        cursor.execute('''
            INSERT INTO sources (user_id, name, url, type, category, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
        ''', (user_id, new_source['name'], new_source['url'], 
              new_source['type'], new_source['category']))
        
        print(f"  ✅ Added: {new_source['name']}")
    else:
        print(f"  ⚠️ Already exists: {new_source['name']}")

conn.commit()
print("\n✅ AllAfrica source added to all users")
conn.close()
