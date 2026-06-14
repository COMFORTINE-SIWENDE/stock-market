"""Alpha Vantage adapter for NSE stock data."""
import logging
import os
from datetime import date, datetime
from typing import List, Optional

try:
    import requests
except ImportError:
    requests = None

from app.models.ohlcv import OHLCVRecord


logger = logging.getLogger(__name__)


class AlphaVantageNSE:
    """Adapter for fetching NSE stock data from Alpha Vantage API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage NSE adapter.
        
        Args:
            api_key: Alpha Vantage API key (defaults to ALPHA_VANTAGE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured")
        
        if requests is None:
            logger.warning("requests library not installed. Alpha Vantage adapter will not work.")
    
    def fetch(self, symbol: str, start: date, end: date) -> List[OHLCVRecord]:
        """
        Fetch historical OHLCV data for an NSE stock from Alpha Vantage.
        
        Args:
            symbol: NSE stock symbol (with or without .NR suffix)
            start: Start date for data
            end: End date for data
        
        Returns:
            List of OHLCVRecord objects
        """
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured")
            return []
        
        if requests is None:
            logger.error("requests library not installed")
            return []
        
        try:
            # Remove .NR suffix for Alpha Vantage (use base symbol)
            base_symbol = symbol.replace(".NR", "")
            
            logger.info(f"Fetching {symbol} data from Alpha Vantage: {start} to {end}")
            
            # Alpha Vantage TIME_SERIES_DAILY endpoint
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': f"{base_symbol}.NSE",  # NSE market suffix
                'outputsize': 'full',
                'apikey': self.api_key
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return []
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return []
            
            if 'Time Series (Daily)' not in data:
                logger.warning(f"No time series data for {symbol} from Alpha Vantage")
                return []
            
            # Parse time series data
            time_series = data['Time Series (Daily)']
            records = []
            
            for date_str, values in time_series.items():
                try:
                    record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Filter by date range
                    if record_date < start or record_date > end:
                        continue
                    
                    record = OHLCVRecord(
                        symbol=symbol if symbol.endswith('.NR') else f"{symbol}.NR",
                        date=record_date,
                        open=float(values['1. open']),
                        high=float(values['2. high']),
                        low=float(values['3. low']),
                        close=float(values['4. close']),
                        volume=int(float(values['5. volume'])),
                        currency='KES',
                        market='NSE'
                    )
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse data for {symbol} on {date_str}: {e}")
                    continue
            
            # Sort by date ascending
            records.sort(key=lambda r: r.date)
            
            logger.info(f"Fetched {len(records)} records for {symbol} from Alpha Vantage")
            return records
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching {symbol} from Alpha Vantage: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch {symbol} from Alpha Vantage: {e}")
            return []
