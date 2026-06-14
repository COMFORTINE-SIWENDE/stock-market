#!/usr/bin/env python3
"""
Detailed schema inspection script to verify exact column types and constraints.
"""

from sqlalchemy import create_engine, text
from app.config.config import settings


def main():
    """Run detailed schema checks."""
    engine = create_engine(settings.sync_database_url)
    
    print("=" * 80)
    print("DETAILED SCHEMA VERIFICATION")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        # Check stock_symbols columns
        print("1. stock_symbols table - New columns:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'stock_symbols'
            AND column_name IN ('market', 'currency', 'base_symbol')
            ORDER BY column_name
        """))
        for row in result:
            print(f"   - {row.column_name}: {row.data_type}, nullable={row.is_nullable}, default={row.column_default}")
        print()
        
        # Check stock_data columns
        print("2. stock_data table - New columns:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'stock_data'
            AND column_name IN ('market', 'currency')
            ORDER BY column_name
        """))
        for row in result:
            print(f"   - {row.column_name}: {row.data_type}, nullable={row.is_nullable}, default={row.column_default}")
        print()
        
        # Check news_articles columns
        print("3. news_articles table - New columns:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'news_articles'
            AND column_name IN ('market', 'language')
            ORDER BY column_name
        """))
        for row in result:
            print(f"   - {row.column_name}: {row.data_type}, nullable={row.is_nullable}, default={row.column_default}")
        print()
        
        # Check indexes on market columns
        print("4. Indexes on market columns:")
        result = conn.execute(text("""
            SELECT tablename, indexname, indexdef
            FROM pg_indexes
            WHERE indexname LIKE '%market%'
            ORDER BY tablename, indexname
        """))
        for row in result:
            print(f"   - Table: {row.tablename}")
            print(f"     Index: {row.indexname}")
            print(f"     Definition: {row.indexdef}")
            print()
        
        # Check data_quality_metrics table structure
        print("5. data_quality_metrics table - All columns:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'data_quality_metrics'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"   - {row.column_name}: {row.data_type}, nullable={row.is_nullable}")
        print()
        
        # Check nse_holidays table structure
        print("6. nse_holidays table - All columns:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'nse_holidays'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"   - {row.column_name}: {row.data_type}, nullable={row.is_nullable}")
        print()
        
        # Check foreign keys
        print("7. Foreign key constraints:")
        result = conn.execute(text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name IN ('data_quality_metrics', 'nse_holidays')
            ORDER BY tc.table_name
        """))
        for row in result:
            print(f"   - {row.table_name}.{row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")
        print()
        
        # Sample data check
        print("8. Sample data from stock_symbols (showing new columns):")
        result = conn.execute(text("""
            SELECT symbol, market, currency, base_symbol
            FROM stock_symbols
            LIMIT 5
        """))
        for row in result:
            print(f"   - {row.symbol}: market={row.market}, currency={row.currency}, base_symbol={row.base_symbol}")
        print()
        
    print("=" * 80)
    print("Schema verification complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
