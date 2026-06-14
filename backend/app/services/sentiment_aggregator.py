"""Daily sentiment aggregator for NSE stocks."""
import logging
from datetime import date as date_type, datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.news import NewsArticle, SentimentAnalysis
from app.services.timezone_handler import TimezoneHandler


logger = logging.getLogger(__name__)


@dataclass
class DailySentiment:
    """Daily aggregated sentiment for a stock."""
    
    symbol_id: int
    date: date_type
    average_score: float
    article_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol_id': self.symbol_id,
            'date': self.date.isoformat(),
            'average_score': self.average_score,
            'article_count': self.article_count,
            'positive_count': self.positive_count,
            'neutral_count': self.neutral_count,
            'negative_count': self.negative_count,
            'positive_pct': self.positive_pct,
            'neutral_pct': self.neutral_pct,
            'negative_pct': self.negative_pct
        }


class SentimentAggregator:
    """Aggregates sentiment scores by day for analysis."""
    
    @staticmethod
    def aggregate_daily(
        symbol: str,
        target_date: date_type,
        session: Session
    ) -> Optional[DailySentiment]:
        """
        Aggregate sentiment scores for a symbol on a specific date.
        
        Args:
            symbol: Stock symbol (e.g., "SCOM.NR")
            target_date: Date to aggregate sentiment for
            session: Database session
        
        Returns:
            DailySentiment object with aggregated metrics, or None if no data
        """
        try:
            # Convert date to EAT timezone bounds
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            # Convert to UTC for database query
            start_utc = TimezoneHandler.to_utc(
                start_datetime.replace(tzinfo=TimezoneHandler.EAT)
            )
            end_utc = TimezoneHandler.to_utc(
                end_datetime.replace(tzinfo=TimezoneHandler.EAT)
            )
            
            # Query news articles for the symbol on this date
            # Join with sentiment_analysis to get scores
            statement = (
                select(NewsArticle, SentimentAnalysis)
                .join(SentimentAnalysis, NewsArticle.id == SentimentAnalysis.article_id)
                .where(NewsArticle.published_at >= start_utc)
                .where(NewsArticle.published_at <= end_utc)
            )
            
            results = session.exec(statement).all()
            
            if not results:
                logger.info(f"No sentiment data for {symbol} on {target_date}")
                return None
            
            # Aggregate scores
            total_score = 0.0
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            
            for article, sentiment in results:
                total_score += sentiment.combined_score
                
                if sentiment.classification == 'positive':
                    positive_count += 1
                elif sentiment.classification == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
            
            article_count = len(results)
            average_score = total_score / article_count
            
            # Calculate percentages
            positive_pct = (positive_count / article_count) * 100 if article_count > 0 else 0
            neutral_pct = (neutral_count / article_count) * 100 if article_count > 0 else 0
            negative_pct = (negative_count / article_count) * 100 if article_count > 0 else 0
            
            # Get symbol_id (assume first article's symbol_id)
            symbol_id = results[0][0].symbol_id
            
            daily_sentiment = DailySentiment(
                symbol_id=symbol_id,
                date=target_date,
                average_score=average_score,
                article_count=article_count,
                positive_count=positive_count,
                neutral_count=neutral_count,
                negative_count=negative_count,
                positive_pct=positive_pct,
                neutral_pct=neutral_pct,
                negative_pct=negative_pct
            )
            
            logger.info(
                f"Aggregated sentiment for {symbol} on {target_date}: "
                f"{article_count} articles, avg score {average_score:.3f}, "
                f"{positive_pct:.1f}% positive"
            )
            
            return daily_sentiment
            
        except Exception as e:
            logger.error(f"Failed to aggregate sentiment for {symbol} on {target_date}: {e}")
            return None
