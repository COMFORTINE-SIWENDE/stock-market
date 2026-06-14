"""
Populate NSE holidays and stock symbols in the database.
This script ensures the NSE-focused system has all necessary data.
"""
import yaml
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select

from app.config.database import get_sync_session
from app.models.stock import StockSymbol
from app.models.market import MarketType


def load_nse_holidays():
    """Load NSE holidays from YAML config into database."""
    from sqlalchemy import text
    
    with get_sync_session() as session:
        # Load holidays from YAML
        config_path = Path(__file__).parent / "app" / "config" / "nse_holidays.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        holidays = config.get('holidays', [])
        
        print(f"\n📅 Loading {len(holidays)} NSE holidays...")
        
        # Clear existing holidays
        session.execute(text("DELETE FROM nse_holidays"))
        
        # Insert holidays
        for holiday in holidays:
            session.execute(
                text("""
                    INSERT INTO nse_holidays (date, name, is_recurring)
                    VALUES (:date, :name, :is_recurring)
                """),
                {
                    "date": holiday['date'],
                    "name": holiday['name'],
                    "is_recurring": holiday['is_recurring']
                }
            )
        
        session.commit()
        print(f"✅ Loaded {len(holidays)} NSE holidays")
        
        # Verify
        result = session.execute(text("SELECT COUNT(*) FROM nse_holidays"))
        count = result.scalar()
        print(f"✅ Verified: {count} holidays in database")


def populate_nse_stocks():
    """Add NSE 20 Index stocks to the database."""
    
    # NSE 20 Index constituents with company names
    nse_stocks = [
        ("SCOM.NR", "Safaricom PLC", "Telecommunications"),
        ("KCB.NR", "KCB Group PLC", "Banking"),
        ("EQTY.NR", "Equity Group Holdings PLC", "Banking"),
        ("EABL.NR", "East African Breweries Limited", "Consumer Goods"),
        ("COOP.NR", "Co-operative Bank of Kenya Limited", "Banking"),
        ("ABSA.NR", "Absa Bank Kenya PLC", "Banking"),
        ("SCBK.NR", "Standard Chartered Bank Kenya Limited", "Banking"),
        ("BAMB.NR", "Bamburi Cement Limited", "Construction"),
        ("BAT.NR", "British American Tobacco Kenya PLC", "Consumer Goods"),
        ("DTBK.NR", "Diamond Trust Bank Kenya Limited", "Banking"),
        ("NCBA.NR", "NCBA Group PLC", "Banking"),
        ("NMG.NR", "Nation Media Group PLC", "Media"),
        ("SBIC.NR", "Stanbic Holdings PLC", "Banking"),
    ]
    
    with get_sync_session() as session:
        print(f"\n📈 Adding {len(nse_stocks)} NSE stocks...")
        
        added = 0
        updated = 0
        
        for symbol, company_name, sector in nse_stocks:
            # Check if stock exists
            statement = select(StockSymbol).where(StockSymbol.symbol == symbol)
            existing = session.exec(statement).first()
            
            if existing:
                # Update existing
                existing.company_name = company_name
                existing.market = "NSE"
                existing.currency = "KES"
                existing.base_symbol = symbol.replace(".NR", "")
                existing.is_active = True
                session.add(existing)
                updated += 1
                print(f"   ↻ Updated: {symbol} - {company_name}")
            else:
                # Create new
                stock = StockSymbol(
                    symbol=symbol,
                    company_name=company_name,
                    market="NSE",
                    currency="KES",
                    base_symbol=symbol.replace(".NR", ""),
                    exchange="NSE",
                    is_active=True
                )
                session.add(stock)
                added += 1
                print(f"   ✓ Added: {symbol} - {company_name}")
        
        session.commit()
        print(f"\n✅ NSE Stocks: {added} added, {updated} updated")
        
        # Verify
        statement = select(StockSymbol).where(StockSymbol.market == "NSE")
        nse_stocks_in_db = session.exec(statement).all()
        print(f"✅ Verified: {len(nse_stocks_in_db)} NSE stocks in database")


def verify_setup():
    """Verify NSE setup is complete."""
    from sqlalchemy import text
    
    with get_sync_session() as session:
        print("\n🔍 Verifying NSE Setup...")
        
        # Check holidays
        result = session.execute(text("SELECT COUNT(*) FROM nse_holidays"))
        holiday_count = result.scalar()
        print(f"   NSE Holidays: {holiday_count}")
        
        # Check stocks
        statement = select(StockSymbol).where(StockSymbol.market == "NSE")
        nse_stocks = session.exec(statement).all()
        print(f"   NSE Stocks: {len(nse_stocks)}")
        
        # Show sample stocks
        if nse_stocks:
            print("\n   Sample NSE Stocks:")
            for stock in nse_stocks[:5]:
                print(f"      • {stock.symbol} - {stock.company_name} ({stock.currency})")
        
        # Check data quality metrics table
        result = session.execute(text("SELECT COUNT(*) FROM data_quality_metrics"))
        metrics_count = result.scalar()
        print(f"\n   Data Quality Metrics: {metrics_count} records")
        
        if holiday_count > 0 and len(nse_stocks) > 0:
            print("\n✅ NSE setup complete and verified!")
            return True
        else:
            print("\n❌ NSE setup incomplete")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("NSE DATA POPULATION SCRIPT")
    print("Nairobi Securities Exchange - Core System Setup")
    print("=" * 60)
    
    try:
        # Step 1: Load holidays
        load_nse_holidays()
        
        # Step 2: Populate stocks
        populate_nse_stocks()
        
        # Step 3: Verify
        verify_setup()
        
        print("\n" + "=" * 60)
        print("✅ NSE DATA POPULATION COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Collect NSE stock data:")
        print("   curl -X POST http://localhost:8000/stocks/collect \\")
        print("     -d '{\"symbols\":[\"SCOM.NR\",\"KCB.NR\"],\"days\":365}'")
        print("\n2. Check NSE market status:")
        print("   curl http://localhost:8000/api/v1/market/nse/status")
        print("\n3. Search NSE stocks:")
        print("   curl http://localhost:8000/symbols/search?q=safaricom&market=NSE")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
