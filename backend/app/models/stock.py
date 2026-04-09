from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class StockSymbol(SQLModel, table=True):
    __tablename__ = "stock_symbols"
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, index=True)
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = Field(default=True)


class StockData(SQLModel, table=True):
    __tablename__ = "stock_data"
    __table_args__ = (sa.Index("ix_stock_data_symbol_date", "symbol_id", "date"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id")
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None
