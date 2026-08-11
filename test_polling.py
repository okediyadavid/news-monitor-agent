"""
Test the polling mechanism directly
"""
import requests
import time

bot_token = "8970886831:AAHuy36lTXx_4s4WM1RAlqo-adnlraM_vLk"
api_url = f"https://api.telegram.org/bot{bot_token}"

offset = 0

print("Starting polling test...")
print("Send /start to your bot now!")

for i in range(10):
    try:
        params = {'offset': offset, 'timeout': 5}
        response = requests.get(f"{api_url}/getUpdates", params=params, timeout=10)
        data = response.json()
        
        print(f"\nAttempt {i+1}:")
        print(f"Offset: {offset}")
        print(f"Response: {data}")
        
        if data.get('ok'):
            updates = data.get('result', [])
            if updates:
                print(f"Got {len(updates)} updates!")
                offset = updates[-1]['update_id'] + 1
                print(f"New offset: {offset}")
                for update in updates:
                    print(f"Update: {update}")
            else:
                print("No updates")
        else:
            print(f"Error: {data}")
        
        time.sleep(2)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)

print("Polling test complete")
