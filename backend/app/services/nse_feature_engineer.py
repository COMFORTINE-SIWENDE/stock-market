"""NSE feature engineering for ML predictions."""
import logging
import pandas as pd
from sqlmodel import Session, select
from app.models.stock import StockData
from app.models.news import SentimentAnalysis, NewsArticle


logger = logging.getLogger(__name__)


class NSEFeatureEngineer:
    """Feature engineering for NSE stock predictions."""
    
    @staticmethod
    def engineer_features(symbol: str, symbol_id: int, session: Session) -> pd.DataFrame:
        """
        Engineer features for ML model training/prediction.
        
        Features include:
        - OHLCV data
        - SMA-5, SMA-20
        - 20-day rolling volatility
        - Daily sentiment scores
        - Day of week, month features
        
        Args:
            symbol: Stock symbol (e.g., "SCOM.NR")
            symbol_id: Stock symbol ID from database
            session: Database session
        
        Returns:
            DataFrame with engineered features
        """
        logger.info(f"Engineering features for {symbol}")
        
        # Fetch stock data
        stock_data = session.exec(
            select(StockData)
            .where(StockData.symbol_id == symbol_id)
            .order_by(StockData.date)
        ).all()
        
        if not stock_data:
            logger.warning(f"No stock data found for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'date': record.date,
                'open': record.open,
                'high': record.high,
                'low': record.low,
                'close': record.close,
                'volume': record.volume,
            }
            for record in stock_data
        ])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Calculate technical indicators
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['volatility_20'] = df['close'].rolling(window=20).std()
        
        # Add sentiment scores (join with news sentiment)
        sentiment_data = session.exec(
            select(NewsArticle, SentimentAnalysis)
            .join(SentimentAnalysis, NewsArticle.id == SentimentAnalysis.article_id)
            .where(NewsArticle.symbol_id == symbol_id)
        ).all()
        
        # Group sentiment by date
        sentiment_by_date = {}
        for article, sentiment in sentiment_data:
            date_key = article.published_at.date()
            if date_key not in sentiment_by_date:
                sentiment_by_date[date_key] = []
            sentiment_by_date[date_key].append(sentiment.combined_score)
        
        # Average sentiment per day
        daily_sentiment = {
            date: sum(scores) / len(scores)
            for date, scores in sentiment_by_date.items()
        }
        
        # Add sentiment to DataFrame
        df['sentiment'] = df.index.map(lambda x: daily_sentiment.get(x.date(), 0.0))
        
        # Add time features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        
        # Fill NaN values
        df['sentiment'] = df['sentiment'].fillna(0.0)
        df = df.dropna()  # Drop rows with NaN in technical indicators
        
        logger.info(f"Engineered {len(df)} feature rows for {symbol}")
        return df
