"""NSE data collector with multi-source fallback logic."""
import logging
from datetime import date
from pathlib import Path
from typing import List, Optional

from app.services.data_sources.yahoo_finance_nse import YahooFinanceNSE
from app.services.data_sources.alpha_vantage_nse import AlphaVantageNSE
from app.services.data_sources.csv_importer import CSVImporter
from app.models.ohlcv import OHLCVRecord


logger = logging.getLogger(__name__)


class DataSourceError(Exception):
    """Raised when all data sources fail."""
    pass


class NSEDataCollector:
    """
    NSE data collector with fallback logic.
    
    Tries multiple data sources in order:
    1. Yahoo Finance (primary)
    2. Alpha Vantage (fallback)
    3. CSV import (manual fallback)
    """
    
    def __init__(self, csv_data_dir: Optional[Path] = None, alpha_vantage_api_key: Optional[str] = None):
        """
        Initialize NSE data collector.
        
        Args:
            csv_data_dir: Directory containing CSV data files (optional)
            alpha_vantage_api_key: Alpha Vantage API key (optional)
        """
        self.yahoo_finance = YahooFinanceNSE()
        self.alpha_vantage = AlphaVantageNSE(api_key=alpha_vantage_api_key)
        self.csv_importer = CSVImporter()
        self.csv_data_dir = csv_data_dir
        
        logger.info("NSE Data Collector initialized with fallback sources")
    
    def fetch_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[OHLCVRecord]:
        """
        Fetch historical OHLCV data with automatic fallback.
        
        Tries sources in order until one succeeds:
        1. Yahoo Finance
        2. Alpha Vantage
        3. CSV import (if csv_data_dir configured)
        
        Args:
            symbol: NSE stock symbol (e.g., "SCOM.NR")
            start_date: Start date for data
            end_date: End date for data
        
        Returns:
            List of OHLCVRecord objects
        
        Raises:
            DataSourceError: If all sources fail
        """
        # Ensure symbol has .NR suffix
        if not symbol.endswith('.NR'):
            symbol = f"{symbol}.NR"
        
        base_symbol = symbol.replace('.NR', '')
        
        # Try Yahoo Finance (primary source)
        try:
            logger.info(f"Trying Yahoo Finance for {symbol}")
            records = self.yahoo_finance.fetch(symbol, start_date, end_date)
            if records:
                logger.info(f"✓ Yahoo Finance: {len(records)} records for {symbol}")
                return records
            logger.warning(f"Yahoo Finance returned no data for {symbol}")
        except Exception as e:
            logger.warning(f"Yahoo Finance failed for {symbol}: {e}")
        
        # Try Alpha Vantage (fallback)
        try:
            logger.info(f"Trying Alpha Vantage for {symbol}")
            records = self.alpha_vantage.fetch(symbol, start_date, end_date)
            if records:
                logger.info(f"✓ Alpha Vantage: {len(records)} records for {symbol}")
                return records
            logger.warning(f"Alpha Vantage returned no data for {symbol}")
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
        
        # Try CSV import (manual fallback)
        if self.csv_data_dir:
            try:
                logger.info(f"Trying CSV import for {symbol}")
                csv_file = self.csv_data_dir / f"{base_symbol}.csv"
                
                if csv_file.exists():
                    records = self.csv_importer.import_file(csv_file, symbol)
                    
                    # Filter by date range
                    records = [
                        r for r in records
                        if start_date <= r.date <= end_date
                    ]
                    
                    if records:
                        logger.info(f"✓ CSV Import: {len(records)} records for {symbol}")
                        return records
                else:
                    logger.warning(f"CSV file not found: {csv_file}")
            except Exception as e:
                logger.warning(f"CSV import failed for {symbol}: {e}")
        
        # All sources failed
        raise DataSourceError(
            f"All data sources failed for {symbol}. "
            f"Tried: Yahoo Finance, Alpha Vantage" +
            (", CSV import" if self.csv_data_dir else "")
        )
    
    def fetch_current_price(self, symbol: str) -> float:
        """
        Fetch current price for an NSE stock.
        
        Args:
            symbol: NSE stock symbol (e.g., "SCOM.NR")
        
        Returns:
            Current price in KES
        
        Raises:
            DataSourceError: If unable to fetch current price
        """
        # Ensure symbol has .NR suffix
        if not symbol.endswith('.NR'):
            symbol = f"{symbol}.NR"
        
        # Try Yahoo Finance for current price
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if price:
                logger.info(f"Current price for {symbol}: {price} KES")
                return float(price)
                
        except Exception as e:
            logger.warning(f"Failed to fetch current price from Yahoo Finance: {e}")
        
        raise DataSourceError(f"Unable to fetch current price for {symbol}")
