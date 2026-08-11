"""
RSS feed parser module for news monitoring agent.
Handles parsing of RSS and Atom feeds using xml.etree.ElementTree.
"""

import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RSSParser:
    """Parser for RSS and Atom feeds."""
    
    def __init__(self, timeout: int = 30, user_agent: str = None):
        """
        Initialize the RSS parser.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_feed(self, url: str) -> Optional[str]:
        """
        Fetch RSS/Atom feed content.
        
        Args:
            url: URL of the RSS feed
            
        Returns:
            XML content string or None if failed
        """
        try:
            logger.info(f"Fetching RSS feed: {url}")
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched feed: {url}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching feed {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {e}")
            return None
    
    def parse_feed(self, feed_url: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Parse an RSS/Atom feed and extract article information.
        
        Args:
            feed_url: URL of the RSS feed
            source_name: Name of the news source
            
        Returns:
            List of article dictionaries
        """
        xml_content = self.fetch_feed(feed_url)
        if not xml_content:
            return []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Detect feed type (RSS or Atom)
            if root.tag.endswith('rss') or root.tag.endswith('RDF'):
                articles = self._parse_rss(root, source_name)
            elif root.tag.endswith('feed'):
                articles = self._parse_atom(root, source_name)
            else:
                logger.warning(f"Unknown feed format for {feed_url}")
                articles = []
            
            logger.info(f"Parsed {len(articles)} articles from {feed_url}")
            return articles
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error for {feed_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            return []
    
    def _parse_rss(self, root: ET.Element, source_name: str) -> List[Dict[str, Any]]:
        """Parse RSS 2.0 feed."""
        articles = []
        
        # Find channel element
        channel = root.find('.//channel')
        if channel is None:
            return articles
        
        # Find all items
        items = channel.findall('.//item')
        
        for item in items:
            try:
                article = self._parse_rss_item(item, source_name)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error parsing RSS item: {e}")
                continue
        
        return articles
    
    def _parse_rss_item(self, item: ET.Element, source_name: str) -> Optional[Dict[str, Any]]:
        """Parse a single RSS item."""
        # Extract title
        title_elem = item.find('title')
        title = title_elem.text if title_elem is not None else None
        if not title:
            return None
        
        # Extract URL
        link_elem = item.find('link')
        url = link_elem.text if link_elem is not None else None
        if not url:
            # Try guid
            guid_elem = item.find('guid')
            url = guid_elem.text if guid_elem is not None else None
        
        if not url:
            return None
        
        # Extract publication date
        pub_date = self._parse_rss_date(item)
        
        # Extract description/summary
        summary = self._extract_rss_summary(item)
        
        # Extract image
        image = self._extract_rss_image(item)
        
        return {
            'title': title,
            'url': url,
            'summary': summary,
            'publication_date': pub_date,
            'featured_image': image,
            'source_name': source_name
        }
    
    def _parse_rss_date(self, item: ET.Element) -> Optional[datetime]:
        """Parse date from RSS item."""
        date_elem = item.find('pubDate')
        if date_elem is not None and date_elem.text:
            return self._parse_date_string(date_elem.text)
        return None
    
    def _extract_rss_summary(self, item: ET.Element) -> Optional[str]:
        """Extract summary from RSS item."""
        summary_elem = item.find('description')
        if summary_elem is not None and summary_elem.text:
            # Remove HTML tags
            soup = BeautifulSoup(summary_elem.text, 'html.parser')
            text = soup.get_text(strip=True)
            return text[:500] if text else None
        return None
    
    def _extract_rss_image(self, item: ET.Element) -> Optional[str]:
        """Extract image from RSS item."""
        # Try enclosure
        enclosure = item.find('enclosure')
        if enclosure is not None:
            url = enclosure.get('url')
            content_type = enclosure.get('type', '')
            if url and content_type.startswith('image/'):
                return url
        
        # Try media:content
        media_content = item.find('.//{http://search.yahoo.com/mrss/}content')
        if media_content is not None:
            url = media_content.get('url')
            content_type = media_content.get('type', '')
            if url and content_type.startswith('image/'):
                return url
        
        return None
    
    def _parse_atom(self, root: ET.Element, source_name: str) -> List[Dict[str, Any]]:
        """Parse Atom feed."""
        articles = []
        
        # Atom namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        # Find all entries
        entries = root.findall('.//atom:entry', ns)
        
        for entry in entries:
            try:
                article = self._parse_atom_entry(entry, source_name, ns)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error parsing Atom entry: {e}")
                continue
        
        return articles
    
    def _parse_atom_entry(self, entry: ET.Element, source_name: str, ns: dict) -> Optional[Dict[str, Any]]:
        """Parse a single Atom entry."""
        # Extract title
        title_elem = entry.find('atom:title', ns)
        title = title_elem.text if title_elem is not None else None
        if not title:
            return None
        
        # Extract URL
        link_elem = entry.find('atom:link[@rel="alternate"]', ns)
        url = link_elem.get('href') if link_elem is not None else None
        if not url:
            # Try any link
            link_elem = entry.find('atom:link', ns)
            url = link_elem.get('href') if link_elem is not None else None
        
        if not url:
            return None
        
        # Extract publication date
        pub_date = self._parse_atom_date(entry, ns)
        
        # Extract summary
        summary = self._extract_atom_summary(entry, ns)
        
        # Extract image
        image = self._extract_atom_image(entry, ns)
        
        return {
            'title': title,
            'url': url,
            'summary': summary,
            'publication_date': pub_date,
            'featured_image': image,
            'source_name': source_name
        }
    
    def _parse_atom_date(self, entry: ET.Element, ns: dict) -> Optional[datetime]:
        """Parse date from Atom entry."""
        date_elem = entry.find('atom:published', ns)
        if date_elem is None:
            date_elem = entry.find('atom:updated', ns)
        
        if date_elem is not None and date_elem.text:
            return self._parse_date_string(date_elem.text)
        return None
    
    def _extract_atom_summary(self, entry: ET.Element, ns: dict) -> Optional[str]:
        """Extract summary from Atom entry."""
        summary_elem = entry.find('atom:summary', ns)
        if summary_elem is None:
            summary_elem = entry.find('atom:content', ns)
        
        if summary_elem is not None and summary_elem.text:
            # Remove HTML tags
            soup = BeautifulSoup(summary_elem.text, 'html.parser')
            text = soup.get_text(strip=True)
            return text[:500] if text else None
        return None
    
    def _extract_atom_image(self, entry: ET.Element, ns: dict) -> Optional[str]:
        """Extract image from Atom entry."""
        # Try media:thumbnail
        thumbnail = entry.find('.//{http://search.yahoo.com/mrss/}thumbnail')
        if thumbnail is not None:
            url = thumbnail.get('url')
            if url:
                return url
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        date_formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S",
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
    
    def get_feed_info(self, feed_url: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a feed.
        
        Args:
            feed_url: URL of the RSS feed
            
        Returns:
            Dictionary with feed metadata or None
        """
        xml_content = self.fetch_feed(feed_url)
        if not xml_content:
            return None
        
        try:
            root = ET.fromstring(xml_content)
            
            if root.tag.endswith('rss'):
                channel = root.find('.//channel')
                if channel is not None:
                    title_elem = channel.find('title')
                    desc_elem = channel.find('description')
                    link_elem = channel.find('link')
                    
                    return {
                        'title': title_elem.text if title_elem is not None else None,
                        'description': desc_elem.text if desc_elem is not None else None,
                        'link': link_elem.text if link_elem is not None else None,
                        'entry_count': len(channel.findall('.//item'))
                    }
            elif root.tag.endswith('feed'):
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                title_elem = root.find('atom:title', ns)
                subtitle_elem = root.find('atom:subtitle', ns)
                
                return {
                    'title': title_elem.text if title_elem is not None else None,
                    'description': subtitle_elem.text if subtitle_elem is not None else None,
                    'link': None,
                    'entry_count': len(root.findall('.//atom:entry', ns))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting feed info: {e}")
            return None
