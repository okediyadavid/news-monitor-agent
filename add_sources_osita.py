import sqlite3

# Joshua's additional sources that Osita doesn't have
additional_sources = [
    {'name': 'Fintech News Africa', 'url': 'https://fintechnews.africa', 'type': 'website', 'category': 'Finance'},
    {'name': 'Fintech Weekly', 'url': 'https://www.fintechweekly.com/', 'type': 'website', 'category': 'Finance'},
    {'name': 'Nairametrics', 'url': 'https://nairametrics.com/', 'type': 'website', 'category': 'Finance'}
]

conn = sqlite3.connect('data/news_monitor.db')
cursor = conn.cursor()

# Get Osita's user ID
cursor.execute('SELECT id FROM users WHERE name = "Osita Nwana"')
user = cursor.fetchone()

if user:
    user_id = user[0]
    print(f"Adding sources to Osita Nwana (ID: {user_id})...")
    
    for source in additional_sources:
        # Check if source already exists for this user
        cursor.execute('''
            SELECT id FROM sources 
            WHERE user_id = ? AND name = ?
        ''', (user_id, source['name']))
        
        existing = cursor.fetchone()
        
        if not existing:
            # Add the source
            cursor.execute('''
                INSERT INTO sources (user_id, name, url, type, category, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
            ''', (user_id, source['name'], source['url'], source['type'], source['category']))
            
            print(f"  ✅ Added: {source['name']}")
        else:
            print(f"  ⚠️ Already exists: {source['name']}")
    
    conn.commit()
    print("\n✅ Sources added successfully")
else:
    print("❌ User Osita Nwana not found")

conn.close()
