"""
Main application module for news monitoring agent.
Coordinates all components to monitor news sources and send notifications.
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import dotenv

from database import DatabaseManager
from rss import RSSParser
from scraper import WebScraper
from notifier import NotificationManager, TelegramNotifier
from scheduler import NewsScheduler, ManualScheduler

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class NewsMonitorAgent:
    """Main agent for monitoring news sources and sending notifications."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the news monitor agent.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # Initialize components
        self.db = DatabaseManager(os.getenv('DATABASE_PATH', 'data/news_monitor.db'))
        self.rss_parser = RSSParser(
            timeout=int(os.getenv('REQUEST_TIMEOUT', 30)),
            user_agent=os.getenv('USER_AGENT')
        )
        self.web_scraper = WebScraper(
            timeout=int(os.getenv('REQUEST_TIMEOUT', 30)),
            user_agent=os.getenv('USER_AGENT'),
            use_playwright=False  # Set to True for JS-heavy sites
        )
        
        # Initialize notification manager
        self.notification_manager = NotificationManager()
        self._setup_notifications()
        
        # Initialize scheduler
        check_interval = int(os.getenv('CHECK_INTERVAL_HOURS', 6))
        self.scheduler = NewsScheduler(check_interval_hours=check_interval)
        
        # Load sources into database
        self._load_sources()
        
        logger.info("News Monitor Agent initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', 'logs/news_monitor.log')
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def _setup_notifications(self) -> None:
        """Set up notification channels."""
        # Setup Telegram
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if telegram_token and telegram_chat_id:
            telegram_notifier = TelegramNotifier(
                bot_token=telegram_token,
                chat_id=telegram_chat_id,
                send_images=self.config.get('notification_settings', {}).get('send_images', True),
                max_summary_length=self.config.get('notification_settings', {}).get('max_summary_length', 500)
            )
            
            # Test connection
            if telegram_notifier.test_connection():
                self.notification_manager.add_channel('telegram', telegram_notifier)
                logger.info("Telegram notification channel added")
            else:
                logger.error("Failed to connect to Telegram bot")
        else:
            logger.warning("Telegram credentials not found in environment variables")
    
    def _load_sources(self) -> None:
        """Load news sources from configuration into database."""
        sources = self.config.get('sources', [])
        
        for source in sources:
            try:
                self.db.add_source(
                    name=source['name'],
                    url=source['url'],
                    source_type=source.get('type', 'website'),
                    category=source.get('category'),
                    rss_url=source.get('rss_url'),
                    enabled=source.get('enabled', True)
                )
                logger.info(f"Loaded source: {source['name']}")
            except Exception as e:
                logger.error(f"Error loading source {source['name']}: {e}")
    
    def check_source(self, source: Dict[str, Any]) -> int:
        """
        Check a single news source for new articles.
        
        Args:
            source: Source dictionary
            
        Returns:
            Number of new articles found
        """
        source_name = source['name']
        source_url = source['url']
        source_type = source['type']
        rss_url = source.get('rss_url')
        
        logger.info(f"Checking source: {source_name}")
        
        new_articles_count = 0
        articles = []
        
        try:
            # Try RSS first if available
            if rss_url and source_type in ['rss', 'website']:
                logger.info(f"Fetching RSS feed for {source_name}")
                articles = self.rss_parser.parse_feed(rss_url, source_name)
            
            # Fallback to web scraping if no RSS or no articles found
            if not articles:
                logger.info(f"Scraping website for {source_name}")
                parsing_rules = self.config.get('parsing_rules', {}).get('default', {})
                articles = self.web_scraper.scrape_articles(
                    source_url, 
                    source_name, 
                    parsing_rules
                )
            
            # Process articles
            for article in articles:
                article_id = self.db.add_article(
                    source_id=source['id'],
                    title=article['title'],
                    url=article['url'],
                    summary=article.get('summary'),
                    publication_date=article.get('publication_date'),
                    featured_image=article.get('featured_image')
                )
                
                if article_id:
                    new_articles_count += 1
                    logger.info(f"New article found: {article['title']}")
                    
                    # Send notification
                    self._send_notification(article_id, article)
            
            # Update last checked timestamp
            self.db.update_source_last_checked(source['id'])
            
            logger.info(f"Checked {source_name}: {new_articles_count} new articles")
            
        except Exception as e:
            logger.error(f"Error checking source {source_name}: {e}")
        
        return new_articles_count
    
    def _send_notification(self, article_id: int, article: Dict[str, Any]) -> bool:
        """
        Send notification for an article.
        
        Args:
            article_id: Database ID of the article
            article: Article dictionary
            
        Returns:
            True if notification sent successfully
        """
        try:
            # Send to all channels
            results = self.notification_manager.send_article_to_all(article)
            
            # Record notification in database
            for channel_name, success in results.items():
                notification_id = self.db.add_notification(article_id, channel_name)
                
                if success:
                    self.db.update_notification_status(notification_id, 'sent')
                else:
                    self.db.update_notification_status(
                        notification_id, 
                        'failed', 
                        'Failed to send notification'
                    )
            
            return any(results.values())
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def check_all_sources(self) -> Dict[str, Any]:
        """
        Check all enabled news sources for new articles.
        
        Returns:
            Dictionary with check results
        """
        logger.info("Starting check of all sources")
        
        # Start scheduler run record
        run_id = self.db.start_scheduler_run()
        
        # Get all enabled sources
        sources = self.db.get_all_sources(enabled_only=True)
        
        if not sources:
            logger.warning("No enabled sources found")
            self.db.end_scheduler_run(run_id, status='completed')
            return {'sources_checked': 0, 'articles_found': 0}
        
        logger.info(f"Checking {len(sources)} sources")
        
        # Check sources concurrently
        total_new_articles = 0
        errors = 0
        max_workers = int(os.getenv('MAX_WORKERS', 10))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_source = {
                executor.submit(self.check_source, source): source 
                for source in sources
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    new_articles = future.result()
                    total_new_articles += new_articles
                except Exception as e:
                    logger.error(f"Error checking source {source['name']}: {e}")
                    errors += 1
        
        # End scheduler run record
        self.db.end_scheduler_run(
            run_id,
            sources_checked=len(sources),
            articles_found=total_new_articles,
            notifications_sent=total_new_articles,  # Assuming one notification per article
            errors=errors,
            status='completed'
        )
        
        logger.info(f"Check completed: {total_new_articles} new articles found")
        
        return {
            'sources_checked': len(sources),
            'articles_found': total_new_articles,
            'errors': errors
        }
    
    def start(self) -> None:
        """Start the automated scheduler."""
        self.scheduler.set_check_function(self.check_all_sources)
        self.scheduler.start()
        logger.info("News monitor agent started")
    
    def stop(self) -> None:
        """Stop the automated scheduler."""
        self.scheduler.stop()
        logger.info("News monitor agent stopped")
    
    def run_once(self) -> Dict[str, Any]:
        """
        Run a single check without starting the scheduler.
        
        Returns:
            Dictionary with check results
        """
        return self.check_all_sources()
    
    def add_source(self, name: str, url: str, source_type: str = 'website',
                   category: str = None, rss_url: str = None) -> None:
        """
        Add a new news source.
        
        Args:
            name: Name of the source
            url: URL of the source
            source_type: Type of source (rss, website, api)
            category: Category of the source
            rss_url: RSS feed URL if available
        """
        self.db.add_source(name, url, source_type, category, rss_url)
        logger.info(f"Added new source: {name}")
        
        # Update config file
        self._update_config_file(name, url, source_type, category, rss_url)
    
    def _update_config_file(self, name: str, url: str, source_type: str,
                           category: str, rss_url: str) -> None:
        """Update the configuration file with a new source."""
        try:
            new_source = {
                'name': name,
                'url': url,
                'type': source_type,
                'category': category,
                'rss_url': rss_url,
                'enabled': True
            }
            
            self.config['sources'].append(new_source)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration file updated with new source: {name}")
        except Exception as e:
            logger.error(f"Error updating configuration file: {e}")
    
    def remove_source(self, name: str) -> None:
        """
        Remove a news source.
        
        Args:
            name: Name of the source to remove
        """
        source = self.db.get_source_by_url(name)
        if source:
            # Note: We would need to add a delete_source method to DatabaseManager
            # For now, just disable it
            logger.warning("Source removal not fully implemented, use config file")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the monitoring agent.
        
        Returns:
            Dictionary with statistics
        """
        return self.db.get_statistics()
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """
        List all configured sources.
        
        Returns:
            List of source dictionaries
        """
        return self.db.get_all_sources(enabled_only=False)


def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description='News Monitor Agent')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--list-sources', action='store_true', help='List all sources')
    parser.add_argument('--add-source', nargs=3, metavar=('NAME', 'URL', 'TYPE'), 
                       help='Add a new source: --add-source "Name" "URL" "type"')
    parser.add_argument('--category', help='Category for new source (use with --add-source)')
    parser.add_argument('--rss-url', help='RSS URL for new source (use with --add-source)')
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = NewsMonitorAgent(config_path=args.config)
    
    if args.stats:
        stats = agent.get_statistics()
        print("\n=== News Monitor Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return
    
    if args.list_sources:
        sources = agent.list_sources()
        print("\n=== Configured Sources ===")
        for source in sources:
            status = "enabled" if source['enabled'] else "disabled"
            print(f"- {source['name']} ({source['url']}) [{status}]")
        return
    
    if args.add_source:
        name, url, source_type = args.add_source
        agent.add_source(
            name=name,
            url=url,
            source_type=source_type,
            category=args.category,
            rss_url=args.rss_url
        )
        print(f"\n✓ Source '{name}' added successfully!")
        print(f"  URL: {url}")
        print(f"  Type: {source_type}")
        if args.category:
            print(f"  Category: {args.category}")
        if args.rss_url:
            print(f"  RSS URL: {args.rss_url}")
        return
    
    if args.once:
        results = agent.run_once()
        print(f"\nCheck completed: {results['articles_found']} new articles found")
        return
    
    # Start automated monitoring
    try:
        agent.start()
        
        # Keep the main thread alive
        import time
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        agent.stop()
        raise


if __name__ == '__main__':
    main()
