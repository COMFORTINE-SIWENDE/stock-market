from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class Prediction(SQLModel, table=True):
    __tablename__ = "predictions"
    __table_args__ = (
        sa.Index("ix_predictions_symbol_date", "symbol_id", "prediction_date"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    predicted_price: float
    confidence_score: float
    trend_direction: str    
    model_source: str   
    prediction_date: date
    target_date: date
    actual_price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
