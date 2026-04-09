# Import all models so Alembic autogenerate can discover them
from app.models.user import User, UserSession
from app.models.stock import StockSymbol, StockData
from app.models.news import NewsArticle, SentimentAnalysis
from app.models.sentiment import DailySentiment
from app.models.prediction import Prediction

__all__ = [
    "User", "UserSession",
    "StockSymbol", "StockData",
    "NewsArticle", "SentimentAnalysis",
    "DailySentiment",
    "Prediction",
]
