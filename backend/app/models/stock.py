from datetime import date as date_type, datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class StockSymbol(SQLModel, table=True):
    __tablename__ = "stock_symbols"
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, index=True)  # Format: SCOM.NR
    company_name: Optional[str] = None
    exchange: str = Field(default="NSE")
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = Field(default=True)
    market: str = Field(default="NSE", index=True)
    currency: str = Field(default="KES")
    base_symbol: Optional[str] = None  # Symbol without .NR suffix


class StockData(SQLModel, table=True):
    __tablename__ = "stock_data"
    __table_args__ = (sa.Index("ix_stock_data_symbol_date", "symbol_id", "date"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    date: date_type
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None
    market: str = Field(default="NSE", index=True)
    currency: str = Field(default="KES")


class DataQualityMetrics(SQLModel, table=True):
    __tablename__ = "data_quality_metrics"
    __table_args__ = (sa.Index("ix_dqm_symbol_date", "symbol_id", "recorded_at"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    source: str
    error_type: str
    error_details: str
    recorded_at: datetime
    market: str


class NSEHoliday(SQLModel, table=True):
    __tablename__ = "nse_holidays"
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date_type = Field(unique=True, index=True)
    name: str
    is_recurring: bool
