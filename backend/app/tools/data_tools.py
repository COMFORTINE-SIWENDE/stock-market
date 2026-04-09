import time
from datetime import datetime, timedelta
from typing import Optional
import requests
import yfinance as yf
from xml.etree import ElementTree

from app.utils.logger import logger
from app.config.config import settings


def fetch_historical_data(symbol: str, start_date: str, end_date: str) -> list[dict]:
    """Fetch daily OHLCV data from Yahoo Finance with retry logic."""
    if not symbol or not start_date or not end_date:
        return [{"error": "symbol, start_date, and end_date are required"}]

    for attempt in range(3):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            if df.empty:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return []
            records = []
            for date_idx, row in df.iterrows():
                records.append({
                    "date": date_idx.date().isoformat(),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": float(row.get("Volume", 0)),
                    "adj_close": float(row.get("Close", 0)),
                })
            return records
        except Exception as e:
            logger.warning(f"fetch_historical_data attempt {attempt+1} failed for {symbol}: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return []


def fetch_current_price(symbol: str) -> float:
    """Return latest closing price for a symbol."""
    if not symbol:
        return 0.0
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return 0.0
        return float(hist["Close"].iloc[-1])
    except Exception as e:
        logger.error(f"fetch_current_price failed for {symbol}: {e}")
        return 0.0


def get_technical_indicators(symbol: str, date_range: tuple, session=None) -> dict:
    """Compute SMA-5, SMA-20, and 20-day rolling volatility from DB or yfinance."""
    if not symbol:
        return {"error": "symbol is required"}
    try:
        start, end = date_range
        records = fetch_historical_data(symbol, start, end)
        if not records:
            return {"error": "no data available"}
        closes = [r["close"] for r in records]
        sma5 = sum(closes[-5:]) / min(5, len(closes)) if closes else 0.0
        sma20 = sum(closes[-20:]) / min(20, len(closes)) if closes else 0.0
        if len(closes) >= 2:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            recent = returns[-20:]
            mean_r = sum(recent) / len(recent)
            variance = sum((r - mean_r) ** 2 for r in recent) / len(recent)
            volatility = variance ** 0.5
        else:
            volatility = 0.0
        return {"sma_5": sma5, "sma_20": sma20, "volatility": volatility}
    except Exception as e:
        logger.error(f"get_technical_indicators failed for {symbol}: {e}")
        return {"error": str(e)}


def fetch_news_articles(symbol: str, hours_back: int = 24) -> list[dict]:
    """Fetch news articles from NewsAPI for a given symbol."""
    if not symbol:
        return [{"error": "symbol is required"}]
    if not settings.NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not configured, skipping NewsAPI fetch")
        return []
    try:
        from_dt = (datetime.utcnow() - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": symbol,
            "from": from_dt,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": settings.NEWS_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=10)
        if not resp.ok:
            logger.error(f"NewsAPI error {resp.status_code} for {symbol}: {resp.text}")
            return []
        data = resp.json()
        articles = []
        for art in data.get("articles", []):
            articles.append({
                "title": art.get("title", ""),
                "content": art.get("content") or art.get("description", ""),
                "url": art.get("url", ""),
                "source": art.get("source", {}).get("name", ""),
                "published_at": art.get("publishedAt", ""),
            })
        return articles
    except Exception as e:
        logger.error(f"fetch_news_articles failed for {symbol}: {e}")
        return []


def fetch_rss_articles(feed_urls: list[str], symbol: str) -> list[dict]:
    """Parse RSS feeds and return articles mentioning the symbol."""
    articles = []
    for url in feed_urls:
        try:
            resp = requests.get(url, timeout=10)
            if not resp.ok:
                logger.warning(f"RSS feed error {resp.status_code} for {url}")
                continue
            root = ElementTree.fromstring(resp.content)
            for item in root.iter("item"):
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                if symbol.lower() in (title + description).lower():
                    articles.append({
                        "title": title,
                        "content": description,
                        "url": link,
                        "source": url,
                        "published_at": pub_date,
                    })
        except Exception as e:
            logger.warning(f"fetch_rss_articles failed for {url}: {e}")
    return articles
