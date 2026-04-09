from datetime import date, datetime
from typing import Optional
from sqlmodel import Session, select

from app.models.news import NewsArticle, SentimentAnalysis
from app.models.sentiment import DailySentiment
from app.models.stock import StockSymbol
from app.tools.sentiment_tools import analyze_article_sentiment
from app.utils.logger import logger


def analyze_pending_articles(session: Session, symbol: str) -> int:
    """Analyze all NewsArticle rows for a symbol that lack a SentimentAnalysis record."""
    stock_symbol = session.exec(
        select(StockSymbol).where(StockSymbol.symbol == symbol)
    ).first()
    if not stock_symbol:
        logger.warning(f"Symbol {symbol} not found in DB")
        return 0

    # Articles without sentiment
    analyzed_ids = session.exec(select(SentimentAnalysis.article_id)).all()
    pending = session.exec(
        select(NewsArticle).where(
            NewsArticle.symbol_id == stock_symbol.id,
            ~NewsArticle.id.in_(analyzed_ids) if analyzed_ids else True,
        )
    ).all()

    count = 0
    for article in pending:
        try:
            analyze_article_sentiment(article.id, session)
            count += 1
        except Exception as e:
            logger.error(f"Failed to analyze article {article.id}: {e}")

    return count


def aggregate_daily_sentiment(session: Session, symbol: str, date_str: str) -> Optional[DailySentiment]:
    """Compute and upsert daily aggregated sentiment for a symbol on a given date."""
    target_date = date.fromisoformat(date_str) if isinstance(date_str, str) else date_str

    stock_symbol = session.exec(
        select(StockSymbol).where(StockSymbol.symbol == symbol)
    ).first()
    if not stock_symbol:
        logger.warning(f"Symbol {symbol} not found")
        return None

    # Get all sentiment records for this symbol+date
    articles = session.exec(
        select(NewsArticle).where(
            NewsArticle.symbol_id == stock_symbol.id,
            NewsArticle.published_at >= datetime.combine(target_date, datetime.min.time()),
            NewsArticle.published_at < datetime.combine(target_date, datetime.max.time()),
        )
    ).all()

    if not articles:
        return None

    article_ids = [a.id for a in articles]
    sentiments = session.exec(
        select(SentimentAnalysis).where(SentimentAnalysis.article_id.in_(article_ids))
    ).all()

    if not sentiments:
        return None

    avg_score = sum(s.combined_score for s in sentiments) / len(sentiments)
    positive_count = sum(1 for s in sentiments if s.classification == "positive")
    neutral_count = sum(1 for s in sentiments if s.classification == "neutral")
    negative_count = sum(1 for s in sentiments if s.classification == "negative")

    # Upsert DailySentiment
    existing = session.exec(
        select(DailySentiment).where(
            DailySentiment.symbol_id == stock_symbol.id,
            DailySentiment.date == target_date,
        )
    ).first()

    if existing:
        existing.avg_sentiment_score = avg_score
        existing.article_count = len(sentiments)
        existing.positive_count = positive_count
        existing.neutral_count = neutral_count
        existing.negative_count = negative_count
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        daily = DailySentiment(
            symbol_id=stock_symbol.id,
            date=target_date,
            avg_sentiment_score=avg_score,
            article_count=len(sentiments),
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
        )
        session.add(daily)
        session.commit()
        session.refresh(daily)
        return daily
