"""
Unit tests for the database module.
"""

import pytest
import os
import tempfile
from datetime import datetime
from database import DatabaseManager


@pytest.fixture
def db_manager():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    db = DatabaseManager(db_path)
    yield db
    
    # Cleanup
    os.unlink(db_path)


def test_database_initialization(db_manager):
    """Test that database initializes correctly."""
    assert db_manager.db_path is not None
    assert os.path.exists(db_manager.db_path)


def test_add_source(db_manager):
    """Test adding a news source."""
    source_id = db_manager.add_source(
        name="Test Source",
        url="https://example.com",
        source_type="website",
        category="Test",
        rss_url="https://example.com/feed"
    )
    
    assert source_id > 0
    
    source = db_manager.get_source(source_id)
    assert source['name'] == "Test Source"
    assert source['url'] == "https://example.com"
    assert source['type'] == "website"


def test_get_source_by_url(db_manager):
    """Test retrieving a source by URL."""
    db_manager.add_source(
        name="Test Source",
        url="https://example.com",
        source_type="website"
    )
    
    source = db_manager.get_source_by_url("https://example.com")
    assert source is not None
    assert source['name'] == "Test Source"


def test_get_all_sources(db_manager):
    """Test retrieving all sources."""
    db_manager.add_source("Source 1", "https://example1.com", "website")
    db_manager.add_source("Source 2", "https://example2.com", "website")
    db_manager.add_source("Source 3", "https://example3.com", "website", enabled=False)
    
    all_sources = db_manager.get_all_sources(enabled_only=False)
    assert len(all_sources) == 3
    
    enabled_sources = db_manager.get_all_sources(enabled_only=True)
    assert len(enabled_sources) == 2


def test_add_article(db_manager):
    """Test adding an article."""
    source_id = db_manager.add_source("Test Source", "https://example.com", "website")
    
    article_id = db_manager.add_article(
        source_id=source_id,
        title="Test Article",
        url="https://example.com/article1",
        summary="Test summary",
        publication_date=datetime.now(),
        featured_image="https://example.com/image.jpg"
    )
    
    assert article_id is not None
    
    # Test duplicate detection
    duplicate_id = db_manager.add_article(
        source_id=source_id,
        title="Test Article",
        url="https://example.com/article1",
        summary="Test summary"
    )
    
    assert duplicate_id is None


def test_article_exists(db_manager):
    """Test checking if an article exists."""
    source_id = db_manager.add_source("Test Source", "https://example.com", "website")
    
    assert not db_manager.article_exists("https://example.com/article1")
    
    db_manager.add_article(
        source_id=source_id,
        title="Test Article",
        url="https://example.com/article1"
    )
    
    assert db_manager.article_exists("https://example.com/article1")


def test_get_articles_by_source(db_manager):
    """Test retrieving articles by source."""
    source_id = db_manager.add_source("Test Source", "https://example.com", "website")
    
    db_manager.add_article(source_id, "Article 1", "https://example.com/1")
    db_manager.add_article(source_id, "Article 2", "https://example.com/2")
    db_manager.add_article(source_id, "Article 3", "https://example.com/3")
    
    articles = db_manager.get_articles_by_source(source_id)
    assert len(articles) == 3


def test_add_notification(db_manager):
    """Test adding a notification record."""
    source_id = db_manager.add_source("Test Source", "https://example.com", "website")
    article_id = db_manager.add_article(source_id, "Test Article", "https://example.com/article1")
    
    notification_id = db_manager.add_notification(article_id, "telegram")
    assert notification_id is not None
    
    db_manager.update_notification_status(notification_id, "sent")
    
    # Note: We would need to add a get_notification method to fully test this


def test_scheduler_runs(db_manager):
    """Test scheduler run tracking."""
    run_id = db_manager.start_scheduler_run()
    assert run_id is not None
    
    db_manager.end_scheduler_run(
        run_id,
        sources_checked=5,
        articles_found=10,
        notifications_sent=10,
        errors=0,
        status="completed"
    )
    
    runs = db_manager.get_scheduler_runs()
    assert len(runs) == 1
    assert runs[0]['sources_checked'] == 5
    assert runs[0]['articles_found'] == 10


def test_get_statistics(db_manager):
    """Test getting database statistics."""
    source_id = db_manager.add_source("Test Source", "https://example.com", "website")
    db_manager.add_article(source_id, "Test Article", "https://example.com/article1")
    
    stats = db_manager.get_statistics()
    assert stats['enabled_sources'] >= 1
    assert stats['total_articles'] >= 1
