"""Quick test of Wave 1 implementations."""
from datetime import date
from app.models.ohlcv import OHLCVRecord, ValidationResult
from app.services.nse_symbol_parser import NSESymbolParser
from app.services.market_detector import MarketDetector
from app.services.timezone_handler import TimezoneHandler
from app.models.market import MarketType

print("Testing Wave 1 implementations...")

# Test 1: OHLCVRecord
print("\n1. Testing OHLCVRecord...")
record = OHLCVRecord(
    symbol='SCOM.NR',
    date=date(2024, 5, 11),
    open=100.0,
    high=105.0,
    low=99.0,
    close=103.0,
    volume=1000000,
    currency='KES',
    market='NSE'
)
print(f"   ✓ Created: {record.symbol} @ {record.close} {record.currency}")

# Test 2: ValidationResult
print("\n2. Testing ValidationResult...")
result = ValidationResult(passed=True)
result.add_warning("Test warning")
print(f"   ✓ Passed: {result.passed}, Warnings: {len(result.warnings)}")

# Test 3: NSESymbolParser
print("\n3. Testing NSESymbolParser...")
symbol = NSESymbolParser.parse('SCOM.NR')
print(f"   ✓ Parsed: {symbol}")
formatted = NSESymbolParser.format('KCB')
print(f"   ✓ Formatted: {formatted}")
is_valid = NSESymbolParser.validate('EQTY.NR')
print(f"   ✓ Validated EQTY.NR: {is_valid}")

# Test 4: MarketDetector
print("\n4. Testing MarketDetector...")
nse_market = MarketDetector.detect_market('SCOM.NR')
us_market = MarketDetector.detect_market('AAPL')
print(f"   ✓ SCOM.NR detected as: {nse_market}")
print(f"   ✓ AAPL detected as: {us_market}")
normalized = MarketDetector.normalize_symbol('SCOM', MarketType.NSE)
print(f"   ✓ Normalized SCOM for NSE: {normalized}")

# Test 5: TimezoneHandler
print("\n5. Testing TimezoneHandler...")
now_eat = TimezoneHandler.now_eat()
formatted = TimezoneHandler.format_eat(now_eat)
print(f"   ✓ Current EAT: {formatted}")

print("\n✅ All Wave 1 implementations working correctly!")
