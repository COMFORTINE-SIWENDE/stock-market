"""Unit tests for market models.

Tests the MarketType enum and NSESymbol dataclass.
"""

import pytest
from app.models.market import MarketType, NSESymbol


class TestMarketType:
    """Tests for MarketType enum."""
    
    def test_market_type_us(self):
        """Test US market type value."""
        assert MarketType.US == "US"
        assert MarketType.US.value == "US"
    
    def test_market_type_nse(self):
        """Test NSE market type value."""
        assert MarketType.NSE == "NSE"
        assert MarketType.NSE.value == "NSE"
    
    def test_market_type_members(self):
        """Test that MarketType has exactly two members."""
        assert len(MarketType) == 2
        assert set(MarketType) == {MarketType.US, MarketType.NSE}
    
    def test_market_type_string_comparison(self):
        """Test that MarketType can be compared with strings."""
        assert MarketType.US == "US"
        assert MarketType.NSE == "NSE"


class TestNSESymbol:
    """Tests for NSESymbol dataclass."""
    
    def test_nse_symbol_creation_with_defaults(self):
        """Test creating NSESymbol with default suffix."""
        symbol = NSESymbol(base="SCOM")
        assert symbol.base == "SCOM"
        assert symbol.suffix == ".NR"
    
    def test_nse_symbol_creation_with_explicit_suffix(self):
        """Test creating NSESymbol with explicit suffix."""
        symbol = NSESymbol(base="KCB", suffix=".NR")
        assert symbol.base == "KCB"
        assert symbol.suffix == ".NR"
    
    def test_nse_symbol_str_method(self):
        """Test __str__ method returns full symbol."""
        symbol = NSESymbol(base="SCOM")
        assert str(symbol) == "SCOM.NR"
    
    def test_nse_symbol_str_with_different_bases(self):
        """Test __str__ with various base symbols."""
        test_cases = [
            ("SCOM", "SCOM.NR"),
            ("KCB", "KCB.NR"),
            ("EQTY", "EQTY.NR"),
            ("EABL", "EABL.NR"),
            ("COOP", "COOP.NR"),
        ]
        for base, expected in test_cases:
            symbol = NSESymbol(base=base)
            assert str(symbol) == expected
    
    def test_nse_symbol_equality(self):
        """Test that NSESymbol instances with same values are equal."""
        symbol1 = NSESymbol(base="SCOM")
        symbol2 = NSESymbol(base="SCOM")
        assert symbol1 == symbol2
    
    def test_nse_symbol_inequality(self):
        """Test that NSESymbol instances with different values are not equal."""
        symbol1 = NSESymbol(base="SCOM")
        symbol2 = NSESymbol(base="KCB")
        assert symbol1 != symbol2
    
    def test_nse_symbol_with_custom_suffix(self):
        """Test NSESymbol with a custom suffix."""
        symbol = NSESymbol(base="TEST", suffix=".XX")
        assert str(symbol) == "TEST.XX"
    
    def test_nse_symbol_empty_base(self):
        """Test NSESymbol with empty base string."""
        symbol = NSESymbol(base="")
        assert str(symbol) == ".NR"
    
    def test_nse_symbol_attributes_accessible(self):
        """Test that NSESymbol attributes are accessible."""
        symbol = NSESymbol(base="SCOM")
        assert hasattr(symbol, "base")
        assert hasattr(symbol, "suffix")
        assert symbol.base == "SCOM"
        assert symbol.suffix == ".NR"
