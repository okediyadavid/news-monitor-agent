"""
Web scraper module for news monitoring agent.
Handles scraping of news websites using BeautifulSoup and Playwright.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tenacity import retry, stop_after_attempt, wait_exponential
import re

logger = logging.getLogger(__name__)


class WebScraper:
    """Scraper for news websites without RSS feeds."""
    
    def __init__(self, timeout: int = 30, user_agent: str = None, 
                 use_playwright: bool = False):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
            use_playwright: Whether to use Playwright for JavaScript rendering
        """
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.use_playwright = use_playwright
        self.playwright_browser = None
        
        if self.use_playwright:
            self._init_playwright()
    
    def _init_playwright(self) -> None:
        """Initialize Playwright browser."""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright()
            self.playwright_browser = self.playwright.start().chromium.launch(headless=True)
            logger.info("Playwright browser initialized")
        except ImportError:
            logger.warning("Playwright not installed, falling back to requests")
            self.use_playwright = False
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            self.use_playwright = False
    
    def __del__(self):
        """Cleanup Playwright resources."""
        if self.playwright_browser:
            try:
                self.playwright_browser.close()
            except:
                pass
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        if self.use_playwright and self.playwright_browser:
            return self._fetch_with_playwright(url)
        else:
            return self._fetch_with_requests(url)
    
    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """
        Fetch page using requests library.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Fetch page using Playwright for JavaScript rendering.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        try:
            page = self.playwright_browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
            content = page.content()
            page.close()
            return content
        except Exception as e:
            logger.error(f"Playwright error fetching {url}: {e}")
            return None
    
    def scrape_articles(self, url: str, source_name: str, 
                       parsing_rules: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Scrape articles from a news website.
        
        Args:
            url: URL of the news website
            source_name: Name of the news source
            parsing_rules: Custom parsing rules for the website
            
        Returns:
            List of article dictionaries
        """
        html = self.fetch_page(url)
        if not html:
            logger.error(f"Failed to fetch page: {url}")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # Use custom parsing rules or defaults
        rules = parsing_rules or self._get_default_parsing_rules()
        
        # Find article containers
        article_containers = soup.select(rules['article_selector'])
        
        if not article_containers:
            logger.warning(f"No articles found using selector: {rules['article_selector']}")
            # Try alternative selectors
            article_containers = self._find_articles_fallback(soup)
        
        logger.info(f"Found {len(article_containers)} article containers on {url}")
        
        for container in article_containers:
            try:
                article = self._parse_article_container(container, url, source_name, rules)
                if article and article.get('url'):
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error parsing article container: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(articles)} articles from {url}")
        return articles
    
    def _get_default_parsing_rules(self) -> Dict[str, Any]:
        """Get default parsing rules."""
        return {
            'article_selector': 'article, .post, .entry, .news-item, .article-item',
            'title_selector': 'h1, h2, h3, .title, .headline, .post-title',
            'link_selector': 'a[href]',
            'date_selector': 'time, .date, .published, .post-date, .timestamp',
            'summary_selector': 'p, .excerpt, .summary, .description, .post-excerpt',
            'image_selector': 'img[src]'
        }
    
    def _find_articles_fallback(self, soup: BeautifulSoup) -> List:
        """Try alternative selectors to find articles."""
        fallback_selectors = [
            'article',
            '.post',
            '.entry',
            '.news-item',
            '[class*="article"]',
            '[class*="post"]',
            'div[class*="item"]'
        ]
        
        for selector in fallback_selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 1:
                logger.info(f"Using fallback selector: {selector}")
                return elements
        
        return []
    
    def _parse_article_container(self, container, base_url: str, source_name: str, 
                                 rules: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single article container.
        
        Args:
            container: BeautifulSoup element
            base_url: Base URL for resolving relative links
            source_name: Name of the news source
            rules: Parsing rules
            
        Returns:
            Article dictionary or None
        """
        # Extract title
        title_elem = container.select_one(rules['title_selector'])
        title = title_elem.get_text(strip=True) if title_elem else None
        
        if not title:
            return None
        
        # Extract URL
        link_elem = container.select_one(rules['link_selector'])
        url = link_elem.get('href') if link_elem else None
        
        if not url:
            return None
        
        # Resolve relative URLs
        url = urljoin(base_url, url)
        
        # Extract publication date
        date_elem = container.select_one(rules['date_selector'])
        pub_date = self._parse_date(date_elem) if date_elem else None
        
        # Extract summary
        summary_elem = container.select_one(rules['summary_selector'])
        summary = summary_elem.get_text(strip=True) if summary_elem else None
        if summary:
            summary = summary[:500]  # Limit length
        
        # Extract image
        image_elem = container.select_one(rules['image_selector'])
        image = image_elem.get('src') if image_elem else None
        if image:
            image = urljoin(base_url, image)
        
        return {
            'title': title,
            'url': url,
            'summary': summary,
            'publication_date': pub_date,
            'featured_image': image,
            'source_name': source_name
        }
    
    def _parse_date(self, date_elem) -> Optional[datetime]:
        """
        Parse date from element.
        
        Args:
            date_elem: BeautifulSoup element with date
            
        Returns:
            Datetime object or None
        """
        if not date_elem:
            return None
        
        # Try datetime attribute
        datetime_attr = date_elem.get('datetime')
        if datetime_attr:
            return self._parse_date_string(datetime_attr)
        
        # Try text content
        date_text = date_elem.get_text(strip=True)
        if date_text:
            return self._parse_date_string(date_text)
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """
        Parse date from string.
        
        Args:
            date_str: Date string
            
        Returns:
            Datetime object or None
        """
        date_formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d %b %Y %H:%M:%S",
            "%d %B %Y",
            "%B %d, %Y",
            "%b %d, %Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.debug(f"Could not parse date string: {date_str}")
        return None
    
    def check_robots_txt(self, url: str) -> bool:
        """
        Check robots.txt to see if scraping is allowed.
        
        Args:
            url: URL to check
            
        Returns:
            True if scraping is allowed, False otherwise
        """
        try:
            from urllib.robotparser import RobotFileParser
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(self.user_agent, url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
            return True  # Allow if check fails
    
    def scrape_pagination(self, url: str, source_name: str, 
                          max_pages: int = 5,
                          parsing_rules: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Scrape articles from multiple pages.
        
        Args:
            url: URL of the first page
            source_name: Name of the news source
            max_pages: Maximum number of pages to scrape
            parsing_rules: Custom parsing rules
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        
        for page in range(1, max_pages + 1):
            if page == 1:
                page_url = url
            else:
                # Try common pagination patterns
                page_url = self._build_pagination_url(url, page)
            
            logger.info(f"Scraping page {page}: {page_url}")
            
            articles = self.scrape_articles(page_url, source_name, parsing_rules)
            
            if not articles:
                logger.info(f"No articles found on page {page}, stopping pagination")
                break
            
            all_articles.extend(articles)
        
        return all_articles
    
    def _build_pagination_url(self, base_url: str, page: int) -> str:
        """
        Build pagination URL.
        
        Args:
            base_url: Base URL
            page: Page number
            
        Returns:
            Paginated URL
        """
        parsed = urlparse(base_url)
        
        # Try common pagination patterns
        pagination_patterns = [
            f"{base_url}?page={page}",
            f"{base_url}?p={page}",
            f"{base_url}/page/{page}",
            f"{base_url}/page/{page}/",
            f"{base_url}?offset={(page-1)*10}",
        ]
        
        return pagination_patterns[0]  # Default to first pattern


class ArticleExtractor:
    """Extract detailed information from individual article pages."""
    
    def __init__(self, timeout: int = 30, user_agent: str = None):
        """
        Initialize the article extractor.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.scraper = WebScraper(timeout, user_agent)
    
    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information from an article page.
        
        Args:
            url: URL of the article
            
        Returns:
            Article dictionary with full details
        """
        html = self.scraper.fetch_page(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract content
        content = self._extract_content(soup)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract publication date
        pub_date = self._extract_date(soup)
        
        # Extract featured image
        image = self._extract_image(soup, url)
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'author': author,
            'publication_date': pub_date,
            'featured_image': image
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title."""
        selectors = ['h1', '.article-title', '.post-title', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content."""
        selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            'main'
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # Remove unwanted elements
                for unwanted in elem.select('script, style, nav, footer, aside'):
                    unwanted.decompose()
                return elem.get_text(strip=True)
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        selectors = ['.author', '.byline', '[rel="author"]', '.post-author']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date."""
        selectors = ['time', '.date', '.published', '.post-date']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return self.scraper._parse_date(elem)
        return None
    
    def _extract_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract featured image."""
        selectors = ['img.featured', '.article-image img', '.post-image img', 'meta[property="og:image"]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    url = elem.get('content')
                else:
                    url = elem.get('src')
                if url:
                    return urljoin(base_url, url)
        return None
