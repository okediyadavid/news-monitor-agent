import os
import requests
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

# Users to notify
users = [
    {'name': 'Joshua', 'chat_id': '2016570012'},
    {'name': 'Dave', 'chat_id': '1287986887'}
]

api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

for user in users:
    name = user['name']
    chat_id = user['chat_id']
    
    message = f"🎉 New Features Added to Your News Bot!\n\n"
    message += f"Hey {name}, I've added some exciting new features to help you organize and save the news articles that interest you most:\n\n"
    message += "📝 **Interest Catalog**\n"
    message += "• /interest [article_id] - Mark articles you find interesting\n"
    message += "• /myinterests [date] - View your daily interests (default: today)\n"
    message += "• /uninterest [article_id] - Remove articles from your interests\n"
    message += "• /exportdaily [date] - Generate a Word document with your daily interests\n\n"
    message += "🤖 **AI-Powered Summaries**\n"
    message += "When you mark an article as interesting, the bot automatically generates an AI summary using OpenAI GPT-3.5-turbo to help you remember key points!\n\n"
    message += "📄 **Word Document Export**\n"
    message += "Generate beautifully formatted Word documents containing all your interests for any day, complete with:\n"
    message += "• Article titles and sources\n"
    message += "• Original summaries\n"
    message += "• AI-generated summaries (highlighted in blue)\n"
    message += "• Direct links to articles\n\n"
    message += "💡 **How to Use**\n"
    message += "1. When you receive an article you like, use /interest [article_id]\n"
    message += "2. View your daily interests with /myinterests\n"
    message += "3. Export as Word document with /exportdaily\n"
    message += "4. Remove items you no longer want with /uninterest [article_id]\n\n"
    message += "Type /help to see all available commands.\n\n"
    message += "Enjoy organizing your news! 🚀"
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(api_url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ New features notification sent to {name}")
    else:
        print(f"❌ Error sending to {name}: {result}")
