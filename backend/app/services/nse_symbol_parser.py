"""NSE symbol parser and validator for Nairobi Securities Exchange stocks."""
from app.models.market import NSESymbol


class NSESymbolParser:
    """Parser and validator for NSE stock symbols."""
    
    # NSE 20 Index constituents and other major NSE stocks
    VALID_SYMBOLS = {
        "SCOM",  # Safaricom PLC
        "KCB",   # KCB Group PLC
        "EQTY",  # Equity Group Holdings PLC
        "EABL",  # East African Breweries Limited
        "COOP",  # Co-operative Bank of Kenya Limited
        "ABSA",  # Absa Bank Kenya PLC
        "SCBK",  # Standard Chartered Bank Kenya Limited
        "BAMB",  # Bamburi Cement Limited
        "BAT",   # British American Tobacco Kenya PLC
        "DTBK",  # Diamond Trust Bank Kenya Limited
        "NCBA",  # NCBA Group PLC
        "NMG",   # Nation Media Group Limited
        "SBIC",  # Stanbic Holdings PLC
        "CIC",   # CIC Insurance Group Limited
        "ARM",   # ARM Cement Limited
        "KEGN",  # KenGen Limited
        "TOTL",  # Total Kenya Limited
        "KNRE",  # Kenya Reinsurance Corporation Limited
        "CABL",  # Carbacid Investments Limited
        "KUKZ",  # Kakuzi PLC
    }
    
    @staticmethod
    def parse(symbol: str) -> NSESymbol:
        """
        Parse a symbol string into an NSESymbol object.
        
        Args:
            symbol: Symbol string (e.g., "SCOM.NR" or "SCOM")
        
        Returns:
            NSESymbol object
        
        Raises:
            ValueError: If symbol is invalid or not in whitelist
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        symbol = symbol.strip().upper()
        
        # Handle symbols with .NR suffix
        if ".NR" in symbol:
            base = symbol.replace(".NR", "")
            suffix = "NR"
        else:
            base = symbol
            suffix = "NR"
        
        # Validate base symbol is in whitelist
        if base not in NSESymbolParser.VALID_SYMBOLS:
            raise ValueError(
                f"Invalid NSE symbol: {base}. "
                f"Must be one of the NSE 20 constituents: {', '.join(sorted(NSESymbolParser.VALID_SYMBOLS))}"
            )
        
        return NSESymbol(base=base, suffix=suffix)
    
    @staticmethod
    def validate(symbol: str) -> bool:
        """
        Validate if a symbol is a valid NSE symbol.
        
        Args:
            symbol: Symbol string to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            NSESymbolParser.parse(symbol)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def format(base: str) -> str:
        """
        Format a base symbol into the full NSE format with .NR suffix.
        
        Args:
            base: Base symbol (e.g., "SCOM")
        
        Returns:
            Formatted symbol (e.g., "SCOM.NR")
        
        Raises:
            ValueError: If base symbol is invalid
        """
        base = base.strip().upper()
        
        if base not in NSESymbolParser.VALID_SYMBOLS:
            raise ValueError(
                f"Invalid NSE symbol: {base}. "
                f"Must be one of the NSE 20 constituents."
            )
        
        return f"{base}.NR"
