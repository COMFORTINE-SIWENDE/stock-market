"""Yahoo Finance adapter for NSE stock data."""
import logging
from datetime import date
from typing import List

try:
    import yfinance as yf
except ImportError:
    yf = None

from app.models.ohlcv import OHLCVRecord


logger = logging.getLogger(__name__)


class YahooFinanceNSE:
    """Adapter for fetching NSE stock data from Yahoo Finance."""
    
    def __init__(self):
        """Initialize Yahoo Finance NSE adapter."""
        if yf is None:
            logger.warning("yfinance library not installed. Yahoo Finance adapter will not work.")
    
    def fetch(self, symbol: str, start: date, end: date) -> List[OHLCVRecord]:
        """
        Fetch historical OHLCV data for an NSE stock from Yahoo Finance.
        
        Args:
            symbol: NSE stock symbol with .NR suffix (e.g., "SCOM.NR")
            start: Start date for data
            end: End date for data
        
        Returns:
            List of OHLCVRecord objects
        """
        if yf is None:
            logger.error("yfinance library not installed")
            return []
        
        try:
            # Ensure symbol has .NR suffix
            if not symbol.endswith(".NR"):
                symbol = f"{symbol}.NR"
            
            logger.info(f"Fetching {symbol} data from Yahoo Finance: {start} to {end}")
            
            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)
            
            if df.empty:
                logger.warning(f"No data returned from Yahoo Finance for {symbol}")
                return []
            
            # Convert to OHLCVRecord format
            records = []
            for idx, row in df.iterrows():
                try:
                    record = OHLCVRecord(
                        symbol=symbol,
                        date=idx.date(),
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume']),
                        currency='KES',
                        market='NSE'
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse row for {symbol} on {idx.date()}: {e}")
                    continue
            
            logger.info(f"Fetched {len(records)} records for {symbol} from Yahoo Finance")
            return records
            
        except Exception as e:
            logger.error(f"Failed to fetch {symbol} from Yahoo Finance: {e}")
            return []
