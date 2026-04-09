from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class DailySentiment(SQLModel, table=True):
    __tablename__ = "daily_sentiment"
    __table_args__ = (
        sa.Index("ix_daily_sentiment_symbol_date", "symbol_id", "date"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    date: date
    avg_sentiment_score: float
    article_count: int = Field(default=0)
    positive_count: int = Field(default=0)
    neutral_count: int = Field(default=0)
    negative_count: int = Field(default=0)
