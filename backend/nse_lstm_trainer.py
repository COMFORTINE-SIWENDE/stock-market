#!/usr/bin/env python3
"""
NSE Stock Price LSTM Trainer
Collects NSE data and trains LSTM models for stock price prediction
Based on training-example.py structure but adapted for time-series forecasting
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# TensorFlow/Keras
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

# Scikit-learn
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Project imports
from sqlmodel import Session, select
from app.config.database import sync_engine
from app.models.stock import StockSymbol, StockData
from app.services.data_service import collect_stock_data
from app.utils.logger import logger

# ==================== CONFIGURATION ====================

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)

# Training configuration
SEQUENCE_LENGTH = 60  # Use 60 days of data to predict next day
TEST_SIZE = 0.2
VAL_SIZE = 0.1
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001

# Model save directory
MODEL_DIR = Path(__file__).parent / "app" / "models" / "trained"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# NSE stocks to train - All 13 major stocks
NSE_STOCKS = [
    'SCOM.NR',  # Safaricom - Most liquid
    'KCB.NR',   # KCB Group
    'EQTY.NR',  # Equity Group
    'EABL.NR',  # East African Breweries
    'COOP.NR',  # Co-operative Bank
    'ABSA.NR',  # ABSA Bank Kenya
    'SCBK.NR',  # Standard Chartered Bank
    'BAMB.NR',  # Bamburi Cement
    'BAT.NR',   # British American Tobacco
    'DTBK.NR',  # Diamond Trust Bank
    'NCBA.NR',  # NCBA Group
    'NMG.NR',   # Nation Media Group
    'SBIC.NR',  # Stanbic Holdings
]

print("=" * 70)
print("  NSE Stock Price LSTM Trainer")
print("=" * 70)
print(f"  TensorFlow: {tf.__version__}")
print(f"  Models dir: {MODEL_DIR}")
print(f"  Sequence length: {SEQUENCE_LENGTH} days")
print(f"  Stocks to train: {', '.join(NSE_STOCKS)}")
print("=" * 70)


# ==================== DATA COLLECTION ====================

def collect_nse_data(symbol: str, days_back: int = 365) -> pd.DataFrame:
    """Collect NSE stock data from database"""
    logger.info(f"Loading data for {symbol}...")
    
    with Session(sync_engine) as session:
        # Get symbol record
        stock_symbol = session.exec(
            select(StockSymbol).where(StockSymbol.symbol == symbol)
        ).first()
        
        if not stock_symbol:
            logger.error(f"Symbol {symbol} not found in database")
            return None
        
        # Get stock data
        stock_data = session.exec(
            select(StockData)
            .where(StockData.symbol_id == stock_symbol.id)
            .order_by(StockData.date)
        ).all()
        
        if not stock_data:
            logger.warning(f"No data found for {symbol}. Attempting to collect...")
            
            # Try to collect data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            records_inserted = collect_stock_data(
                session,
                symbol,
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            if records_inserted == 0:
                logger.error(f"Failed to collect data for {symbol}")
                return None
            
            # Reload data
            stock_data = session.exec(
                select(StockData)
                .where(StockData.symbol_id == stock_symbol.id)
                .order_by(StockData.date)
            ).all()
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': d.date,
            'open': float(d.open),
            'high': float(d.high),
            'low': float(d.low),
            'close': float(d.close),
            'volume': int(d.volume),
            'adj_close': float(d.adj_close) if d.adj_close else float(d.close)
        } for d in stock_data])
        
        df = df.sort_values('date').reset_index(drop=True)
        logger.info(f"Loaded {len(df)} records for {symbol} from {df['date'].min()} to {df['date'].max()}")
        
        return df


# ==================== FEATURE ENGINEERING ====================

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create technical indicators as features"""
    df = df.copy()
    
    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    
    # Moving averages
    df['ma_7'] = df['close'].rolling(window=7).mean()
    df['ma_21'] = df['close'].rolling(window=21).mean()
    df['ma_50'] = df['close'].rolling(window=50).mean()
    
    # Volatility
    df['volatility_7'] = df['returns'].rolling(window=7).std()
    df['volatility_21'] = df['returns'].rolling(window=21).std()
    
    # Price momentum
    df['momentum_7'] = df['close'] - df['close'].shift(7)
    df['momentum_21'] = df['close'] - df['close'].shift(21)
    
    # Volume features
    df['volume_ma_7'] = df['volume'].rolling(window=7).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma_7']
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Drop NaN values
    df = df.dropna().reset_index(drop=True)
    
    return df


# ==================== SEQUENCE PREPARATION ====================

def create_sequences(data: np.ndarray, sequence_length: int):
    """Create sequences for LSTM training"""
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i+sequence_length])
        y.append(data[i+sequence_length, 0])  # Predict close price
    return np.array(X), np.array(y)


# ==================== MODEL ARCHITECTURE ====================

def build_lstm_model(sequence_length: int, n_features: int) -> models.Model:
    """Build LSTM model for stock price prediction"""
    model = models.Sequential([
        # First LSTM layer
        layers.LSTM(128, return_sequences=True, input_shape=(sequence_length, n_features)),
        layers.Dropout(0.2),
        layers.BatchNormalization(),
        
        # Second LSTM layer
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),
        layers.BatchNormalization(),
        
        # Third LSTM layer
        layers.LSTM(32, return_sequences=False),
        layers.Dropout(0.2),
        layers.BatchNormalization(),
        
        # Dense layers
        layers.Dense(16, activation='relu'),
        layers.Dropout(0.1),
        
        # Output layer
        layers.Dense(1)
    ], name='nse_lstm_price_predictor')
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='mse',
        metrics=['mae', 'mape']
    )
    
    return model


# ==================== TRAINING PIPELINE ====================

def train_model_for_symbol(symbol: str, df: pd.DataFrame):
    """Train LSTM model for a specific NSE stock"""
    
    print(f"\n{'='*70}")
    print(f"Training model for {symbol}")
    print(f"{'='*70}")
    
    # Check minimum data requirement
    min_required = SEQUENCE_LENGTH + 100
    if len(df) < min_required:
        logger.warning(f"Insufficient data for {symbol}: {len(df)} records (need {min_required})")
        return None
    
    # Create features
    df = create_features(df)
    print(f"Created features. Data shape: {df.shape}")
    
    # Select features for training
    feature_columns = [
        'close', 'open', 'high', 'low', 'volume',
        'returns', 'ma_7', 'ma_21', 'ma_50',
        'volatility_7', 'volatility_21',
        'momentum_7', 'momentum_21',
        'volume_ratio', 'rsi'
    ]
    
    data = df[feature_columns].values
    n_features = len(feature_columns)
    
    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)
    
    # Create sequences
    X, y = create_sequences(data_scaled, SEQUENCE_LENGTH)
    print(f"Created sequences. X shape: {X.shape}, y shape: {y.shape}")
    
    # Split data
    train_size = int(len(X) * (1 - TEST_SIZE - VAL_SIZE))
    val_size = int(len(X) * VAL_SIZE)
    
    X_train = X[:train_size]
    y_train = y[:train_size]
    
    X_val = X[train_size:train_size+val_size]
    y_val = y[train_size:train_size+val_size]
    
    X_test = X[train_size+val_size:]
    y_test = y[train_size+val_size:]
    
    print(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    
    # Build model
    model = build_lstm_model(SEQUENCE_LENGTH, n_features)
    model.summary()
    
    # Define callbacks
    base_symbol = symbol.replace('.NR', '')
    model_path = str(MODEL_DIR / f"{base_symbol}_lstm.keras")
    scaler_path = str(MODEL_DIR / f"{base_symbol}_scaler.joblib")
    
    callbacks = [
        ModelCheckpoint(
            model_path,
            monitor='val_loss',
            save_best_only=True,
            mode='min',
            verbose=1
        ),
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        )
    ]
    
    # Train model
    print(f"\n🚀 Training LSTM model for {symbol}...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate on test set
    test_loss, test_mae, test_mape = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n{'='*70}")
    print(f"Test Results for {symbol}")
    print(f"{'='*70}")
    print(f"Test Loss (MSE): {test_loss:.6f}")
    print(f"Test MAE: {test_mae:.6f}")
    print(f"Test MAPE: {test_mape:.2f}%")
    
    # Make predictions
    y_pred = model.predict(X_test, verbose=0)
    
    # Inverse transform predictions (scale back to original values)
    # Create dummy array with same shape as original features
    dummy = np.zeros((len(y_test), n_features))
    dummy[:, 0] = y_test  # Close price is first feature
    y_test_original = scaler.inverse_transform(dummy)[:, 0]
    
    dummy[:, 0] = y_pred.flatten()
    y_pred_original = scaler.inverse_transform(dummy)[:, 0]
    
    # Calculate metrics on original scale
    mae = mean_absolute_error(y_test_original, y_pred_original)
    rmse = np.sqrt(mean_squared_error(y_test_original, y_pred_original))
    r2 = r2_score(y_test_original, y_pred_original)
    mape = np.mean(np.abs((y_test_original - y_pred_original) / y_test_original)) * 100
    
    print(f"\nMetrics on Original Scale:")
    print(f"MAE: KES {mae:.2f}")
    print(f"RMSE: KES {rmse:.2f}")
    print(f"R² Score: {r2:.4f}")
    print(f"MAPE: {mape:.2f}%")
    
    # Save scaler
    joblib.dump(scaler, scaler_path)
    print(f"\n✅ Model saved: {model_path}")
    print(f"✅ Scaler saved: {scaler_path}")
    
    # Save metadata
    metadata = {
        'symbol': symbol,
        'base_symbol': base_symbol,
        'model_type': 'LSTM',
        'sequence_length': SEQUENCE_LENGTH,
        'n_features': n_features,
        'feature_columns': feature_columns,
        'training_samples': len(X_train),
        'validation_samples': len(X_val),
        'test_samples': len(X_test),
        'epochs_trained': len(history.history['loss']),
        'batch_size': BATCH_SIZE,
        'learning_rate': LEARNING_RATE,
        'best_val_loss': float(min(history.history['val_loss'])),
        'test_loss': float(test_loss),
        'test_mae': float(test_mae),
        'test_mape': float(test_mape),
        'mae_kes': float(mae),
        'rmse_kes': float(rmse),
        'r2_score': float(r2),
        'mape_percent': float(mape),
        'training_date': datetime.now().isoformat(),
        'data_range': {
            'start': df['date'].min().isoformat(),
            'end': df['date'].max().isoformat(),
            'total_records': len(df)
        }
    }
    
    meta_path = str(MODEL_DIR / f"{base_symbol}_lstm_meta.json")
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved: {meta_path}")
    
    return metadata


# ==================== MAIN EXECUTION ====================

def main():
    """Main training pipeline"""
    print("\n🚀 Starting NSE LSTM Training Pipeline\n")
    
    results = {}
    
    for symbol in NSE_STOCKS:
        try:
            # Collect data
            df = collect_nse_data(symbol, days_back=730)  # 2 years of data
            
            if df is None or len(df) < SEQUENCE_LENGTH + 100:
                logger.error(f"Skipping {symbol} due to insufficient data")
                results[symbol] = {'status': 'failed', 'reason': 'insufficient_data'}
                continue
            
            # Train model
            metadata = train_model_for_symbol(symbol, df)
            
            if metadata:
                results[symbol] = {'status': 'success', 'metadata': metadata}
            else:
                results[symbol] = {'status': 'failed', 'reason': 'training_failed'}
                
        except Exception as e:
            logger.error(f"Error training model for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            results[symbol] = {'status': 'failed', 'reason': str(e)}
    
    # Print summary
    print("\n" + "="*70)
    print("TRAINING SUMMARY")
    print("="*70)
    
    for symbol, result in results.items():
        status = result['status']
        if status == 'success':
            meta = result['metadata']
            print(f"\n✅ {symbol}: SUCCESS")
            print(f"   MAE: KES {meta['mae_kes']:.2f}")
            print(f"   RMSE: KES {meta['rmse_kes']:.2f}")
            print(f"   R² Score: {meta['r2_score']:.4f}")
            print(f"   MAPE: {meta['mape_percent']:.2f}%")
        else:
            reason = result.get('reason', 'unknown')
            print(f"\n❌ {symbol}: FAILED ({reason})")
    
    print("\n" + "="*70)
    print(f"Models saved in: {MODEL_DIR}")
    print("="*70)
    
    # Save overall summary
    summary_path = str(MODEL_DIR / "training_summary.json")
    with open(summary_path, 'w') as f:
        json.dump({
            'training_date': datetime.now().isoformat(),
            'stocks_trained': NSE_STOCKS,
            'results': results
        }, f, indent=2)
    print(f"✅ Summary saved: {summary_path}\n")


if __name__ == "__main__":
    main()
