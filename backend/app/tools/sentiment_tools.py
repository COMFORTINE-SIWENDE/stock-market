import re
import time
from datetime import date
from typing import Optional
from sqlmodel import Session, select

from app.models.news import NewsArticle, SentimentAnalysis
from app.models.sentiment import DailySentiment
from app.models.stock import StockSymbol
from app.utils.logger import logger


def preprocess_text(text: str) -> str:
    """Strip HTML, remove special chars, collapse whitespace, lowercase."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove special characters (keep letters, digits, spaces, basic punctuation)
    text = re.sub(r"[^\w\s.,!?'-]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def analyze_article_sentiment(article_id: int, session: Session) -> dict:
    """Run TextBlob + VADER on an article, store result, return dict."""
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    start_time = time.time()
    article = session.get(NewsArticle, article_id)
    if not article:
        return {"error": f"Article {article_id} not found"}

    text = preprocess_text((article.title or "") + " " + (article.content or ""))

    # TextBlob
    blob = TextBlob(text)
    tb_polarity = float(blob.sentiment.polarity)
    tb_subjectivity = float(blob.sentiment.subjectivity)

    # VADER
    analyzer = SentimentIntensityAnalyzer()
    vader_scores = analyzer.polarity_scores(text)
    vader_compound = float(vader_scores["compound"])
    vader_pos = float(vader_scores["pos"])
    vader_neu = float(vader_scores["neu"])
    vader_neg = float(vader_scores["neg"])

    # Combined score (equal weights)
    combined = (tb_polarity * 0.5) + (vader_compound * 0.5)

    # Classification
    if combined > 0.05:
        classification = "positive"
    elif combined < -0.05:
        classification = "negative"
    else:
        classification = "neutral"

    # Upsert SentimentAnalysis
    existing = session.exec(
        select(SentimentAnalysis).where(SentimentAnalysis.article_id == article_id)
    ).first()
    if existing:
        existing.textblob_polarity = tb_polarity
        existing.textblob_subjectivity = tb_subjectivity
        existing.vader_compound = vader_compound
        existing.vader_positive = vader_pos
        existing.vader_neutral = vader_neu
        existing.vader_negative = vader_neg
        existing.combined_score = combined
        existing.classification = classification
        session.add(existing)
    else:
        sentiment = SentimentAnalysis(
            article_id=article_id,
            textblob_polarity=tb_polarity,
            textblob_subjectivity=tb_subjectivity,
            vader_compound=vader_compound,
            vader_positive=vader_pos,
            vader_neutral=vader_neu,
            vader_negative=vader_neg,
            combined_score=combined,
            classification=classification,
        )
        session.add(sentiment)
    session.commit()

    duration = time.time() - start_time
    logger.info(
        f"Sentiment article_id={article_id} score={combined:.3f} "
        f"classification={classification} duration={duration:.2f}s"
    )

    return {
        "article_id": article_id,
        "textblob_polarity": tb_polarity,
        "textblob_subjectivity": tb_subjectivity,
        "vader_compound": vader_compound,
        "combined_score": combined,
        "classification": classification,
    }


def get_daily_sentiment(symbol: str, date_range: tuple, session: Session) -> list[dict]:
    """Query DailySentiment for a symbol over a date range."""
    start_date, end_date = date_range
    stock_symbol = session.exec(
        select(StockSymbol).where(StockSymbol.symbol == symbol)
    ).first()
    if not stock_symbol:
        return []
    records = session.exec(
        select(DailySentiment).where(
            DailySentiment.symbol_id == stock_symbol.id,
            DailySentiment.date >= start_date,
            DailySentiment.date <= end_date,
        )
    ).all()
    return [
        {
            "date": str(r.date),
            "avg_sentiment_score": r.avg_sentiment_score,
            "article_count": r.article_count,
            "positive_count": r.positive_count,
            "neutral_count": r.neutral_count,
            "negative_count": r.negative_count,
        }
        for r in records
    ]


def compare_sentiment(symbols: list[str], date_range: tuple, session: Session) -> dict:
    """Compare sentiment across multiple symbols."""
    return {symbol: get_daily_sentiment(symbol, date_range, session) for symbol in symbols}
