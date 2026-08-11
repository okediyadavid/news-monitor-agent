"""
Test script to debug bot functionality
"""
import requests
import time

bot_token = "8970886831:AAHuy36lTXx_4s4WM1RAlqo-adnlraM_vLk"
api_url = f"https://api.telegram.org/bot{bot_token}"

# Send a test command
print("Sending /start command...")
response = requests.post(f"{api_url}/sendMessage", json={'chat_id': 1287986887, 'text': '/start'})
print(f"Response: {response.json()}")

# Wait a moment
time.sleep(2)

# Check for updates
print("\nChecking for updates...")
response = requests.get(f"{api_url}/getUpdates")
data = response.json()
print(f"Updates: {data}")

# Check if bot responded
if data.get('ok'):
    updates = data.get('result', [])
    print(f"\nTotal updates: {len(updates)}")
    for update in updates:
        print(f"Update: {update}")
