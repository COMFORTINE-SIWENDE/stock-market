"""OHLCV data models and validation results."""
from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class OHLCVRecord:
    """Represents a single OHLCV (Open, High, Low, Close, Volume) data record."""
    
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    currency: str
    market: str
    
    def __post_init__(self):
        """Validate OHLCV constraints after initialization."""
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValueError("Prices cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if self.low > self.high:
            raise ValueError(f"Low price ({self.low}) cannot be greater than high price ({self.high})")


@dataclass
class ValidationResult:
    """Result of data validation."""
    
    passed: bool
    errors: List[str]
    warnings: List[str]
    
    def __init__(self, passed: bool = True, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.passed = passed
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str) -> None:
        """Add an error message and mark validation as failed."""
        self.errors.append(error)
        self.passed = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.passed
