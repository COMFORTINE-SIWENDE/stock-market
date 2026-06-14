"""Market detector for routing symbols to correct market pipelines."""
from app.models.market import MarketType


class MarketDetector:
    """Detects market type from stock symbol format."""
    
    @staticmethod
    def detect_market(symbol: str) -> MarketType:
        """
        Detect the market type based on symbol format.
        
        NSE stocks are identified by the .NR suffix (e.g., SCOM.NR).
        All other symbols default to US market.
        
        Args:
            symbol: Stock symbol string
        
        Returns:
            MarketType enum (US or NSE)
        """
        if not symbol:
            return MarketType.US
        
        symbol = symbol.strip().upper()
        
        # Check for NSE suffix
        if symbol.endswith(".NR"):
            return MarketType.NSE
        
        # Default to US market
        return MarketType.US
    
    @staticmethod
    def normalize_symbol(symbol: str, market: MarketType) -> str:
        """
        Normalize a symbol for the given market.
        
        For NSE stocks, ensures .NR suffix is present.
        For US stocks, removes any .NR suffix if present.
        
        Args:
            symbol: Stock symbol string
            market: Market type
        
        Returns:
            Normalized symbol string
        """
        if not symbol:
            return symbol
        
        symbol = symbol.strip().upper()
        
        if market == MarketType.NSE:
            # Ensure NSE symbols have .NR suffix
            if not symbol.endswith(".NR"):
                return f"{symbol}.NR"
            return symbol
        else:
            # Remove .NR suffix for US symbols
            if symbol.endswith(".NR"):
                return symbol.replace(".NR", "")
            return symbol
