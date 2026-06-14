"""RSS parser for Kenyan news feeds."""
import logging
from datetime import datetime
from typing import List, Dict, Any

try:
    import feedparser
except ImportError:
    feedparser = None


logger = logging.getLogger(__name__)


class RSSParser:
    """Parser for RSS news feeds."""
    
    def __init__(self):
        """Initialize RSS parser."""
        if feedparser is None:
            logger.warning("feedparser library not installed. RSS parsing will not work.")
    
    def parse_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """
        Parse an RSS feed and extract news articles.
        
        Args:
            feed_url: URL of the RSS feed
        
        Returns:
            List of article dictionaries with keys:
                - title: Article title
                - content: Article content/summary
                - url: Article URL
                - published_at: Publication datetime
                - source: Feed title/source name
        """
        if feedparser is None:
            logger.error("feedparser library not installed")
            return []
        
        try:
            logger.info(f"Parsing RSS feed: {feed_url}")
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            # Check for parsing errors
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            if not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                return []
            
            # Extract articles
            articles = []
            source_name = feed.feed.get('title', 'Unknown')
            
            for entry in feed.entries:
                try:
                    # Extract content (try multiple fields)
                    content = None
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # Extract publication date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6])
                    else:
                        # Default to current time if no date available
                        published_at = datetime.utcnow()
                    
                    article = {
                        'title': entry.get('title', ''),
                        'content': content or '',
                        'url': entry.get('link', ''),
                        'published_at': published_at,
                        'source': source_name
                    }
                    
                    # Only add if we have at least title and URL
                    if article['title'] and article['url']:
                        articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse entry from {feed_url}: {e}")
                    continue
            
            logger.info(f"Parsed {len(articles)} articles from {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {feed_url}: {e}")
            return []
