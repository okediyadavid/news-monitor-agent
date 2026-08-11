"""
Notification module for news monitoring agent.
Handles sending notifications via Telegram and other channels.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    @abstractmethod
    def send(self, message: str, **kwargs) -> bool:
        """
        Send a notification.
        
        Args:
            message: Message content
            **kwargs: Additional parameters
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def send_article(self, article: Dict[str, Any]) -> bool:
        """
        Send an article notification.
        
        Args:
            article: Article dictionary
            
        Returns:
            True if successful, False otherwise
        """
        pass


class TelegramNotifier(NotificationChannel):
    """Telegram bot notification channel."""
    
    def __init__(self, bot_token: str, chat_id: str, 
                 send_images: bool = True, 
                 max_summary_length: int = 500):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
            send_images: Whether to send article images
            max_summary_length: Maximum length of summary
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.send_images = send_images
        self.max_summary_length = max_summary_length
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a text message via Telegram.
        
        Args:
            message: Message content
            parse_mode: Parse mode (Markdown or HTML)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_article(self, article: Dict[str, Any]) -> bool:
        """
        Send an article notification via Telegram.
        
        Args:
            article: Article dictionary with keys: title, url, summary, 
                    publication_date, source_name, featured_image
            
        Returns:
            True if successful, False otherwise
        """
        message = self._format_article_message(article)
        
        # Send image first if available and enabled
        if self.send_images and article.get('featured_image'):
            image_sent = self._send_image(article['featured_image'], message)
            if image_sent:
                return True
        
        # Fallback to text message
        return self.send(message)
    
    def _format_article_message(self, article: Dict[str, Any]) -> str:
        """
        Format article data into a Telegram message.
        
        Args:
            article: Article dictionary
            
        Returns:
            Formatted message string
        """
        title = article.get('title', 'No title')
        url = article.get('url', '')
        source_name = article.get('source_name', 'Unknown')
        summary = article.get('summary', '')
        pub_date = article.get('publication_date')
        
        # Format publication date
        if pub_date:
            if isinstance(pub_date, datetime):
                date_str = pub_date.strftime('%Y-%m-%d %H:%M')
            else:
                date_str = str(pub_date)
        else:
            date_str = 'Unknown'
        
        message = f"*New Article*\n\n"
        message += f"📍 Source: {source_name}\n"
        message += f"📝 Title: {title}\n"
        message += f"🕐 Published: {date_str}\n"
        
        if summary:
            message += f"📄 Summary: {summary}\n\n"
        else:
            message += "\n"
        
        message += f"🔗 [Read more]({url})"
        
        return message
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _send_image(self, image_url: str, caption: str = "") -> bool:
        """
        Send an image via Telegram.
        
        Args:
            image_url: URL of the image
            caption: Image caption
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/sendPhoto"
            data = {
                'chat_id': self.chat_id,
                'photo': image_url,
                'caption': caption[:1024],  # Telegram caption limit
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info("Telegram image sent successfully")
                return True
            else:
                logger.warning(f"Failed to send image: {result.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram image: {e}")
            return False
    
    def send_batch(self, articles: List[Dict[str, Any]]) -> int:
        """
        Send multiple article notifications.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Number of successfully sent notifications
        """
        success_count = 0
        
        for article in articles:
            if self.send_article(article):
                success_count += 1
        
        logger.info(f"Sent {success_count}/{len(articles)} Telegram notifications")
        return success_count
    
    def test_connection(self) -> bool:
        """
        Test the Telegram bot connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"Connected to Telegram bot: @{bot_info.get('username')}")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False


class EmailNotifier(NotificationChannel):
    """Email notification channel (placeholder for future implementation)."""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 username: str, password: str, 
                 from_email: str, to_email: str):
        """
        Initialize email notifier.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: From email address
            to_email: To email address
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_email = to_email
    
    def send(self, message: str, **kwargs) -> bool:
        """Send email notification (placeholder)."""
        logger.warning("Email notifier not yet implemented")
        return False
    
    def send_article(self, article: Dict[str, Any]) -> bool:
        """Send article email notification (placeholder)."""
        logger.warning("Email notifier not yet implemented")
        return False


class SlackNotifier(NotificationChannel):
    """Slack notification channel (placeholder for future implementation)."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
    
    def send(self, message: str, **kwargs) -> bool:
        """Send Slack notification (placeholder)."""
        logger.warning("Slack notifier not yet implemented")
        return False
    
    def send_article(self, article: Dict[str, Any]) -> bool:
        """Send article Slack notification (placeholder)."""
        logger.warning("Slack notifier not yet implemented")
        return False


class NotificationManager:
    """Manages multiple notification channels."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.channels: Dict[str, NotificationChannel] = {}
    
    def add_channel(self, name: str, channel: NotificationChannel) -> None:
        """
        Add a notification channel.
        
        Args:
            name: Name of the channel
            channel: Notification channel instance
        """
        self.channels[name] = channel
        logger.info(f"Added notification channel: {name}")
    
    def remove_channel(self, name: str) -> None:
        """
        Remove a notification channel.
        
        Args:
            name: Name of the channel
        """
        if name in self.channels:
            del self.channels[name]
            logger.info(f"Removed notification channel: {name}")
    
    def send_to_all(self, message: str) -> Dict[str, bool]:
        """
        Send a message to all channels.
        
        Args:
            message: Message content
            
        Returns:
            Dictionary of channel names and success status
        """
        results = {}
        for name, channel in self.channels.items():
            results[name] = channel.send(message)
        return results
    
    def send_article_to_all(self, article: Dict[str, Any]) -> Dict[str, bool]:
        """
        Send an article notification to all channels.
        
        Args:
            article: Article dictionary
            
        Returns:
            Dictionary of channel names and success status
        """
        results = {}
        for name, channel in self.channels.items():
            results[name] = channel.send_article(article)
        return results
    
    def send_to_channel(self, channel_name: str, message: str) -> bool:
        """
        Send a message to a specific channel.
        
        Args:
            channel_name: Name of the channel
            message: Message content
            
        Returns:
            True if successful, False otherwise
        """
        if channel_name not in self.channels:
            logger.error(f"Channel not found: {channel_name}")
            return False
        
        return self.channels[channel_name].send(message)
    
    def send_article_to_channel(self, channel_name: str, article: Dict[str, Any]) -> bool:
        """
        Send an article notification to a specific channel.
        
        Args:
            channel_name: Name of the channel
            article: Article dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if channel_name not in self.channels:
            logger.error(f"Channel not found: {channel_name}")
            return False
        
        return self.channels[channel_name].send_article(article)
