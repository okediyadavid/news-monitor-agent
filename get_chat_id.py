"""
Simple script to get your Telegram chat ID using your bot token.
"""

import requests

BOT_TOKEN = "8970886831:AAHuy36lTXx_4s4WM1RAlqo-adnlraM_vLk"

print("Getting your chat ID...")
print("Please send a message to your bot on Telegram first (any message like 'Hello')")
print("Then press Enter to continue...")
input()

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    if data.get('ok'):
        updates = data.get('result', [])
        if updates:
            for update in updates:
                chat_id = update.get('message', {}).get('chat', {}).get('id')
                if chat_id:
                    print(f"\n✓ Your Chat ID: {chat_id}")
                    print("\nAdd this to your .env file:")
                    print(f"TELEGRAM_CHAT_ID={chat_id}")
                    break
            else:
                print("No messages found. Please send a message to your bot first.")
        else:
            print("No updates found. Please send a message to your bot first.")
    else:
        print(f"Error: {data.get('description')}")
else:
    print(f"HTTP Error: {response.status_code}")
