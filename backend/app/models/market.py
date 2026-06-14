"""Market-related data models and enums.

This module defines market types and symbol structures for multi-market support.
"""

from dataclasses import dataclass
from enum import Enum


class MarketType(str, Enum):
    """Enumeration of supported stock markets.
    
    Attributes:
        US: United States stock market
        NSE: Nairobi Securities Exchange (Kenya)
    """
    US = "US"
    NSE = "NSE"


@dataclass
class NSESymbol:
    """Represents a Nairobi Securities Exchange stock symbol.
    
    NSE symbols consist of a base symbol (e.g., "SCOM") and a suffix (".NR").
    
    Attributes:
        base: The base symbol (e.g., "SCOM" for Safaricom)
        suffix: The market suffix, defaults to ".NR" for NSE
    
    Example:
        >>> symbol = NSESymbol(base="SCOM")
        >>> str(symbol)
        'SCOM.NR'
    """
    base: str
    suffix: str = ".NR"
    
    def __str__(self) -> str:
        """Return the full symbol string with suffix.
        
        Returns:
            Full symbol string (e.g., "SCOM.NR")
        """
        return f"{self.base}{self.suffix}"
