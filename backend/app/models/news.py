from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"
    __table_args__ = (
        sa.Index("ix_news_articles_symbol_published", "symbol_id", "published_at"),
        sa.Index("ix_news_articles_market", "market"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    title: str
    content: Optional[str] = None
    url: str = Field(unique=True, index=True)
    source: Optional[str] = None
    published_at: datetime
    market: str = Field(default="US")
    language: str = Field(default="en")


class SentimentAnalysis(SQLModel, table=True):
    __tablename__ = "sentiment_analysis"
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="news_articles.id", unique=True, index=True)
    textblob_polarity: float
    textblob_subjectivity: float
    vader_compound: float
    vader_positive: float
    vader_neutral: float
    vader_negative: float
    combined_score: float
    classification: str  # positive / neutral / negative
    processed_at: datetime = Field(default_factory=datetime.utcnow)
