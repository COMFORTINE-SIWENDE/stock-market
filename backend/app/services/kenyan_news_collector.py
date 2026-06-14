"""Kenyan news collector for NSE stocks."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config.news_source_config import NewsSourceConfig
from app.services.news_sources.rss_parser import RSSParser


logger = logging.getLogger(__name__)


# Company name mappings for symbol filtering
COMPANY_NAMES = {
    'SCOM': ['safaricom', 'safaricom plc'],
    'KCB': ['kcb', 'kcb group', 'kenya commercial bank'],
    'EQTY': ['equity', 'equity bank', 'equity group'],
    'EABL': ['eabl', 'east african breweries', 'breweries'],
    'COOP': ['co-operative bank', 'coop bank', 'co-op bank'],
    'ABSA': ['absa', 'absa bank'],
    'SCBK': ['standard chartered', 'stanchart'],
    'BAMB': ['bamburi', 'bamburi cement'],
    'BAT': ['british american tobacco', 'bat kenya'],
    'DTBK': ['diamond trust', 'dtb', 'diamond trust bank'],
    'NCBA': ['ncba', 'ncba group'],
    'NMG': ['nation media', 'nation media group'],
    'SBIC': ['stanbic', 'stanbic holdings'],
}


class KenyanNewsCollector:
    """Collector for Kenyan financial news from configured sources."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Kenyan news collector.
        
        Args:
            config_path: Path to news sources config (defaults to standard location)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'kenyan_news_sources.yaml'
        
        try:
            self.config = NewsSourceConfig.load(config_path)
            self.rss_parser = RSSParser()
            logger.info(f"Initialized with {len(self.config.get_enabled_sources())} news sources")
        except Exception as e:
            logger.error(f"Failed to load news config: {e}")
            self.config = None
            self.rss_parser = RSSParser()
    
    def collect_news(self, symbol: str, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Collect news articles for a stock symbol from all enabled sources.
        
        Args:
            symbol: Stock symbol (e.g., "SCOM.NR")
            hours_back: How many hours back to collect news (default 24)
        
        Returns:
            List of article dictionaries filtered by symbol/company
        """
        if not self.config:
            logger.error("News config not loaded")
            return []
        
        # Get base symbol (remove .NR suffix)
        base_symbol = symbol.replace('.NR', '').upper()
        
        # Get RSS sources
        rss_sources = self.config.get_rss_sources()
        
        if not rss_sources:
            logger.warning("No RSS sources configured")
            return []
        
        all_articles = []
        
        # Collect from each RSS source
        for source in rss_sources:
            try:
                logger.info(f"Collecting from {source.name}")
                articles = self.collect_from_rss(source.url, base_symbol)
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Failed to collect from {source.name}: {e}")
                continue
        
        # Filter by time window
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        filtered_articles = [
            article for article in all_articles
            if article['published_at'] >= cutoff_time
        ]
        
        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in filtered_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        logger.info(
            f"Collected {len(unique_articles)} unique articles for {symbol} "
            f"(filtered from {len(all_articles)} total, within {hours_back}h window)"
        )
        
        return unique_articles
    
    def collect_from_rss(self, feed_url: str, symbol: str) -> List[Dict[str, Any]]:
        """
        Collect and filter articles from a specific RSS feed.
        
        Args:
            feed_url: RSS feed URL
            symbol: Base stock symbol (e.g., "SCOM")
        
        Returns:
            List of articles mentioning the symbol or company name
        """
        # Parse the feed
        articles = self.rss_parser.parse_feed(feed_url)
        
        # Filter articles by symbol/company name
        filtered_articles = []
        
        for article in articles:
            if self._matches_symbol(article, symbol):
                # Add metadata
                article['market'] = 'NSE'
                article['language'] = 'en'
                filtered_articles.append(article)
        
        logger.info(
            f"Filtered {len(filtered_articles)} articles for {symbol} "
            f"from {len(articles)} total articles"
        )
        
        return filtered_articles
    
    def _matches_symbol(self, article: Dict[str, Any], symbol: str) -> bool:
        """
        Check if article mentions the symbol or company name.
        
        Args:
            article: Article dictionary with title and content
            symbol: Base stock symbol (e.g., "SCOM")
        
        Returns:
            True if article mentions symbol/company, False otherwise
        """
        # Combine title and content for searching
        text = (article.get('title', '') + ' ' + article.get('content', '')).lower()
        
        # Check for symbol
        if symbol.lower() in text:
            return True
        
        # Check for company names
        company_names = COMPANY_NAMES.get(symbol.upper(), [])
        for name in company_names:
            if name.lower() in text:
                return True
        
        return False
