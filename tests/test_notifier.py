"""
Unit tests for the notifier module.
"""

import pytest
from unittest.mock import Mock, patch
from notifier import TelegramNotifier, NotificationManager


@pytest.fixture
def telegram_notifier():
    """Create a Telegram notifier instance for testing."""
    return TelegramNotifier(
        bot_token="test_token",
        chat_id="test_chat_id",
        send_images=False
    )


def test_telegram_notifier_initialization(telegram_notifier):
    """Test that Telegram notifier initializes correctly."""
    assert telegram_notifier.bot_token == "test_token"
    assert telegram_notifier.chat_id == "test_chat_id"
    assert telegram_notifier.send_images is False


def test_format_article_message(telegram_notifier):
    """Test article message formatting."""
    article = {
        'title': 'Test Article',
        'url': 'https://example.com/article',
        'source_name': 'Test Source',
        'summary': 'This is a test summary',
        'publication_date': '2023-01-15 10:30:00'
    }
    
    message = telegram_notifier._format_article_message(article)
    
    assert 'Test Article' in message
    assert 'Test Source' in message
    assert 'https://example.com/article' in message
    assert '📰' in message  # Emoji should be present


def test_format_article_message_long_summary(telegram_notifier):
    """Test that long summaries are truncated."""
    long_summary = "This is a very long summary. " * 50
    article = {
        'title': 'Test Article',
        'url': 'https://example.com/article',
        'source_name': 'Test Source',
        'summary': long_summary,
        'publication_date': '2023-01-15 10:30:00'
    }
    
    message = telegram_notifier._format_article_message(article)
    
    # Summary should be truncated
    assert len(message) < len(long_summary) + 200


def test_notification_manager():
    """Test notification manager functionality."""
    manager = NotificationManager()
    
    # Create a mock notifier
    mock_notifier = Mock()
    mock_notifier.send.return_value = True
    mock_notifier.send_article.return_value = True
    
    # Add channel
    manager.add_channel('test', mock_notifier)
    assert 'test' in manager.channels
    
    # Send to channel
    result = manager.send_to_channel('test', 'Test message')
    assert result is True
    mock_notifier.send.assert_called_once_with('Test message')
    
    # Send article to channel
    article = {'title': 'Test', 'url': 'https://example.com'}
    result = manager.send_article_to_channel('test', article)
    assert result is True
    mock_notifier.send_article.assert_called_once_with(article)
    
    # Remove channel
    manager.remove_channel('test')
    assert 'test' not in manager.channels


def test_notification_manager_send_to_all():
    """Test sending to all channels."""
    manager = NotificationManager()
    
    mock_notifier1 = Mock()
    mock_notifier1.send.return_value = True
    
    mock_notifier2 = Mock()
    mock_notifier2.send.return_value = False
    
    manager.add_channel('channel1', mock_notifier1)
    manager.add_channel('channel2', mock_notifier2)
    
    results = manager.send_to_all('Test message')
    
    assert results['channel1'] is True
    assert results['channel2'] is False


def test_send_to_nonexistent_channel():
    """Test sending to a channel that doesn't exist."""
    manager = NotificationManager()
    
    result = manager.send_to_channel('nonexistent', 'Test message')
    assert result is False
