"""
NSE-Only Data Service
Handles data collection exclusively for Nairobi Securities Exchange stocks
"""
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from sqlmodel import Session, select

from app.models.stock import StockSymbol, StockData
from app.models.news import NewsArticle
from app.tools.data_tools import fetch_news_articles
from app.config.config import settings
from app.utils.logger import logger

# NSE-specific imports
from app.services.nse_data_collector import NSEDataCollector
from app.services.data_quality_validator import DataQualityValidator, MetricsTracker
from app.services.trading_hours_validator import TradingHoursValidator


# Initialize NSE services (lazy initialization)
_nse_data_collector = None
_data_quality_validator = None
_trading_hours_validator = None


def _get_nse_data_collector() -> NSEDataCollector:
    """Get or create NSE data collector instance."""
    global _nse_data_collector
    if _nse_data_collector is None:
        _nse_data_collector = NSEDataCollector(
            alpha_vantage_api_key=settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, 'ALPHA_VANTAGE_API_KEY') else None
        )
    return _nse_data_collector


def _get_data_quality_validator() -> DataQualityValidator:
    """Get or create data quality validator instance."""
    global _data_quality_validator
    if _data_quality_validator is None:
        metrics_tracker = MetricsTracker()
        _data_quality_validator = DataQualityValidator(metrics_tracker)
    return _data_quality_validator


def _get_trading_hours_validator() -> TradingHoursValidator:
    """Get or create trading hours validator instance."""
    global _trading_hours_validator
    if _trading_hours_validator is None:
        holidays_config = Path(__file__).parent.parent / 'config' / 'nse_holidays.yaml'
        _trading_hours_validator = TradingHoursValidator(holidays_config)
    return _trading_hours_validator


def _normalize_nse_symbol(symbol: str) -> str:
    """Normalize NSE symbol to standard format (SYMBOL.NR)."""
    symbol = symbol.upper().strip()
    if not symbol.endswith('.NR'):
        symbol = f"{symbol}.NR"
    return symbol


def _get_or_create_symbol(session: Session, symbol: str) -> StockSymbol:
    """Get or create NSE stock symbol."""
    # Normalize to NSE format
    normalized_symbol = _normalize_nse_symbol(symbol)
    base_symbol = normalized_symbol.replace('.NR', '')
    
    stock_symbol = session.exec(
        select(StockSymbol).where(StockSymbol.symbol == normalized_symbol)
    ).first()
    
    if not stock_symbol:
        stock_symbol = StockSymbol(
            symbol=normalized_symbol,
            exchange="NSE",
            market="NSE",
            currency="KES",
            base_symbol=base_symbol
        )
        session.add(stock_symbol)
        session.commit()
        session.refresh(stock_symbol)
        logger.info(f"Created new NSE symbol: {normalized_symbol} (base: {base_symbol})")
    
    return stock_symbol


def collect_stock_data(
    session: Session,
    symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    """
    Fetch and store NSE stock OHLCV data with validation.
    
    Args:
        session: Database session
        symbol: NSE stock symbol (e.g., 'SCOM' or 'SCOM.NR')
        start_date: Start date in ISO format
        end_date: End date in ISO format
        
    Returns:
        Number of records inserted
    """
    logger.info(f"Collecting NSE stock data for {symbol} from {start_date} to {end_date}")
    
    # Get or create symbol
    stock_symbol = _get_or_create_symbol(session, symbol)
    
    # Get services
    nse_collector = _get_nse_data_collector()
    validator = _get_data_quality_validator()
    
    # Parse dates
    start = date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    
    try:
        # Fetch data from NSE collector (Alpha Vantage + Yahoo Finance fallback)
        records = nse_collector.fetch_historical(stock_symbol.symbol, start, end)
        
        if not records:
            logger.warning(f"No data returned for NSE stock {stock_symbol.symbol}")
            return 0
        
        logger.info(f"Fetched {len(records)} records for {stock_symbol.symbol} from NSE collector")
        
        inserted = 0
        skipped_validation = 0
        skipped_duplicate = 0
        
        for record in records:
            # Apply data quality validation
            validation_result = validator.validate_ohlcv(record)
            
            if not validation_result.passed:
                logger.warning(
                    f"Validation failed for {stock_symbol.symbol} on {record.date}: "
                    f"{validation_result.errors}"
                )
                skipped_validation += 1
                continue
            
            # Check for duplicates
            existing = session.exec(
                select(StockData).where(
                    StockData.symbol_id == stock_symbol.id,
                    StockData.date == record.date,
                )
            ).first()
            
            if existing:
                skipped_duplicate += 1
                continue
            
            # Insert record
            stock_data = StockData(
                symbol_id=stock_symbol.id,
                date=record.date,
                open=record.open,
                high=record.high,
                low=record.low,
                close=record.close,
                volume=record.volume,
                adj_close=record.close,  # NSE doesn't have adjusted close
                market="NSE",
                currency="KES",
            )
            session.add(stock_data)
            inserted += 1
        
        session.commit()
        logger.info(
            f"NSE data collection for {stock_symbol.symbol}: {inserted} inserted, "
            f"{skipped_validation} validation failures, {skipped_duplicate} duplicates"
        )
        return inserted
        
    except Exception as e:
        logger.error(f"Failed to collect NSE data for {symbol}: {e}")
        session.rollback()
        return 0


def collect_news(
    session: Session,
    symbol: str,
    hours_back: int = 24,
) -> int:
    """
    Fetch and store news articles for NSE stocks using EventRegistry.
    
    Args:
        session: Database session
        symbol: NSE stock symbol
        hours_back: Hours to look back for news
        
    Returns:
        Number of articles inserted
    """
    logger.info(f"Collecting news for NSE stock {symbol} (last {hours_back}h)")
    
    # Get or create symbol
    stock_symbol = _get_or_create_symbol(session, symbol)
    
    # Map NSE symbols to company keywords for better news matching
    company_keywords = {
        "SCOM.NR": "Safaricom",
        "KCB.NR": "KCB Kenya",
        "EQTY.NR": "Equity Bank Kenya",
        "EABL.NR": "EABL Kenya Breweries",
        "COOP.NR": "Co-operative Bank Kenya",
        "ABSA.NR": "Absa Kenya",
        "SCBK.NR": "Standard Chartered Kenya",
        "BAMB.NR": "Bamburi Cement",
        "BAT.NR": "British American Tobacco Kenya",
        "DTBK.NR": "Diamond Trust Bank Kenya",
        "NCBA.NR": "NCBA Kenya",
        "NMG.NR": "Nation Media Kenya",
        "SBIC.NR": "Stanbic Kenya",
    }
    
    # Get company-specific keyword or use base symbol
    search_term = company_keywords.get(stock_symbol.symbol, stock_symbol.base_symbol or symbol)
    
    try:
        # Collect news from EventRegistry
        articles = fetch_news_articles(search_term, hours_back)
        
        if not articles:
            logger.info(f"No news articles found for NSE stock {stock_symbol.symbol} (searched: {search_term})")
            return 0
        
        inserted = 0
        for art in articles:
            if not art.get("url"):
                continue
            
            # Check for duplicates
            existing = session.exec(
                select(NewsArticle).where(NewsArticle.url == art["url"])
            ).first()
            if existing:
                continue
            
            # Create news article
            news = NewsArticle(
                symbol_id=stock_symbol.id,
                title=art.get("title", ""),
                content=art.get("content", ""),
                url=art["url"],
                source=art.get("source", ""),
                published_at=art.get("published_at", datetime.utcnow()),
                market="NSE",
                language=art.get("language", "en"),
            )
            session.add(news)
            inserted += 1
        
        session.commit()
        logger.info(f"Inserted {inserted} new NSE news articles for {stock_symbol.symbol}")
        return inserted
        
    except Exception as e:
        logger.error(f"Failed to collect NSE news for {symbol}: {e}")
        session.rollback()
        return 0
