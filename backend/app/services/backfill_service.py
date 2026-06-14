"""Backfill service for historical NSE data."""
import logging
import time
from datetime import date, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass

from sqlmodel import Session
from app.services.nse_data_collector import NSEDataCollector
from app.services.data_quality_validator import DataQualityValidator, MetricsTracker
from app.models.stock import StockSymbol, StockData


logger = logging.getLogger(__name__)


@dataclass
class BackfillResult:
    """Result of backfill operation."""
    total_records: Dict[str, int]
    total_collected: int
    total_failed: int
    duration_seconds: float


class BackfillService:
    """Service for backfilling historical NSE stock data."""
    
    def __init__(self):
        """Initialize backfill service."""
        self.nse_collector = NSEDataCollector()
        self.validator = DataQualityValidator(MetricsTracker())
    
    def backfill_historical(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        session: Session
    ) -> BackfillResult:
        """
        Backfill historical data for multiple NSE symbols.
        
        Features:
        - Exponential backoff for rate limiting
        - Progress logging every 100 records
        - Resume support from last successful date
        - Data quality validation
        
        Args:
            symbols: List of NSE symbols
            start_date: Start date for backfill
            end_date: End date for backfill
            session: Database session
        
        Returns:
            BackfillResult with summary
        """
        logger.info(f"Starting backfill for {len(symbols)} symbols from {start_date} to {end_date}")
        
        start_time = time.time()
        results = {}
        total_collected = 0
        total_failed = 0
        
        for symbol in symbols:
            logger.info(f"Backfilling {symbol}")
            
            try:
                # Get or create symbol
                stock_symbol = self._get_or_create_symbol(session, symbol)
                
                # Check last date in database
                last_record = session.query(StockData).filter(
                    StockData.symbol_id == stock_symbol.id
                ).order_by(StockData.date.desc()).first()
                
                # Resume from last date if exists
                resume_date = last_record.date + timedelta(days=1) if last_record else start_date
                resume_date = max(resume_date, start_date)
                
                if resume_date > end_date:
                    logger.info(f"{symbol} already up to date")
                    results[symbol] = 0
                    continue
                
                # Fetch data with exponential backoff
                attempt = 0
                max_attempts = 3
                records = []
                
                while attempt < max_attempts:
                    try:
                        records = self.nse_collector.fetch_historical(symbol, resume_date, end_date)
                        break
                    except Exception as e:
                        attempt += 1
                        if attempt < max_attempts:
                            wait_time = 2 ** attempt
                            logger.warning(f"Attempt {attempt} failed for {symbol}, retrying in {wait_time}s: {e}")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"All attempts failed for {symbol}")
                            total_failed += 1
                            raise
                
                # Validate and insert
                inserted = 0
                for i, record in enumerate(records):
                    # Validate
                    validation = self.validator.validate_ohlcv(record)
                    if not validation.passed:
                        logger.warning(f"Validation failed for {symbol} on {record.date}")
                        continue
                    
                    # Check duplicate
                    existing = session.query(StockData).filter(
                        StockData.symbol_id == stock_symbol.id,
                        StockData.date == record.date
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Insert
                    stock_data = StockData(
                        symbol_id=stock_symbol.id,
                        date=record.date,
                        open=record.open,
                        high=record.high,
                        low=record.low,
                        close=record.close,
                        volume=record.volume,
                        adj_close=record.close,
                        market='NSE',
                        currency='KES'
                    )
                    session.add(stock_data)
                    inserted += 1
                    total_collected += 1
                    
                    # Progress logging
                    if (i + 1) % 100 == 0:
                        logger.info(f"{symbol}: {i + 1}/{len(records)} records processed")
                
                session.commit()
                results[symbol] = inserted
                logger.info(f"Backfilled {inserted} records for {symbol}")
                
                # Rate limiting between symbols
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Backfill failed for {symbol}: {e}")
                session.rollback()
                results[symbol] = 0
                total_failed += 1
        
        duration = time.time() - start_time
        
        logger.info(
            f"Backfill complete: {total_collected} records collected, "
            f"{total_failed} symbols failed, {duration:.1f}s"
        )
        
        return BackfillResult(
            total_records=results,
            total_collected=total_collected,
            total_failed=total_failed,
            duration_seconds=duration
        )
    
    def _get_or_create_symbol(self, session: Session, symbol: str) -> StockSymbol:
        """Get or create stock symbol."""
        # Ensure .NR suffix
        if not symbol.endswith('.NR'):
            symbol = f"{symbol}.NR"
        
        stock_symbol = session.query(StockSymbol).filter(
            StockSymbol.symbol == symbol
        ).first()
        
        if not stock_symbol:
            base_symbol = symbol.replace('.NR', '')
            stock_symbol = StockSymbol(
                symbol=symbol,
                market='NSE',
                currency='KES',
                base_symbol=base_symbol
            )
            session.add(stock_symbol)
            session.commit()
            session.refresh(stock_symbol)
        
        return stock_symbol
