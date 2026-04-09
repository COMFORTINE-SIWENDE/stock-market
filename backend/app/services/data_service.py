from datetime import date, datetime, timedelta
from typing import Optional
from sqlmodel import Session, select

from app.models.stock import StockSymbol, StockData
from app.models.news import NewsArticle
from app.tools.data_tools import fetch_historical_data, fetch_news_articles, fetch_rss_articles
from app.config.config import settings
from app.utils.logger import logger


def _get_or_create_symbol(session: Session, symbol: str) -> StockSymbol:
    stock_symbol = session.exec(
        select(StockSymbol).where(StockSymbol.symbol == symbol)
    ).first()
    if not stock_symbol:
        stock_symbol = StockSymbol(symbol=symbol)
        session.add(stock_symbol)
        session.commit()
        session.refresh(stock_symbol)
    return stock_symbol


def collect_stock_data(
    session: Session,
    symbol: str,
    start_date: str,
    end_date: str,
) -> int:
    """Fetch and store stock OHLCV data, deduplicating by (symbol_id, date)."""
    logger.info(f"Collecting stock data for {symbol} from {start_date} to {end_date}")
    stock_symbol = _get_or_create_symbol(session, symbol)

    records = fetch_historical_data(symbol, start_date, end_date)
    if not records or (len(records) == 1 and "error" in records[0]):
        # Try Alpha Vantage fallback
        if settings.ALPHA_VANTAGE_API_KEY:
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
    """Fetch and store news articles, deduplicating by URL."""
    logger.info(f"Collecting news for {symbol} (last {hours_back}h)")
    stock_symbol = _get_or_create_symbol(session, symbol)

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
