import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# Users
users = [
    {'name': 'Dave', 'chat_id': '1287986887'},
    {'name': 'Joshua', 'chat_id': '2016570012'}
]

message = """🎉 **Bot Successfully Deployed!**

Your news monitoring bot is now live and running 24/7 on Render!

**What you need to do:**
Since this is a fresh deployment, you'll need to register again:

1. Send /start to begin
2. Send /register [your name] to create your account
3. Add your news sources with /addsource

**Your previous sources were:**

Dave's Sources:
• CNBC Africa - https://www.cnbcafrica.com/
• Cryptopolitan - https://www.cryptopolitan.com/
• Nairametrics - https://nairametrics.com/
• TechNext24 - https://technext24.com/
• Today Africa - https://todayafrica.co/

Joshua's Sources:
• CNBC Africa - https://www.cnbcafrica.com/
• Cryptopolitan - https://www.cryptopolitan.com/
• Fintech News Africa - https://fintechnews.africa
• Fintech Weekly - https://www.fintechweekly.com/
• Nairametrics - https://nairametrics.com/
• TechNext24 - https://technext24.com/
• Today Africa - https://todayafrica.co/

**Bot Features:**
✅ Automatic article delivery every 6 hours
✅ 24/7 operation
✅ All your favorite news sources

Please register now to continue receiving your news updates! 📰"""

for user in users:
    chat_id = user['chat_id']
    name = user['name']
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Message sent to {name}")
    else:
        print(f"❌ Error sending to {name}: {result}")

print("\n✅ All users notified")
