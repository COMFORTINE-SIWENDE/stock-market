#!/usr/bin/env python3
"""
Generate synthetic NSE stock data for testing and training
Based on real NSE stock price characteristics
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.config.database import sync_engine
from app.models.stock import StockSymbol, StockData
from app.utils.logger import logger

# NSE Stock characteristics (approximate values in KES)
NSE_STOCKS_CONFIG = {
    'SCOM.NR': {
        'name': 'Safaricom PLC',
        'base_price': 25.0,
        'volatility': 0.02,
        'drift': 0.0001,  # Slight upward trend
        'volume_mean': 50_000_000,
        'volume_std': 15_000_000
    },
    'KCB.NR': {
        'name': 'KCB Group PLC',
        'base_price': 45.0,
        'volatility': 0.025,
        'drift': 0.00005,
        'volume_mean': 5_000_000,
        'volume_std': 2_000_000
    },
    'EQTY.NR': {
        'name': 'Equity Group Holdings PLC',
        'base_price': 50.0,
        'volatility': 0.023,
        'drift': 0.00008,
        'volume_mean': 8_000_000,
        'volume_std': 3_000_000
    },
    'EABL.NR': {
        'name': 'East African Breweries Limited',
        'base_price': 150.0,
        'volatility': 0.018,
        'drift': 0.00005,
        'volume_mean': 1_500_000,
        'volume_std': 500_000
    },
    'COOP.NR': {
        'name': 'Co-operative Bank of Kenya Limited',
        'base_price': 14.0,
        'volatility': 0.022,
        'drift': 0.00003,
        'volume_mean': 10_000_000,
        'volume_std': 4_000_000
    },
    'ABSA.NR': {
        'name': 'Absa Bank Kenya PLC',
        'base_price': 13.0,
        'volatility': 0.020,
        'drift': 0.00002,
        'volume_mean': 3_000_000,
        'volume_std': 1_000_000
    },
    'SCBK.NR': {
        'name': 'Standard Chartered Bank Kenya Limited',
        'base_price': 160.0,
        'volatility': 0.019,
        'drift': 0.00004,
        'volume_mean': 500_000,
        'volume_std': 200_000
    },
    'BAMB.NR': {
        'name': 'Bamburi Cement Limited',
        'base_price': 30.0,
        'volatility': 0.021,
        'drift': -0.00001,  # Slight downward trend
        'volume_mean': 800_000,
        'volume_std': 300_000
    },
    'BAT.NR': {
        'name': 'British American Tobacco Kenya PLC',
        'base_price': 400.0,
        'volatility': 0.017,
        'drift': 0.00003,
        'volume_mean': 200_000,
        'volume_std': 80_000
    },
    'DTBK.NR': {
        'name': 'Diamond Trust Bank Kenya Limited',
        'base_price': 60.0,
        'volatility': 0.023,
        'drift': 0.00005,
        'volume_mean': 1_000_000,
        'volume_std': 400_000
    },
    'NCBA.NR': {
        'name': 'NCBA Group PLC',
        'base_price': 35.0,
        'volatility': 0.024,
        'drift': 0.00006,
        'volume_mean': 2_000_000,
        'volume_std': 800_000
    },
    'NMG.NR': {
        'name': 'Nation Media Group PLC',
        'base_price': 18.0,
        'volatility': 0.026,
        'drift': -0.00002,
        'volume_mean': 1_500_000,
        'volume_std': 600_000
    },
    'SBIC.NR': {
        'name': 'Stanbic Holdings PLC',
        'base_price': 95.0,
        'volatility': 0.021,
        'drift': 0.00004,
        'volume_mean': 900_000,
        'volume_std': 350_000
    }
}


def generate_stock_prices(config, days=730, seed=None):
    """
    Generate synthetic stock prices using Geometric Brownian Motion
    
    Args:
        config: Stock configuration dict with base_price, volatility, drift
        days: Number of days to generate
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with OHLCV data
    """
    if seed:
        np.random.seed(seed)
    
    base_price = config['base_price']
    volatility = config['volatility']
    drift = config['drift']
    volume_mean = config['volume_mean']
    volume_std = config['volume_std']
    
    # Generate daily returns using Geometric Brownian Motion
    dt = 1  # Daily
    returns = np.random.normal(drift * dt, volatility * np.sqrt(dt), days)
    
    # Generate prices from returns
    prices = [base_price]
    for ret in returns:
        prices.append(prices[-1] * np.exp(ret))
    
    prices = np.array(prices[1:])  # Remove first element
    
    # Generate OHLC from close prices
    # Open: previous close with small random variation
    opens = prices * (1 + np.random.normal(0, 0.002, days))
    
    # High: max of open/close plus random variation
    highs = np.maximum(opens, prices) * (1 + np.abs(np.random.normal(0, 0.005, days)))
    
    # Low: min of open/close minus random variation
    lows = np.minimum(opens, prices) * (1 - np.abs(np.random.normal(0, 0.005, days)))
    
    # Ensure OHLC consistency
    highs = np.maximum(highs, np.maximum(opens, prices))
    lows = np.minimum(lows, np.minimum(opens, prices))
    
    # Generate volumes (log-normal distribution)
    volumes = np.random.lognormal(
        np.log(volume_mean), 
        volume_std / volume_mean, 
        days
    ).astype(int)
    
    # Create date range (exclude weekends for NSE trading days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days + days//5)  # Add buffer for weekends
    
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    trading_days = all_dates[all_dates.dayofweek < 5]  # Monday=0, Friday=4
    trading_days = trading_days[:days]  # Take exactly 'days' trading days
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': trading_days,
        'open': opens[:len(trading_days)],
        'high': highs[:len(trading_days)],
        'low': lows[:len(trading_days)],
        'close': prices[:len(trading_days)],
        'volume': volumes[:len(trading_days)]
    })
    
    return df


def populate_database():
    """Populate database with synthetic NSE stock data"""
    
    print("=" * 70)
    print("  NSE Synthetic Data Generator")
    print("=" * 70)
    
    with Session(sync_engine) as session:
        for symbol, config in NSE_STOCKS_CONFIG.items():
            print(f"\n📊 Generating data for {symbol} ({config['name']})")
            
            # Get or create symbol
            stock_symbol = session.exec(
                select(StockSymbol).where(StockSymbol.symbol == symbol)
            ).first()
            
            if not stock_symbol:
                base_symbol = symbol.replace('.NR', '')
                stock_symbol = StockSymbol(
                    symbol=symbol,
                    company_name=config['name'],
                    exchange="NSE",
                    market="NSE",
                    currency="KES",
                    base_symbol=base_symbol,
                    is_active=True
                )
                session.add(stock_symbol)
                session.commit()
                session.refresh(stock_symbol)
                logger.info(f"Created symbol: {symbol}")
            
            # Check existing data
            existing_count = session.exec(
                select(StockData).where(StockData.symbol_id == stock_symbol.id)
            ).all()
            
            if len(existing_count) > 0:
                print(f"  ⚠️  {len(existing_count)} existing records found. Skipping...")
                continue
            
            # Generate synthetic data (2 years = 730 days, ~520 trading days)
            df = generate_stock_prices(config, days=520, seed=hash(symbol) % 10000)
            
            print(f"  Generated {len(df)} trading days")
            print(f"  Price range: KES {df['close'].min():.2f} - {df['close'].max():.2f}")
            print(f"  Avg volume: {df['volume'].mean():,.0f}")
            
            # Insert into database
            inserted = 0
            for _, row in df.iterrows():
                stock_data = StockData(
                    symbol_id=stock_symbol.id,
                    date=row['date'].date(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    adj_close=float(row['close']),
                    market="NSE",
                    currency="KES"
                )
                session.add(stock_data)
                inserted += 1
                
                if inserted % 100 == 0:
                    session.commit()
            
            session.commit()
            print(f"  ✅ Inserted {inserted} records for {symbol}")
    
    print("\n" + "=" * 70)
    print("✅ Synthetic data generation complete!")
    print("=" * 70)
    
    # Summary
    with Session(sync_engine) as session:
        for symbol in NSE_STOCKS_CONFIG.keys():
            stock_symbol = session.exec(
                select(StockSymbol).where(StockSymbol.symbol == symbol)
            ).first()
            
            if stock_symbol:
                count = len(session.exec(
                    select(StockData).where(StockData.symbol_id == stock_symbol.id)
                ).all())
                
                if count > 0:
                    latest = session.exec(
                        select(StockData)
                        .where(StockData.symbol_id == stock_symbol.id)
                        .order_by(StockData.date.desc())
                    ).first()
                    
                    print(f"  {symbol:12} : {count:4} records, latest: {latest.date} (KES {latest.close:.2f})")


if __name__ == "__main__":
    populate_database()
