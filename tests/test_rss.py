"""
Unit tests for the RSS parser module.
"""

import pytest
from rss import RSSParser


@pytest.fixture
def rss_parser():
    """Create an RSS parser instance."""
    return RSSParser(timeout=30)


def test_rss_parser_initialization(rss_parser):
    """Test that RSS parser initializes correctly."""
    assert rss_parser.timeout == 30
    assert rss_parser.user_agent is not None


def test_parse_date(rss_parser):
    """Test date parsing from feed entries."""
    # Test with parsed time tuple
    entry = {
        'published_parsed': (2023, 1, 15, 10, 30, 0, 0, 15, 0)
    }
    date = rss_parser._parse_date(entry)
    assert date is not None
    assert date.year == 2023
    assert date.month == 1
    assert date.day == 15


def test_extract_summary(rss_parser):
    """Test summary extraction from feed entries."""
    entry = {
        'summary': '<p>This is a <strong>test</strong> summary.</p>'
    }
    summary = rss_parser._extract_summary(entry)
    assert summary is not None
    assert '<strong>' not in summary  # HTML tags should be removed
    assert 'test' in summary.lower()


def test_extract_image(rss_parser):
    """Test image extraction from feed entries."""
    # Test with media content
    entry = {
        'media_content': [{'type': 'image/jpeg', 'url': 'https://example.com/image.jpg'}]
    }
    image = rss_parser._extract_image(entry)
    assert image == 'https://example.com/image.jpg'
    
    # Test with enclosures
    entry = {
        'enclosures': [{'type': 'image/png', 'href': 'https://example.com/image.png'}]
    }
    image = rss_parser._extract_image(entry)
    assert image == 'https://example.com/image.png'


def test_generate_url_hash():
    """Test URL hash generation."""
    from database import DatabaseManager
    db = DatabaseManager(":memory:")
    
    hash1 = db._generate_url_hash("https://example.com/article1")
    hash2 = db._generate_url_hash("https://example.com/article1")
    hash3 = db._generate_url_hash("https://example.com/article2")
    
    assert hash1 == hash2  # Same URL should produce same hash
    assert hash1 != hash3  # Different URLs should produce different hashes
