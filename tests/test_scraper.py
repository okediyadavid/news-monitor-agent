"""
Unit tests for the scraper module.
"""

import pytest
from scraper import WebScraper


@pytest.fixture
def web_scraper():
    """Create a web scraper instance for testing."""
    return WebScraper(timeout=30, use_playwright=False)


def test_web_scraper_initialization(web_scraper):
    """Test that web scraper initializes correctly."""
    assert web_scraper.timeout == 30
    assert web_scraper.user_agent is not None
    assert web_scraper.use_playwright is False


def test_get_default_parsing_rules(web_scraper):
    """Test getting default parsing rules."""
    rules = web_scraper._get_default_parsing_rules()
    
    assert 'article_selector' in rules
    assert 'title_selector' in rules
    assert 'link_selector' in rules
    assert 'date_selector' in rules
    assert 'summary_selector' in rules
    assert 'image_selector' in rules


def test_parse_date_string(web_scraper):
    """Test parsing date strings in various formats."""
    # Test ISO format
    date = web_scraper._parse_date_string("2023-01-15T10:30:00")
    assert date is not None
    assert date.year == 2023
    
    # Test simple date
    date = web_scraper._parse_date_string("2023-01-15")
    assert date is not None
    assert date.year == 2023
    
    # Test invalid format
    date = web_scraper._parse_date_string("invalid date")
    assert date is None


def test_build_pagination_url(web_scraper):
    """Test building pagination URLs."""
    base_url = "https://example.com/news"
    
    url = web_scraper._build_pagination_url(base_url, 2)
    assert "page=2" in url


def test_parse_date_element(web_scraper):
    """Test parsing date from BeautifulSoup element."""
    from bs4 import BeautifulSoup
    
    # Test with datetime attribute
    html = '<time datetime="2023-01-15T10:30:00">January 15, 2023</time>'
    soup = BeautifulSoup(html, 'lxml')
    elem = soup.find('time')
    
    date = web_scraper._parse_date(elem)
    assert date is not None
    assert date.year == 2023
