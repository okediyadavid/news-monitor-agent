# News Monitor Agent

A Python application that monitors news sources and sends notifications about newly published articles via Telegram bot.

## Features

- **Multi-user Telegram Bot**: Interactive bot commands for user management
- **Multi-source support**: Monitor RSS feeds, news websites, and blogs
- **Automatic scheduling**: Checks sources every 6 hours (configurable)
- **Duplicate detection**: Prevents duplicate notifications using SQLite database
- **Telegram notifications**: Sends formatted article updates via Telegram bot
- **Concurrent processing**: Checks multiple sources simultaneously for efficiency
- **Extensible design**: Easy to add new notification channels (Slack, Email, etc.)
- **Web scraping**: Falls back to web scraping when RSS is not available
- **Error handling**: Retries failed requests with exponential backoff
- **Comprehensive logging**: Tracks all operations for debugging

## Project Structure

```
news-monitor-agent/
├── app.py              # Main application entry point
├── database.py         # SQLite database management
├── rss.py              # RSS/Atom feed parser
├── scraper.py          # Web scraper for non-RSS sources
├── notifier.py         # Notification channels (Telegram, etc.)
├── scheduler.py        # APScheduler-based task scheduler
├── config.json         # News sources configuration
├── .env.example        # Environment variables template
├── requirements.txt    # Python dependencies
├── logs/               # Application logs
├── data/               # SQLite database
└── tests/              # Unit tests
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download the project:
```bash
cd news-monitor-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Configure your environment variables in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
CHECK_INTERVAL_HOURS=6
DATABASE_PATH=data/news_monitor.db
LOG_LEVEL=INFO
LOG_FILE=logs/news_monitor.log
```

5. Configure news sources in `config.json`:
```json
{
  "sources": [
    {
      "name": "TechNext24",
      "url": "https://technext24.com/",
      "type": "website",
      "category": "Technology",
      "enabled": true,
      "rss_url": "https://technext24.com/feed/"
    }
  ]
}
```

## Telegram Bot Setup

1. Create a Telegram bot by messaging [@BotFather](https://t.me/botfather) on Telegram
2. Follow the instructions to create a new bot and obtain the API token
3. Get your chat ID:
   - Message your bot on Telegram
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response
4. Add the token and chat ID to your `.env` file

## Usage

### Telegram Bot (Recommended)

The easiest way to use the News Monitor Agent is through the Telegram bot. The bot supports multiple users and allows full management through chat commands.

#### Start the Bot

```bash
python bot.py
```

#### Bot Commands

**User Management**
- `/start` - Start the bot and see welcome message
- `/register your@email.com` - Register with your email
- `/help` - Show all available commands

**News Sources**
- `/addsource URL [name] [category]` - Add a new news source
  - Example: `/addsource https://techcrunch.com TechCrunch Technology`
- `/mysources` - View all your news sources
- `/removesource source_id` - Remove a news source

**Settings**
- `/setinterval hours` - Set check interval (1-24 hours)
  - Example: `/setinterval 3`

**Actions**
- `/checknow` - Check for new articles immediately
- `/stats` - View your statistics

#### How Others Can Use the Bot

1. **Share the bot**: Share your Telegram bot username with others
2. **Registration**: New users register with `/register their@email.com`
3. **Add sources**: Each user adds their own news sources
4. **Personal notifications**: Each user receives notifications for their own sources

The bot automatically:
- Associates each user with their Telegram chat ID
- Separates data per user (sources, articles, notifications)
- Sends notifications to each user individually
- Allows users to manage their own settings

### Command Line Interface

You can also use the command line interface for direct management.

#### Start Automated Monitoring

```bash
python app.py
```

The agent will:
- Check all configured sources immediately on startup
- Continue checking every 6 hours (configurable)
- Send Telegram notifications for new articles
- Log all operations to `logs/news_monitor.log`

#### Run Once

Check all sources once without starting the scheduler:

```bash
python app.py --once
```

#### Add Source via CLI

```bash
python app.py --add-source "Source Name" "https://example.com" "website" --category "Technology"
```

#### View Statistics

Display monitoring statistics:

```bash
python app.py --stats
```

#### List Sources

List all configured news sources:

```bash
python app.py --list-sources
```

#### Custom Config File

Use a custom configuration file:

```bash
python app.py --config /path/to/config.json
```

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token | Required |
| `TELEGRAM_CHAT_ID` | Telegram chat ID to send notifications | Required |
| `CHECK_INTERVAL_HOURS` | Hours between checks | 6 |
| `DATABASE_PATH` | Path to SQLite database | data/news_monitor.db |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `LOG_FILE` | Path to log file | logs/news_monitor.log |
| `REQUEST_TIMEOUT` | HTTP request timeout in seconds | 30 |
| `MAX_RETRIES` | Maximum retry attempts for failed requests | 3 |
| `USER_AGENT` | User agent string for HTTP requests | Mozilla/5.0... |
| `MAX_WORKERS` | Maximum concurrent workers for source checking | 10 |

### Config File (config.json)

#### Sources Configuration

Each source requires:
- `name`: Display name
- `url`: Website URL
- `type`: Source type (rss, website, api)
- `category`: Category for organization
- `enabled`: Whether to check this source
- `rss_url`: RSS feed URL (optional)

#### Parsing Rules

Customize CSS selectors for web scraping:

```json
{
  "parsing_rules": {
    "default": {
      "article_selector": "article, .post, .entry",
      "title_selector": "h1, h2, .title",
      "link_selector": "a[href]",
      "date_selector": "time, .date",
      "summary_selector": "p, .excerpt",
      "image_selector": "img[src]"
    }
  }
}
```

#### Notification Settings

```json
{
  "notification_settings": {
    "send_images": true,
    "max_summary_length": 500,
    "batch_notifications": false
  }
}
```

## Adding News Sources

### Method 1: Edit config.json

Add a new source to the `sources` array in `config.json`:

```json
{
  "name": "News Site",
  "url": "https://example.com",
  "type": "website",
  "category": "News",
  "enabled": true,
  "rss_url": "https://example.com/feed/"
}
```

### Method 2: Programmatic (Future)

You can also add sources programmatically (requires implementing the full add_source method):

```python
from app import NewsMonitorAgent

agent = NewsMonitorAgent()
agent.add_source(
    name="News Site",
    url="https://example.com",
    source_type="website",
    category="News",
    rss_url="https://example.com/feed/"
)
```

## Database Schema

The SQLite database contains four tables:

- **sources**: News source configurations
- **articles**: Detected articles with metadata
- **notifications**: Notification history
- **scheduler_runs**: Scheduler execution logs

## Extensibility

### Adding New Notification Channels

The notification system is designed for extensibility. To add a new channel:

1. Create a new class inheriting from `NotificationChannel` in `notifier.py`
2. Implement the `send()` and `send_article()` methods
3. Add the channel to the `NotificationManager` in `app.py`

Example placeholders are provided for:
- Email (`EmailNotifier`)
- Slack (`SlackNotifier`)
- Discord, Microsoft Teams, etc.

### Future Enhancements

The codebase is structured to support:

- AI-generated article summaries
- Topic classification and keyword filtering
- Sentiment analysis
- Duplicate story detection across outlets
- Translation services
- Daily/weekly digests
- Web dashboard
- REST API
- Docker deployment

## Docker Deployment (Optional)

### Using Docker Compose

```bash
docker-compose up -d
```

### Manual Docker Build

```bash
docker build -t news-monitor-agent .
docker run -d \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  news-monitor-agent
```

## Testing

Run unit tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=. --cov-report=html
```

## Troubleshooting

### Telegram Bot Not Sending Messages

1. Verify your bot token and chat ID are correct
2. Ensure you've started a conversation with your bot
3. Check the logs for error messages
4. Test the connection using the test_connection() method

### No Articles Being Detected

1. Check that the source URLs are accessible
2. Verify RSS feed URLs if using RSS
3. Review parsing rules for web scraping
4. Check logs for scraping errors
5. Ensure sources are enabled in config.json

### Scheduler Not Running

1. Verify CHECK_INTERVAL_HOURS is set correctly
2. Check that the application has write permissions
3. Review logs for scheduler errors
4. Ensure no firewall is blocking the application

## Logging

Logs are written to `logs/news_monitor.log` and include:
- Scheduler start/stop events
- Source check results
- Article detection
- Notification status
- Errors and retry attempts

## Performance

- Concurrent source checking with configurable thread pool
- HTTP response caching
- Duplicate detection using URL hashing
- Efficient database indexing
- Supports 100+ news sources

## Security Considerations

- Never commit `.env` file to version control
- Use environment variables for sensitive data
- Rotate API keys periodically
- Implement rate limiting for production use
- Validate all user inputs

## License

This project is provided as-is for educational and personal use.

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All functions have type hints
- New features include tests
- Documentation is updated

## Support

For issues or questions:
1. Check the logs in `logs/news_monitor.log`
2. Review this README
3. Check the configuration files
4. Open an issue on the project repository
