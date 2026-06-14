#!/usr/bin/env python3
"""
Verification script for NSE market adaptation migration.
Checks that all schema changes have been applied correctly.
"""

import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any
from app.config.config import settings


def get_engine() -> Engine:
    """Create database engine."""
    return create_engine(settings.sync_database_url)


def verify_column_exists(inspector, table_name: str, column_name: str, expected_type: str = None) -> tuple[bool, str]:
    """Verify a column exists in a table with optional type check."""
    columns = inspector.get_columns(table_name)
    column_names = [col['name'] for col in columns]
    
    if column_name not in column_names:
        return False, f"Column '{column_name}' NOT FOUND in table '{table_name}'"
    
    if expected_type:
        column = next(col for col in columns if col['name'] == column_name)
        col_type = str(column['type']).upper()
        if expected_type.upper() not in col_type:
            return False, f"Column '{column_name}' has type '{col_type}', expected '{expected_type}'"
    
    return True, f"✓ Column '{column_name}' exists in '{table_name}'"


def verify_index_exists(inspector, table_name: str, index_name: str) -> tuple[bool, str]:
    """Verify an index exists on a table."""
    indexes = inspector.get_indexes(table_name)
    index_names = [idx['name'] for idx in indexes]
    
    if index_name not in index_names:
        return False, f"Index '{index_name}' NOT FOUND on table '{table_name}'"
    
    return True, f"✓ Index '{index_name}' exists on '{table_name}'"


def verify_table_exists(inspector, table_name: str) -> tuple[bool, str]:
    """Verify a table exists."""
    tables = inspector.get_table_names()
    
    if table_name not in tables:
        return False, f"Table '{table_name}' NOT FOUND"
    
    return True, f"✓ Table '{table_name}' exists"


def verify_default_values(engine: Engine) -> List[tuple[bool, str]]:
    """Verify default values have been applied to existing records."""
    results = []
    
    with engine.connect() as conn:
        # Check stock_symbols defaults
        result = conn.execute(text("""
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN market = 'US' THEN 1 END) as us_market,
                   COUNT(CASE WHEN currency = 'USD' THEN 1 END) as usd_currency
            FROM stock_symbols
        """))
        row = result.fetchone()
        
        if row and row[0] > 0:  # If there are records
            if row[1] == row[0]:
                results.append((True, f"✓ All {row[0]} stock_symbols have market='US' as default"))
            else:
                results.append((False, f"✗ Only {row[1]}/{row[0]} stock_symbols have market='US'"))
            
            if row[2] == row[0]:
                results.append((True, f"✓ All {row[0]} stock_symbols have currency='USD' as default"))
            else:
                results.append((False, f"✗ Only {row[2]}/{row[0]} stock_symbols have currency='USD'"))
        else:
            results.append((True, "✓ No existing stock_symbols records to verify defaults"))
        
        # Check stock_data defaults
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN market = 'US' THEN 1 END) as us_market,
                   COUNT(CASE WHEN currency = 'USD' THEN 1 END) as usd_currency
            FROM stock_data
        """))
        row = result.fetchone()
        
        if row and row[0] > 0:
            if row[1] == row[0]:
                results.append((True, f"✓ All {row[0]} stock_data records have market='US' as default"))
            else:
                results.append((False, f"✗ Only {row[1]}/{row[0]} stock_data records have market='US'"))
            
            if row[2] == row[0]:
                results.append((True, f"✓ All {row[0]} stock_data records have currency='USD' as default"))
            else:
                results.append((False, f"✗ Only {row[2]}/{row[0]} stock_data records have currency='USD'"))
        else:
            results.append((True, "✓ No existing stock_data records to verify defaults"))
        
        # Check news_articles defaults
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN market = 'US' THEN 1 END) as us_market,
                   COUNT(CASE WHEN language = 'en' THEN 1 END) as en_language
            FROM news_articles
        """))
        row = result.fetchone()
        
        if row and row[0] > 0:
            if row[1] == row[0]:
                results.append((True, f"✓ All {row[0]} news_articles have market='US' as default"))
            else:
                results.append((False, f"✗ Only {row[1]}/{row[0]} news_articles have market='US'"))
            
            if row[2] == row[0]:
                results.append((True, f"✓ All {row[0]} news_articles have language='en' as default"))
            else:
                results.append((False, f"✗ Only {row[2]}/{row[0]} news_articles have language='en'"))
        else:
            results.append((True, "✓ No existing news_articles records to verify defaults"))
    
    return results


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("NSE Market Adaptation Migration Verification")
    print("=" * 70)
    print()
    
    engine = get_engine()
    inspector = inspect(engine)
    
    all_checks = []
    
    # Verify stock_symbols table changes
    print("Checking stock_symbols table...")
    all_checks.append(verify_column_exists(inspector, "stock_symbols", "market", "VARCHAR"))
    all_checks.append(verify_column_exists(inspector, "stock_symbols", "currency", "VARCHAR"))
    all_checks.append(verify_column_exists(inspector, "stock_symbols", "base_symbol", "VARCHAR"))
    all_checks.append(verify_index_exists(inspector, "stock_symbols", "ix_stock_symbols_market"))
    print()
    
    # Verify stock_data table changes
    print("Checking stock_data table...")
    all_checks.append(verify_column_exists(inspector, "stock_data", "market", "VARCHAR"))
    all_checks.append(verify_column_exists(inspector, "stock_data", "currency", "VARCHAR"))
    all_checks.append(verify_index_exists(inspector, "stock_data", "ix_stock_data_market"))
    print()
    
    # Verify news_articles table changes
    print("Checking news_articles table...")
    all_checks.append(verify_column_exists(inspector, "news_articles", "market", "VARCHAR"))
    all_checks.append(verify_column_exists(inspector, "news_articles", "language", "VARCHAR"))
    all_checks.append(verify_index_exists(inspector, "news_articles", "ix_news_articles_market"))
    print()
    
    # Verify new tables
    print("Checking new tables...")
    all_checks.append(verify_table_exists(inspector, "data_quality_metrics"))
    all_checks.append(verify_table_exists(inspector, "nse_holidays"))
    print()
    
    # Verify data_quality_metrics columns and indexes
    if verify_table_exists(inspector, "data_quality_metrics")[0]:
        print("Checking data_quality_metrics table structure...")
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "id", "INTEGER"))
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "symbol_id", "INTEGER"))
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "source", "VARCHAR"))
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "error_type", "VARCHAR"))
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "error_details", "VARCHAR"))
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "recorded_at", "TIMESTAMP"))
        all_checks.append(verify_column_exists(inspector, "data_quality_metrics", "market", "VARCHAR"))
        all_checks.append(verify_index_exists(inspector, "data_quality_metrics", "ix_dqm_symbol_date"))
        print()
    
    # Verify nse_holidays columns and indexes
    if verify_table_exists(inspector, "nse_holidays")[0]:
        print("Checking nse_holidays table structure...")
        all_checks.append(verify_column_exists(inspector, "nse_holidays", "id", "INTEGER"))
        all_checks.append(verify_column_exists(inspector, "nse_holidays", "date", "DATE"))
        all_checks.append(verify_column_exists(inspector, "nse_holidays", "name", "VARCHAR"))
        all_checks.append(verify_column_exists(inspector, "nse_holidays", "is_recurring", "BOOLEAN"))
        all_checks.append(verify_index_exists(inspector, "nse_holidays", "ix_nse_holidays_date"))
        print()
    
    # Verify default values
    print("Checking default values on existing records...")
    default_checks = verify_default_values(engine)
    all_checks.extend(default_checks)
    print()
    
    # Print all results
    print("=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    for success, message in all_checks:
        print(message)
    print()
    
    # Summary
    passed = sum(1 for success, _ in all_checks if success)
    failed = sum(1 for success, _ in all_checks if not success)
    total = len(all_checks)
    
    print("=" * 70)
    print(f"Summary: {passed}/{total} checks passed")
    if failed > 0:
        print(f"WARNING: {failed} checks FAILED")
        print("=" * 70)
        sys.exit(1)
    else:
        print("All verification checks PASSED ✓")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
