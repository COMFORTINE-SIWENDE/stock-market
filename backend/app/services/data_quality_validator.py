"""Data quality validator for OHLCV data with metrics tracking."""
import logging
from datetime import datetime
from typing import Optional

from app.models.ohlcv import OHLCVRecord, ValidationResult


logger = logging.getLogger(__name__)


class MetricsTracker:
    """Tracks data quality metrics for failures."""
    
    def __init__(self):
        self.failures = []
    
    def track(self, symbol: str, source: str, error_type: str, details: str) -> None:
        """
        Track a data quality failure.
        
        Args:
            symbol: Stock symbol
            source: Data source name
            error_type: Type of error
            details: Error details
        """
        self.failures.append({
            'symbol': symbol,
            'source': source,
            'error_type': error_type,
            'details': details,
            'timestamp': datetime.utcnow()
        })
        logger.warning(f"Data quality issue: {symbol} from {source} - {error_type}: {details}")


class DataQualityValidator:
    """Validates OHLCV data quality with constraint checking."""
    
    # Outlier threshold: 50% price change from previous day
    OUTLIER_THRESHOLD = 0.50
    
    def __init__(self, metrics_tracker: MetricsTracker):
        """
        Initialize the data quality validator.
        
        Args:
            metrics_tracker: MetricsTracker instance for logging failures
        """
        self.metrics_tracker = metrics_tracker
    
    def validate_ohlcv(self, record: OHLCVRecord) -> ValidationResult:
        """
        Validate OHLCV data constraints.
        
        Checks:
        - Low <= Open <= High
        - Low <= Close <= High
        - All prices > 0
        - Volume >= 0
        
        Args:
            record: OHLCVRecord to validate
        
        Returns:
            ValidationResult with pass/fail status and error messages
        """
        result = ValidationResult(passed=True)
        
        # Check: All prices must be positive
        if record.open <= 0:
            result.add_error(f"Open price must be positive, got {record.open}")
        if record.high <= 0:
            result.add_error(f"High price must be positive, got {record.high}")
        if record.low <= 0:
            result.add_error(f"Low price must be positive, got {record.low}")
        if record.close <= 0:
            result.add_error(f"Close price must be positive, got {record.close}")
        
        # Check: Volume must be non-negative
        if record.volume < 0:
            result.add_error(f"Volume cannot be negative, got {record.volume}")
        
        # Check: Low must be the lowest price
        if record.low > record.open:
            result.add_error(f"Low ({record.low}) cannot be greater than Open ({record.open})")
        if record.low > record.high:
            result.add_error(f"Low ({record.low}) cannot be greater than High ({record.high})")
        if record.low > record.close:
            result.add_error(f"Low ({record.low}) cannot be greater than Close ({record.close})")
        
        # Check: High must be the highest price
        if record.high < record.open:
            result.add_error(f"High ({record.high}) cannot be less than Open ({record.open})")
        if record.high < record.low:
            result.add_error(f"High ({record.high}) cannot be less than Low ({record.low})")
        if record.high < record.close:
            result.add_error(f"High ({record.high}) cannot be less than Close ({record.close})")
        
        # Track failures
        if not result.passed:
            self.track_failure(
                record.symbol,
                'validation',
                'OHLCV_CONSTRAINT_VIOLATION',
                '; '.join(result.errors)
            )
        
        return result
    
    def detect_outliers(
        self, 
        current: OHLCVRecord, 
        previous: Optional[OHLCVRecord]
    ) -> bool:
        """
        Detect outliers based on price change from previous day.
        
        An outlier is defined as a price change > 50% from previous day's close.
        
        Args:
            current: Current day's OHLCV record
            previous: Previous day's OHLCV record (optional)
        
        Returns:
            True if current record is an outlier, False otherwise
        """
        if previous is None:
            # No previous data to compare, not an outlier
            return False
        
        if previous.close <= 0:
            # Invalid previous close, can't detect outlier
            return False
        
        # Calculate percentage change
        price_change = abs(current.close - previous.close) / previous.close
        
        is_outlier = price_change > self.OUTLIER_THRESHOLD
        
        if is_outlier:
            self.track_failure(
                current.symbol,
                'outlier_detection',
                'PRICE_OUTLIER',
                f"Price changed {price_change:.2%} from {previous.close} to {current.close} "
                f"(threshold: {self.OUTLIER_THRESHOLD:.2%})"
            )
        
        return is_outlier
    
    def track_failure(
        self, 
        symbol: str, 
        source: str, 
        error_type: str, 
        details: str
    ) -> None:
        """
        Track a data quality failure.
        
        Args:
            symbol: Stock symbol
            source: Data source name
            error_type: Type of error
            details: Error details
        """
        self.metrics_tracker.track(symbol, source, error_type, details)
