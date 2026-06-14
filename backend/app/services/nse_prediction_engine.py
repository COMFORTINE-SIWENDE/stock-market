"""NSE prediction engine with LSTM model."""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    from tensorflow import keras
    from sklearn.preprocessing import MinMaxScaler
    import joblib
except ImportError:
    keras = None
    MinMaxScaler = None
    joblib = None

from sqlmodel import Session
from app.services.nse_feature_engineer import NSEFeatureEngineer


logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Result of model training."""
    symbol: str
    mae: float
    avg_price: float
    days_trained: int
    model_path: str
    scaler_path: str


@dataclass
class Prediction:
    """Stock price prediction."""
    symbol: str
    target_date: date
    predicted_price: float
    currency: str
    horizon_days: int


class InsufficientDataError(Exception):
    """Raised when insufficient data for training."""
    pass


class NSEPredictionEngine:
    """Prediction engine for NSE stocks using LSTM."""
    
    def __init__(self, model_dir: Path):
        """
        Initialize prediction engine.
        
        Args:
            model_dir: Directory to save/load models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        if keras is None or MinMaxScaler is None:
            logger.warning("TensorFlow/scikit-learn not installed. Prediction engine disabled.")
    
    def train_model(
        self,
        symbol: str,
        symbol_id: int,
        session: Session,
        min_days: int = 365
    ) -> TrainingResult:
        """
        Train LSTM model for NSE stock.
        
        Args:
            symbol: Stock symbol
            symbol_id: Stock symbol ID
            session: Database session
            min_days: Minimum days of data required
        
        Returns:
            TrainingResult with metrics
        
        Raises:
            InsufficientDataError: If insufficient data
        """
        if keras is None or MinMaxScaler is None:
            raise RuntimeError("TensorFlow/scikit-learn not installed")
        
        logger.info(f"Training model for {symbol}")
        
        # Engineer features
        df = NSEFeatureEngineer.engineer_features(symbol, symbol_id, session)
        
        if len(df) < min_days:
            raise InsufficientDataError(
                f"Insufficient data for {symbol}: {len(df)} days available, {min_days} required"
            )
        
        # Prepare data
        features = ['open', 'high', 'low', 'close', 'volume', 'sma_5', 'sma_20', 'volatility_20', 'sentiment']
        data = df[features].values
        
        # Scale data
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data)
        
        # Create sequences (60 days lookback)
        lookback = 60
        X, y = [], []
        
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i])
            y.append(scaled_data[i, 3])  # Predict close price
        
        X, y = np.array(X), np.array(y)
        
        # Split train/test
        split = int(0.8 * len(X))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Build LSTM model
        model = keras.Sequential([
            keras.layers.LSTM(50, return_sequences=True, input_shape=(lookback, len(features))),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(50, return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(25),
            keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        # Train
        model.fit(X_train, y_train, batch_size=32, epochs=10, validation_split=0.1, verbose=0)
        
        # Evaluate
        predictions = model.predict(X_test, verbose=0)
        
        # Inverse transform to get actual prices
        dummy = np.zeros((len(predictions), len(features)))
        dummy[:, 3] = predictions.flatten()
        predictions_unscaled = scaler.inverse_transform(dummy)[:, 3]
        
        dummy_y = np.zeros((len(y_test), len(features)))
        dummy_y[:, 3] = y_test
        y_test_unscaled = scaler.inverse_transform(dummy_y)[:, 3]
        
        # Calculate MAE
        mae = np.mean(np.abs(predictions_unscaled - y_test_unscaled))
        avg_price = np.mean(df['close'])
        
        # Save model and scaler
        base_symbol = symbol.replace('.NR', '')
        model_path = self.model_dir / f"{base_symbol}_lstm.keras"
        scaler_path = self.model_dir / f"{base_symbol}_scaler.joblib"
        
        model.save(model_path)
        joblib.dump(scaler, scaler_path)
        
        logger.info(f"Model trained for {symbol}: MAE={mae:.2f}, Avg Price={avg_price:.2f}")
        
        return TrainingResult(
            symbol=symbol,
            mae=mae,
            avg_price=avg_price,
            days_trained=len(df),
            model_path=str(model_path),
            scaler_path=str(scaler_path)
        )
    
    def predict(
        self,
        symbol: str,
        symbol_id: int,
        session: Session,
        horizons: List[int] = [1, 5, 30]
    ) -> List[Prediction]:
        """
        Generate predictions for NSE stock.
        
        Args:
            symbol: Stock symbol
            symbol_id: Stock symbol ID
            session: Database session
            horizons: Days ahead to predict
        
        Returns:
            List of Prediction objects
        """
        if keras is None or joblib is None:
            raise RuntimeError("TensorFlow/scikit-learn not installed")
        
        base_symbol = symbol.replace('.NR', '')
        model_path = self.model_dir / f"{base_symbol}_lstm.keras"
        scaler_path = self.model_dir / f"{base_symbol}_scaler.joblib"
        
        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(f"Model not found for {symbol}. Train first.")
        
        # Load model and scaler
        model = keras.models.load_model(model_path)
        scaler = joblib.load(scaler_path)
        
        # Engineer features
        df = NSEFeatureEngineer.engineer_features(symbol, symbol_id, session)
        
        if len(df) < 60:
            raise InsufficientDataError(f"Need at least 60 days of data for prediction")
        
        # Get last 60 days
        features = ['open', 'high', 'low', 'close', 'volume', 'sma_5', 'sma_20', 'volatility_20', 'sentiment']
        last_60 = df[features].tail(60).values
        
        # Scale
        scaled = scaler.transform(last_60)
        
        # Predict
        predictions = []
        last_date = df.index[-1].date()
        
        for horizon in horizons:
            # Predict next day iteratively
            current_sequence = scaled.copy()
            
            for _ in range(horizon):
                X = current_sequence[-60:].reshape(1, 60, len(features))
                pred = model.predict(X, verbose=0)[0, 0]
                
                # Create next day's features (simplified)
                next_row = current_sequence[-1].copy()
                next_row[3] = pred  # Update close price
                current_sequence = np.vstack([current_sequence, next_row])
            
            # Get final prediction
            final_pred = current_sequence[-1, 3]
            
            # Inverse transform
            dummy = np.zeros((1, len(features)))
            dummy[0, 3] = final_pred
            price = scaler.inverse_transform(dummy)[0, 3]
            
            target_date = last_date + timedelta(days=horizon)
            
            predictions.append(Prediction(
                symbol=symbol,
                target_date=target_date,
                predicted_price=float(price),
                currency='KES',
                horizon_days=horizon
            ))
        
        logger.info(f"Generated {len(predictions)} predictions for {symbol}")
        return predictions
