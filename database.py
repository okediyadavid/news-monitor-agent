"""
Database module for news monitoring agent.
Handles SQLite database operations for sources, articles, notifications, and scheduler runs.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import hashlib
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the news monitoring agent."""
    
    def __init__(self, db_path: str = "data/news_monitor.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_database(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    telegram_chat_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sources table (updated with user_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT,
                    rss_url TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, url)
                )
            """)
            
            # Articles table (updated with user_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    source_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    url_hash TEXT NOT NULL,
                    summary TEXT,
                    publication_date TIMESTAMP,
                    featured_image TEXT,
                    content_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (source_id) REFERENCES sources (id),
                    UNIQUE(user_id, url_hash)
                )
            """)
            
            # Notifications table (updated with user_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    article_id INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Scheduler runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduler_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    sources_checked INTEGER DEFAULT 0,
                    articles_found INTEGER DEFAULT 0,
                    notifications_sent INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Keywords table (for keyword filtering)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, keyword)
                )
            """)
            
            # Bookmarks table (for article bookmarking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    article_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (article_id) REFERENCES articles (id),
                    UNIQUE(user_id, article_id)
                )
            """)
            
            # Source performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    source_id INTEGER NOT NULL,
                    total_checks INTEGER DEFAULT 0,
                    successful_checks INTEGER DEFAULT 0,
                    failed_checks INTEGER DEFAULT 0,
                    total_articles_found INTEGER DEFAULT 0,
                    avg_response_time REAL,
                    last_check_time TIMESTAMP,
                    last_success_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (source_id) REFERENCES sources (id),
                    UNIQUE(user_id, source_id)
                )
            """)
            
            # User analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    articles_viewed INTEGER DEFAULT 0,
                    articles_bookmarked INTEGER DEFAULT 0,
                    searches_performed INTEGER DEFAULT 0,
                    last_active TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id)
                )
            """)
            
            # User interests table (for daily interest catalog)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_interests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    article_id INTEGER NOT NULL,
                    summary TEXT,
                    ai_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (article_id) REFERENCES articles (id),
                    UNIQUE(user_id, article_id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_name 
                ON users(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sources_user_id 
                ON sources(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_user_id 
                ON articles(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_url_hash 
                ON articles(url_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_source_id 
                ON articles(source_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_publication_date 
                ON articles(publication_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
                ON notifications(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_article_id 
                ON notifications(article_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_status 
                ON notifications(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keywords_user_id 
                ON keywords(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id 
                ON bookmarks(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_article_id 
                ON bookmarks(article_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_performance_user_id 
                ON source_performance(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_performance_source_id 
                ON source_performance(source_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_interests_user_id 
                ON user_interests(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_interests_article_id 
                ON user_interests(article_id)
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def add_source(self, name: str, url: str, source_type: str, 
                   category: Optional[str] = None, rss_url: Optional[str] = None,
                   enabled: bool = True, user_id: Optional[int] = None) -> int:
        """
        Add a new news source to the database.
        
        Args:
            name: Name of the source
            url: URL of the source
            source_type: Type of source (rss, website, api)
            category: Category of the source
            rss_url: RSS feed URL if available
            enabled: Whether the source is enabled
            user_id: User ID (for multi-user support)
            
        Returns:
            ID of the inserted source
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sources 
                (user_id, name, url, type, category, rss_url, enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, name, url, source_type, category, rss_url, enabled))
            return cursor.lastrowid
    
    def get_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a source by ID.
        
        Args:
            source_id: ID of the source
            
        Returns:
            Source dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_source_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get a source by URL.
        
        Args:
            url: URL of the source
            
        Returns:
            Source dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE url = ?", (url,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_sources(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all sources.
        
        Args:
            enabled_only: Whether to only return enabled sources
            
        Returns:
            List of source dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if enabled_only:
                cursor.execute("SELECT * FROM sources WHERE enabled = 1")
            else:
                cursor.execute("SELECT * FROM sources")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_sources(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all sources for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of source dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE user_id = ? AND enabled = 1", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_source_last_checked(self, source_id: int) -> None:
        """
        Update the last checked timestamp for a source.
        
        Args:
            source_id: ID of the source
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sources 
                SET last_checked = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (source_id,))
    
    def article_exists(self, url: str, user_id: Optional[int] = None) -> bool:
        """
        Check if an article already exists in the database.
        
        Args:
            url: URL of the article
            user_id: User ID (for multi-user support)
            
        Returns:
            True if article exists, False otherwise
        """
        url_hash = self._generate_url_hash(url)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT 1 FROM articles WHERE url_hash = ? AND user_id = ?", (url_hash, user_id))
            else:
                cursor.execute("SELECT 1 FROM articles WHERE url_hash = ?", (url_hash,))
            return cursor.fetchone() is not None
    
    def add_article(self, source_id: int, title: str, url: str, 
                   summary: Optional[str] = None, publication_date: Optional[datetime] = None,
                   featured_image: Optional[str] = None, content: Optional[str] = None,
                   user_id: Optional[int] = None, content_hash: Optional[str] = None) -> Optional[int]:
        """
        Add a new article to the database.
        
        Args:
            source_id: ID of the source
            title: Title of the article
            url: URL of the article
            summary: Summary of the article
            publication_date: Publication date of the article
            featured_image: URL of the featured image
            content: Full content for hash generation
            user_id: User ID (for multi-user support)
            content_hash: Pre-computed content hash
            
        Returns:
            ID of the inserted article or None if already exists
        """
        if self.article_exists(url, user_id):
            logger.debug(f"Article already exists: {url}")
            return None
        
        url_hash = self._generate_url_hash(url)
        if not content_hash:
            content_hash = self._generate_content_hash(content or title + summary)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles 
                (user_id, source_id, title, url, url_hash, summary, publication_date, featured_image, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, source_id, title, url, url_hash, summary, publication_date, featured_image, content_hash))
            return cursor.lastrowid
    
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an article by ID.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Article dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_articles_by_source(self, source_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get articles by source ID.
        
        Args:
            source_id: ID of the source
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM articles 
                WHERE source_id = ? 
                ORDER BY publication_date DESC 
                LIMIT ?
            """, (source_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_articles(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent articles from the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, s.name as source_name 
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                WHERE a.created_at >= datetime('now', '-' || ? || ' hours')
                ORDER BY a.created_at DESC
                LIMIT ?
            """, (hours, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_notification(self, article_id: int, channel: str) -> int:
        """
        Add a notification record.
        
        Args:
            article_id: ID of the article
            channel: Notification channel (telegram, email, etc.)
            
        Returns:
            ID of the inserted notification
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notifications (article_id, channel)
                VALUES (?, ?)
            """, (article_id, channel))
            return cursor.lastrowid
    
    def update_notification_status(self, notification_id: int, status: str, 
                                  error_message: Optional[str] = None) -> None:
        """
        Update notification status.
        
        Args:
            notification_id: ID of the notification
            status: Status of the notification (pending, sent, failed)
            error_message: Error message if failed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status == 'sent':
                cursor.execute("""
                    UPDATE notifications 
                    SET status = ?, sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, notification_id))
            else:
                cursor.execute("""
                    UPDATE notifications 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, (status, error_message, notification_id))
    
    def start_scheduler_run(self) -> int:
        """
        Start a new scheduler run record.
        
        Returns:
            ID of the scheduler run
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scheduler_runs (start_time, status)
                VALUES (CURRENT_TIMESTAMP, 'running')
            """)
            return cursor.lastrowid
    
    def end_scheduler_run(self, run_id: int, sources_checked: int = 0, 
                         articles_found: int = 0, notifications_sent: int = 0,
                         errors: int = 0, status: str = 'completed') -> None:
        """
        End a scheduler run record.
        
        Args:
            run_id: ID of the scheduler run
            sources_checked: Number of sources checked
            articles_found: Number of articles found
            notifications_sent: Number of notifications sent
            errors: Number of errors
            status: Status of the run
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scheduler_runs 
                SET end_time = CURRENT_TIMESTAMP, 
                    sources_checked = ?,
                    articles_found = ?,
                    notifications_sent = ?,
                    errors = ?,
                    status = ?
                WHERE id = ?
            """, (sources_checked, articles_found, notifications_sent, errors, status, run_id))
    
    def get_scheduler_runs(self, limit: int = 10) -> list:
        """
        Get recent scheduler runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of scheduler run dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scheduler_runs 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Keyword methods
    def add_keyword(self, user_id: int, keyword: str) -> int:
        """Add a keyword for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO keywords (user_id, keyword)
                VALUES (?, ?)
            """, (user_id, keyword.lower()))
            return cursor.lastrowid
    
    def remove_keyword(self, user_id: int, keyword: str) -> bool:
        """Remove a keyword for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM keywords WHERE user_id = ? AND keyword = ?
            """, (user_id, keyword.lower()))
            return cursor.rowcount > 0
    
    def get_user_keywords(self, user_id: int) -> list:
        """Get all keywords for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT keyword FROM keywords WHERE user_id = ?", (user_id,))
            return [row[0] for row in cursor.fetchall()]
    
    # Bookmark methods
    def add_bookmark(self, user_id: int, article_id: int) -> int:
        """Add a bookmark for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO bookmarks (user_id, article_id)
                VALUES (?, ?)
            """, (user_id, article_id))
            return cursor.lastrowid
    
    def remove_bookmark(self, user_id: int, article_id: int) -> bool:
        """Remove a bookmark for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM bookmarks WHERE user_id = ? AND article_id = ?
            """, (user_id, article_id))
            return cursor.rowcount > 0
    
    def get_user_bookmarks(self, user_id: int) -> list:
        """Get all bookmarks for a user with article details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, b.created_at as bookmarked_at 
                FROM bookmarks b 
                JOIN articles a ON b.article_id = a.id 
                WHERE b.user_id = ?
                ORDER BY b.created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Source performance methods
    def update_source_performance(self, user_id: int, source_id: int, 
                                  success: bool, articles_found: int = 0, 
                                  response_time: Optional[float] = None) -> None:
        """Update source performance metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO source_performance 
                (user_id, source_id, total_checks, successful_checks, failed_checks, 
                 total_articles_found, avg_response_time, last_check_time, last_success_time)
                VALUES (?, ?, 1, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(user_id, source_id) DO UPDATE SET
                    total_checks = total_checks + 1,
                    successful_checks = successful_checks + ?,
                    failed_checks = failed_checks + ?,
                    total_articles_found = total_articles_found + ?,
                    avg_response_time = (avg_response_time * (total_checks - 1) + ?) / total_checks,
                    last_check_time = CURRENT_TIMESTAMP,
                    last_success_time = CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE last_success_time END,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, source_id, 1 if success else 0, 0 if success else 1, articles_found,
                  response_time, response_time, 1 if success else 0, 0 if success else 1,
                  articles_found, response_time, success))
    
    def get_source_performance(self, user_id: int, source_id: int) -> Optional[dict]:
        """Get performance metrics for a specific source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM source_performance 
                WHERE user_id = ? AND source_id = ?
            """, (user_id, source_id))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_source_performance(self, user_id: int) -> list:
        """Get performance metrics for all user sources."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sp.*, s.name as source_name 
                FROM source_performance sp 
                JOIN sources s ON sp.source_id = s.id 
                WHERE sp.user_id = ?
                ORDER BY sp.successful_checks DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # User interests methods
    def add_interest(self, user_id: int, article_id: int, summary: str = None, ai_summary: str = None) -> bool:
        """Add an article to user's interests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO user_interests (user_id, article_id, summary, ai_summary)
                    VALUES (?, ?, ?, ?)
                """, (user_id, article_id, summary, ai_summary))
                return True
            except sqlite3.IntegrityError:
                # Already exists
                return False
    
    def remove_interest(self, user_id: int, article_id: int) -> bool:
        """Remove an article from user's interests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_interests 
                WHERE user_id = ? AND article_id = ?
            """, (user_id, article_id))
            return cursor.rowcount > 0
    
    def get_user_interests(self, user_id: int, date: str = None) -> list:
        """Get user's interests, optionally filtered by date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute("""
                    SELECT ui.*, a.title, a.url, a.summary as article_summary, s.name as source_name
                    FROM user_interests ui
                    JOIN articles a ON ui.article_id = a.id
                    JOIN sources s ON a.source_id = s.id
                    WHERE ui.user_id = ? AND DATE(ui.created_at) = ?
                    ORDER BY ui.created_at DESC
                """, (user_id, date))
            else:
                cursor.execute("""
                    SELECT ui.*, a.title, a.url, a.summary as article_summary, s.name as source_name
                    FROM user_interests ui
                    JOIN articles a ON ui.article_id = a.id
                    JOIN sources s ON a.source_id = s.id
                    WHERE ui.user_id = ?
                    ORDER BY ui.created_at DESC
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_interest_by_article(self, user_id: int, article_id: int) -> Optional[dict]:
        """Check if an article is in user's interests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_interests 
                WHERE user_id = ? AND article_id = ?
            """, (user_id, article_id))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # User analytics methods
    def update_user_analytics(self, user_id: int, articles_viewed: int = 0,
                             articles_bookmarked: int = 0, searches_performed: int = 0) -> None:
        """Update user analytics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_analytics 
                (user_id, articles_viewed, articles_bookmarked, searches_performed, last_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    articles_viewed = articles_viewed + ?,
                    articles_bookmarked = articles_bookmarked + ?,
                    searches_performed = searches_performed + ?,
                    last_active = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, articles_viewed, articles_bookmarked, searches_performed,
                  articles_viewed, articles_bookmarked, searches_performed))
    
    def get_user_analytics(self, user_id: int) -> Optional[dict]:
        """Get analytics for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_analytics WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate a hash for a URL."""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute("SELECT COUNT(*) FROM sources WHERE enabled = 1")
            stats['enabled_sources'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles")
            stats['total_articles'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE status = 'sent'")
            stats['sent_notifications'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM scheduler_runs")
            stats['total_runs'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MAX(created_at) FROM articles
            """)
            result = cursor.fetchone()[0]
            stats['last_article_added'] = result
            
            return stats
