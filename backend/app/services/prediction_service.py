"""
NSE Stock Price Prediction Service
Loads trained LSTM models and generates predictions
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select
import joblib

try:
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("Warning: TensorFlow not available. Prediction service will be limited.")

from app.models.stock import StockSymbol, StockData
from app.models.prediction import Prediction
from app.utils.logger import logger


class PredictionService:
    """Service for loading LSTM models and making predictions"""
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path(__file__).parent.parent / "models" / "trained"
        self.loaded_models: Dict[str, Dict] = {}
        
    def _get_base_symbol(self, symbol: str) -> str:
        """Extract base symbol (remove .NR suffix)"""
        return symbol.replace('.NR', '').upper()
    
    def _load_model(self, symbol: str) -> bool:
        """Load model, scaler, and metadata for a symbol"""
        base_symbol = self._get_base_symbol(symbol)
        
        # Check if already loaded
        if base_symbol in self.loaded_models:
            return True
        
        if not TF_AVAILABLE:
            logger.error("TensorFlow not available - cannot load models")
            return False
        
        try:
            model_path = self.models_dir / f"{base_symbol}_lstm.keras"
            scaler_path = self.models_dir / f"{base_symbol}_scaler.joblib"
            meta_path = self.models_dir / f"{base_symbol}_lstm_meta.json"
            
            # Check if files exist
            if not model_path.exists():
                logger.warning(f"Model not found for {symbol}: {model_path}")
                return False
            
            # Load model
            model = load_model(str(model_path))
            
            # Load scaler
            scaler = joblib.load(str(scaler_path))
            
            # Load metadata
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            self.loaded_models[base_symbol] = {
                'model': model,
                'scaler': scaler,
                'metadata': metadata,
                'symbol': symbol
            }
            
            logger.info(f"Loaded model for {symbol}: {metadata['epochs_trained']} epochs, "
                       f"MAPE: {metadata['mape_percent']:.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model for {symbol}: {e}")
            return False
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
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
    
    def _get_stock_data(self, session: Session, symbol: str, days: int = 120) -> Optional[pd.DataFrame]:
        """Fetch stock data from database"""
        # Get symbol record
        stock_symbol = session.exec(
            select(StockSymbol).where(StockSymbol.symbol == symbol)
        ).first()
        
        if not stock_symbol:
            logger.error(f"Symbol {symbol} not found in database")
            return None
        
        # Get latest stock data
        stock_data = session.exec(
            select(StockData)
            .where(StockData.symbol_id == stock_symbol.id)
            .order_by(StockData.date.desc())
            .limit(days)
        ).all()
        
        if not stock_data or len(stock_data) < 60:
            logger.error(f"Insufficient data for {symbol}: {len(stock_data) if stock_data else 0} records")
            return None
        
        # Convert to DataFrame and sort by date ascending
        df = pd.DataFrame([{
            'date': d.date,
            'open': float(d.open),
            'high': float(d.high),
            'low': float(d.low),
            'close': float(d.close),
            'volume': int(d.volume)
        } for d in stock_data])
        
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def predict_next_day(self, session: Session, symbol: str, user_id: Optional[int] = None) -> Optional[Dict]:
        """
        Predict next day's closing price for a stock
        
        Args:
            session: Database session
            symbol: Stock symbol (e.g., 'SCOM.NR')
            user_id: User ID for tracking predictions
            
        Returns:
            Dictionary with prediction details or None if failed
        """
        # Ensure .NR suffix
        if not symbol.endswith('.NR'):
            symbol = f"{symbol}.NR"
        
        # Load model if not loaded
        if not self._load_model(symbol):
            return None
        
        base_symbol = self._get_base_symbol(symbol)
        model_data = self.loaded_models[base_symbol]
        
        # Get stock data
        df = self._get_stock_data(session, symbol, days=120)
        if df is None:
            return None
        
        # Create features
        df = self._create_features(df)
        
        if len(df) < 60:
            logger.error(f"Insufficient data after feature engineering for {symbol}: {len(df)} rows")
            return None
        
        # Get latest 60 days for prediction
        latest_data = df.tail(60)
        
        # Select features in correct order
        feature_columns = model_data['metadata']['feature_columns']
        X = latest_data[feature_columns].values
        
        # Scale data
        scaler = model_data['scaler']
        X_scaled = scaler.transform(X)
        
        # Reshape for LSTM input: (1, 60, n_features)
        X_input = X_scaled.reshape(1, 60, len(feature_columns))
        
        # Make prediction
        model = model_data['model']
        pred_scaled = model.predict(X_input, verbose=0)
        
        # Inverse transform to get actual price
        # Create dummy array with same shape as training features
        dummy = np.zeros((1, len(feature_columns)))
        dummy[:, 0] = pred_scaled[0, 0]  # Close price is first feature
        predicted_price = scaler.inverse_transform(dummy)[0, 0]
        
        # Get current price and calculate change
        current_price = float(latest_data['close'].iloc[-1])
        price_change = predicted_price - current_price
        price_change_pct = (price_change / current_price) * 100
        
        # Determine trend direction
        if price_change_pct > 1:
            trend = 'up'
        elif price_change_pct < -1:
            trend = 'down'
        else:
            trend = 'neutral'
        
        # Calculate confidence based on model performance
        mape = model_data['metadata'].get('mape_percent', 10.0)
        confidence = max(0.0, min(1.0, (100 - mape) / 100))
        
        # Get dates
        last_date = latest_data['date'].iloc[-1]
        prediction_date = datetime.now().date()
        target_date = last_date + timedelta(days=1)
        
        # Skip weekends
        while target_date.weekday() >= 5:  # Saturday=5, Sunday=6
            target_date += timedelta(days=1)
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'trend_direction': trend,
            'confidence_score': confidence,
            'prediction_date': prediction_date,
            'target_date': target_date,
            'last_data_date': last_date,
            'model_source': 'local',
            'model_mape': mape
        }
        
        # Save prediction to database
        try:
            # Get stock symbol ID
            stock_symbol = session.exec(
                select(StockSymbol).where(StockSymbol.symbol == symbol)
            ).first()
            
            prediction = Prediction(
                symbol_id=stock_symbol.id,
                user_id=user_id,
                predicted_price=predicted_price,
                confidence_score=confidence,
                trend_direction=trend,
                model_source='local',
                prediction_date=prediction_date,
                target_date=target_date
            )
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            
            result['prediction_id'] = prediction.id
            logger.info(f"Saved prediction for {symbol}: KES {predicted_price:.2f} ({trend})")
            
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            session.rollback()
        
        return result
    
    def predict_multiple_days(
        self, 
        session: Session, 
        symbol: str, 
        days: int = 7,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Predict multiple days ahead (experimental)
        Note: Predictions become less accurate further into the future
        
        Args:
            session: Database session
            symbol: Stock symbol
            days: Number of days to predict
            user_id: User ID
            
        Returns:
            List of prediction dictionaries
        """
        predictions = []
        
        # Get first prediction
        pred = self.predict_next_day(session, symbol, user_id)
        if not pred:
            return predictions
        
        predictions.append(pred)
        
        # For multiple days, we would need to:
        # 1. Add predicted price to historical data
        # 2. Recalculate features
        # 3. Make next prediction
        # This is experimental and accuracy degrades quickly
        
        logger.warning(f"Multi-day prediction for {symbol} limited to 1 day")
        
        return predictions
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available trained models"""
        available = []
        
        if not self.models_dir.exists():
            return available
        
        for meta_file in self.models_dir.glob("*_lstm_meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                available.append({
                    'symbol': metadata['symbol'],
                    'base_symbol': metadata['base_symbol'],
                    'mape': metadata['mape_percent'],
                    'mae_kes': metadata['mae_kes'],
                    'training_date': metadata['training_date'],
                    'epochs': metadata['epochs_trained']
                })
            except Exception as e:
                logger.error(f"Failed to read metadata from {meta_file}: {e}")
        
        return sorted(available, key=lambda x: x['mape'])
    
    def update_prediction_accuracy(self, session: Session, prediction_id: int):
        """
        Update prediction with actual price after target date
        Calculate accuracy metrics
        """
        prediction = session.get(Prediction, prediction_id)
        if not prediction:
            return
        
        # Check if target date has passed
        if prediction.target_date > datetime.now().date():
            return
        
        # Get actual price on target date
        stock_data = session.exec(
            select(StockData)
            .where(StockData.symbol_id == prediction.symbol_id)
            .where(StockData.date == prediction.target_date)
        ).first()
        
        if stock_data:
            prediction.actual_price = float(stock_data.close)
            session.commit()
            logger.info(f"Updated prediction {prediction_id} with actual price: {stock_data.close}")


# Global instance
_prediction_service = None

def get_prediction_service() -> PredictionService:
    """Get or create prediction service singleton"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
