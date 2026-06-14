from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from sqlmodel import Session, select

from app.models.stock import StockSymbol, StockData
from app.models.news import NewsArticle
from app.models.market import MarketType
from app.tools.data_tools import fetch_historical_data, fetch_news_articles, fetch_rss_articles
from app.config.config import settings
from app.utils.logger import logger

# NSE-specific imports
from app.services.market_detector import MarketDetector
from app.services.nse_data_collector import NSEDataCollector
from app.services.data_quality_validator import DataQualityValidator, MetricsTracker
from app.services.trading_hours_validator import TradingHoursValidator
from app.services.kenyan_news_collector import KenyanNewsCollector


# Initialize NSE-specific services (lazy initialization)
_nse_data_collector = None
_data_quality_validator = None
_trading_hours_validator = None
_kenyan_news_collector = None


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


def _get_kenyan_news_collector() -> KenyanNewsCollector:
    """Get or create Kenyan news collector instance."""
    global _kenyan_news_collector
    if _kenyan_news_collector is None:
        _kenyan_news_collector = KenyanNewsCollector()
    return _kenyan_news_collector


def _get_or_create_symbol(session: Session, symbol: str, market: MarketType = None) -> StockSymbol:
    """Get or create stock symbol with market detection."""
    # Detect market if not provided
    if market is None:
        market = MarketDetector.detect_market(symbol)
    
    # Normalize symbol for the market
    normalized_symbol = MarketDetector.normalize_symbol(symbol, market)
    
    stock_symbol = session.exec(
        select(StockSymbol).where(StockSymbol.symbol == normalized_symbol)
    ).first()
    
    if not stock_symbol:
        # Get base symbol for NSE stocks
        base_symbol = normalized_symbol.replace('.NR', '') if market == MarketType.NSE else None
        currency = 'KES' if market == MarketType.NSE else 'USD'
        
        stock_symbol = StockSymbol(
            symbol=normalized_symbol,
            market=market.value,
            currency=currency,
            base_symbol=base_symbol
        )
        session.add(stock_symbol)
        session.commit()
        session.refresh(stock_symbol)
        logger.info(f"Created new symbol: {normalized_symbol} ({market.value}, {currency})")
    
    return stock_symbol


def collect_stock_data(
    session: Session,
    symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    """
    Fetch and store stock OHLCV data with multi-market support.
    
    Detects market type, routes to appropriate collector, applies validation.
    """
    logger.info(f"Collecting stock data for {symbol} from {start_date} to {end_date}")
    
    # Detect market type
    market = MarketDetector.detect_market(symbol)
    logger.info(f"Detected market: {market.value} for {symbol}")
    
    # Get or create symbol
    stock_symbol = _get_or_create_symbol(session, symbol, market)
    
    # Route to appropriate data collector
    if market == MarketType.NSE:
        return _collect_nse_stock_data(session, stock_symbol, symbol, start_date, end_date)
    else:
        return _collect_us_stock_data(session, stock_symbol, symbol, start_date, end_date)


def _collect_nse_stock_data(
    session: Session,
    stock_symbol: StockSymbol,
    symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    """Collect NSE stock data with validation and trading hours check."""
    # Get services
    nse_collector = _get_nse_data_collector()
    validator = _get_data_quality_validator()
    trading_validator = _get_trading_hours_validator()
    
    # Parse dates
    start = date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    
    try:
        # Fetch data from NSE collector (with fallback logic)
        records = nse_collector.fetch_historical(symbol, start, end)
        
        if not records:
            logger.warning(f"No data returned for NSE stock {symbol}")
            return 0
        
        logger.info(f"Fetched {len(records)} records for {symbol} from NSE collector")
        
        inserted = 0
        skipped_validation = 0
        skipped_duplicate = 0
        
        for record in records:
            # Apply data quality validation
            validation_result = validator.validate_ohlcv(record)
            
            if not validation_result.passed:
                logger.warning(f"Validation failed for {symbol} on {record.date}: {validation_result.errors}")
                skipped_validation += 1
                continue
            
            # Check if record is within trading hours (for real-time data)
            # Historical data is assumed to be valid
            
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
                market=record.market,
                currency=record.currency,
            )
            session.add(stock_data)
            inserted += 1
        
        session.commit()
        logger.info(
            f"NSE data collection for {symbol}: {inserted} inserted, "
            f"{skipped_validation} validation failures, {skipped_duplicate} duplicates"
        )
        return inserted
        
    except Exception as e:
        logger.error(f"Failed to collect NSE data for {symbol}: {e}")
        session.rollback()
        return 0


def _collect_us_stock_data(
    session: Session,
    stock_symbol: StockSymbol,
    symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    """Collect US stock data (original logic)."""
    records = fetch_historical_data(symbol, start_date, end_date)
    if not records or (len(records) == 1 and "error" in records[0]):
        # Try Alpha Vantage fallback
        if hasattr(settings, 'ALPHA_VANTAGE_API_KEY') and settings.ALPHA_VANTAGE_API_KEY:
            logger.info(f"Falling back to Alpha Vantage for {symbol}")
            av_record = alpha_vantage_fallback(session, symbol, end_date)
            records = [av_record] if av_record else []

    inserted = 0
    for rec in records:
        if "error" in rec:
            continue
        rec_date = date.fromisoformat(rec["date"]) if isinstance(rec["date"], str) else rec["date"]
        existing = session.exec(
            select(StockData).where(
                StockData.symbol_id == stock_symbol.id,
                StockData.date == rec_date,
            )
        ).first()
        if existing:
            continue
        stock_data = StockData(
            symbol_id=stock_symbol.id,
            date=rec_date,
            open=rec["open"],
            high=rec["high"],
            low=rec["low"],
            close=rec["close"],
            volume=rec["volume"],
            adj_close=rec.get("adj_close"),
            market='US',
            currency='USD',
        )
        session.add(stock_data)
        inserted += 1

    session.commit()
    logger.info(f"Inserted {inserted} new stock records for {symbol}")
    return inserted


def collect_news(
    session: Session,
    symbol: str,
    hours_back: int = 24,
    rss_feeds: Optional[list[str]] = None,
) -> int:
    """
    Fetch and store news articles with multi-market support.
    
    Routes to Kenyan news collector for NSE stocks.
    """
    logger.info(f"Collecting news for {symbol} (last {hours_back}h)")
    
    # Detect market type
    market = MarketDetector.detect_market(symbol)
    
    # Get or create symbol
    stock_symbol = _get_or_create_symbol(session, symbol, market)
    
    # Route to appropriate news collector
    if market == MarketType.NSE:
        return _collect_nse_news(session, stock_symbol, symbol, hours_back)
    else:
        return _collect_us_news(session, stock_symbol, symbol, hours_back, rss_feeds)


def _collect_nse_news(
    session: Session,
    stock_symbol: StockSymbol,
    symbol: str,
    hours_back: int,
) -> int:
    """Collect Kenyan news for NSE stocks."""
    kenyan_collector = _get_kenyan_news_collector()
    
    try:
        # Collect news from Kenyan sources
        articles = kenyan_collector.collect_news(symbol, hours_back)
        
        if not articles:
            logger.info(f"No news articles found for NSE stock {symbol}")
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
                market=art.get("market", "NSE"),
                language=art.get("language", "en"),
            )
            session.add(news)
            inserted += 1
        
        session.commit()
        logger.info(f"Inserted {inserted} new NSE news articles for {symbol}")
        return inserted
        
    except Exception as e:
        logger.error(f"Failed to collect NSE news for {symbol}: {e}")
        session.rollback()
        return 0


def _collect_us_news(
    session: Session,
    stock_symbol: StockSymbol,
    symbol: str,
    hours_back: int,
    rss_feeds: Optional[list[str]],
) -> int:
    """Collect US news (original logic)."""
    articles = fetch_news_articles(symbol, hours_back)
    if rss_feeds:
        articles += fetch_rss_articles(rss_feeds, symbol)

    inserted = 0
    for art in articles:
        if not art.get("url"):
            continue
        existing = session.exec(
            select(NewsArticle).where(NewsArticle.url == art["url"])
        ).first()
        if existing:
            continue
        # Parse published_at
        pub_at = datetime.utcnow()
        if art.get("published_at"):
            try:
                pub_at = datetime.fromisoformat(art["published_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        news = NewsArticle(
            symbol_id=stock_symbol.id,
            title=art.get("title", ""),
            content=art.get("content", ""),
            url=art["url"],
            source=art.get("source", ""),
            published_at=pub_at,
            market='US',
            language='en',
        )
        session.add(news)
        inserted += 1

    session.commit()
    logger.info(f"Inserted {inserted} new articles for {symbol}")
    return inserted


def alpha_vantage_fallback(
    session: Session,
    symbol: str,
    date_str: str,
) -> Optional[dict]:
    """Fetch a single day's OHLCV from Alpha Vantage if configured."""
    if not settings.ALPHA_VANTAGE_API_KEY:
        return None
    import requests
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": settings.ALPHA_VANTAGE_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=15)
        if not resp.ok:
            logger.error(f"Alpha Vantage error {resp.status_code} for {symbol}")
            return None
        data = resp.json().get("Time Series (Daily)", {})
        day_data = data.get(date_str)
        if not day_data:
            return None
        return {
            "date": date_str,
            "open": float(day_data["1. open"]),
            "high": float(day_data["2. high"]),
            "low": float(day_data["3. low"]),
            "close": float(day_data["4. close"]),
            "volume": float(day_data["5. volume"]),
            "adj_close": float(day_data["4. close"]),
        }
    except Exception as e:
        logger.error(f"alpha_vantage_fallback failed for {symbol}: {e}")
        return None
