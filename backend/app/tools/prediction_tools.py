from __future__ import annotations
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sqlmodel import Session, select

from app.models.stock import StockData, StockSymbol
from app.models.sentiment import DailySentiment
from app.models.prediction import Prediction
from app.utils.logger import logger

MODELS_DIR = Path(__file__).parent.parent / "models" / "trained"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = ["open", "high", "low", "close", "volume", "sentiment_score", "sma_5", "sma_20", "volatility"]


def engineer_features(session: Session, symbol: str, end_date: str, window: int = 60) -> pd.DataFrame:
    """Build a DataFrame with 9 features for the last `window` days up to end_date."""
    stock_symbol = session.exec(select(StockSymbol).where(StockSymbol.symbol == symbol)).first()
    if not stock_symbol:
        return pd.DataFrame()

    end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    start = end - timedelta(days=window * 2)  # fetch extra for rolling calcs

    stock_rows = session.exec(
        select(StockData).where(
            StockData.symbol_id == stock_symbol.id,
            StockData.date >= start,
            StockData.date <= end,
        ).order_by(StockData.date)
    ).all()

    if not stock_rows:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "date": r.date,
        "open": r.open, "high": r.high, "low": r.low,
        "close": r.close, "volume": r.volume,
    } for r in stock_rows])
    df.set_index("date", inplace=True)

    # Sentiment scores
    sentiment_rows = session.exec(
        select(DailySentiment).where(
            DailySentiment.symbol_id == stock_symbol.id,
            DailySentiment.date >= start,
            DailySentiment.date <= end,
        )
    ).all()
    sentiment_map = {r.date: r.avg_sentiment_score for r in sentiment_rows}
    df["sentiment_score"] = df.index.map(lambda d: sentiment_map.get(d, 0.0))

    # Technical features
    df["returns"] = df["close"].pct_change()
    df["sma_5"] = df["close"].rolling(5).mean()
    df["sma_20"] = df["close"].rolling(20).mean()
    df["volatility"] = df["returns"].rolling(20).std()

    df.ffill(inplace=True)
    df.fillna(0.0, inplace=True)

    return df[FEATURE_COLS].tail(window)


def create_sequences(df: pd.DataFrame, seq_len: int = 60) -> tuple[np.ndarray, np.ndarray]:
    """Build (X, y) arrays: X shape (n, seq_len, 9), y shape (n,)."""
    data = df.values
    X, y = [], []
    close_idx = FEATURE_COLS.index("close")
    for i in range(seq_len, len(data)):
        X.append(data[i - seq_len:i])
        y.append(data[i][close_idx])
    return np.array(X), np.array(y)


def build_lstm_model(input_shape: tuple):
    """Build LSTM(50) → Dropout → LSTM(50) → Dense(25) → Dense(1)."""
    import tensorflow as tf
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(50, return_sequences=True, input_shape=input_shape),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(50, return_sequences=False),
        tf.keras.layers.Dense(25, activation="relu"),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss="mse")
    return model


def save_model_artifacts(symbol: str, model, scaler) -> None:
    """Save .keras model and joblib scaler to app/models/trained/."""
    model.save(str(MODELS_DIR / f"{symbol}_lstm.keras"))
    joblib.dump(scaler, str(MODELS_DIR / f"{symbol}_scaler.joblib"))
    logger.info(f"Saved model artifacts for {symbol}")


def load_model_artifacts(symbol: str):
    """Load model and scaler from disk. Returns (model, scaler) or None."""
    import tensorflow as tf
    model_path = MODELS_DIR / f"{symbol}_lstm.keras"
    scaler_path = MODELS_DIR / f"{symbol}_scaler.joblib"
    if not model_path.exists() or not scaler_path.exists():
        return None
    try:
        model = tf.keras.models.load_model(str(model_path))
        scaler = joblib.load(str(scaler_path))
        return model, scaler
    except Exception as e:
        logger.error(f"Failed to load model artifacts for {symbol}: {e}")
        return None


def calculate_confidence(session: Session, symbol: str, scaler=None) -> float:
    """Estimate confidence [0,1] based on recent prediction accuracy + volatility."""
    stock_symbol = session.exec(select(StockSymbol).where(StockSymbol.symbol == symbol)).first()
    if not stock_symbol:
        return 0.5

    recent_preds = session.exec(
        select(Prediction).where(
            Prediction.symbol_id == stock_symbol.id,
            Prediction.actual_price.is_not(None),
        ).order_by(Prediction.prediction_date.desc()).limit(10)
    ).all()

    if recent_preds:
        errors = [abs(p.predicted_price - p.actual_price) / p.actual_price for p in recent_preds if p.actual_price]
        mae_pct = sum(errors) / len(errors) if errors else 0.1
        accuracy_score = max(0.0, 1.0 - mae_pct * 5)
    else:
        accuracy_score = 0.5

    return round(min(1.0, max(0.0, accuracy_score)), 4)


def predict_price(symbol: str, horizon_days: int, session: Session) -> list[dict]:
    """Generate price predictions for horizon_days. Returns list of {date, predicted_price, confidence, trend}."""
    from sklearn.preprocessing import MinMaxScaler
    from app.services import prediction_service  # lazy import to avoid circular

    artifacts = load_model_artifacts(symbol)
    model_source = "local"

    if artifacts is None:
        # Try Azure ML
        from app.services.azure_ml_client import AzureMLClient
        azure_client = AzureMLClient()
        if azure_client.is_configured():
            model_source = "azure"
            # Use Azure for single-day prediction
            end_date = date.today().isoformat()
            df = engineer_features(session, symbol, end_date)
            if df.empty:
                return []
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(df.values)
            features_dict = {col: float(scaled[-1][i]) for i, col in enumerate(FEATURE_COLS)}
            try:
                predicted = azure_client.predict(features_dict)
                confidence = calculate_confidence(session, symbol)
                results = []
                prev_price = predicted
                for i in range(horizon_days):
                    target = date.today() + timedelta(days=i + 1)
                    trend = "up" if predicted >= prev_price else "down"
                    results.append({
                        "date": target.isoformat(),
                        "predicted_price": round(predicted, 4),
                        "confidence": confidence,
                        "trend": trend,
                        "model_source": model_source,
                    })
                    prev_price = predicted
                return results
            except Exception as e:
                logger.error(f"Azure ML prediction failed: {e}")
        # Fall back to on-demand training
        logger.info(f"No model for {symbol}, training on demand...")
        prediction_service.train_model(session, symbol)
        artifacts = load_model_artifacts(symbol)
        if artifacts is None:
            return []

    model, scaler = artifacts
    end_date = date.today().isoformat()
    df = engineer_features(session, symbol, end_date)
    if df.empty or len(df) < 60:
        logger.warning(f"Insufficient data for {symbol}: {len(df)} rows")
        return []

    scaled = scaler.transform(df.values)
    sequence = scaled[-60:].reshape(1, 60, len(FEATURE_COLS))
    close_idx = FEATURE_COLS.index("close")

    results = []
    current_seq = sequence.copy()
    prev_price = float(df["close"].iloc[-1])
    confidence = calculate_confidence(session, symbol, scaler)

    for i in range(horizon_days):
        pred_scaled = model.predict(current_seq, verbose=0)[0][0]
        # Inverse transform: reconstruct full row, replace close, inverse
        dummy = np.zeros((1, len(FEATURE_COLS)))
        dummy[0][close_idx] = pred_scaled
        predicted_price = float(scaler.inverse_transform(dummy)[0][close_idx])
        trend = "up" if predicted_price >= prev_price else "down"
        target_date = date.today() + timedelta(days=i + 1)
        results.append({
            "date": target_date.isoformat(),
            "predicted_price": round(predicted_price, 4),
            "confidence": confidence,
            "trend": trend,
            "model_source": model_source,
        })
        # Shift sequence: append new row
        new_row = current_seq[0][-1].copy()
        new_row[close_idx] = pred_scaled
        current_seq = np.append(current_seq[0][1:], [new_row], axis=0).reshape(1, 60, len(FEATURE_COLS))
        prev_price = predicted_price

    logger.info(f"Predicted {horizon_days} days for {symbol} confidence={confidence} source={model_source}")
    return results


def batch_predict(symbols: list[str], session: Session) -> dict:
    return {symbol: predict_price(symbol, 1, session) for symbol in symbols}


def get_prediction_history(symbol: str, session: Session) -> list[dict]:
    stock_symbol = session.exec(select(StockSymbol).where(StockSymbol.symbol == symbol)).first()
    if not stock_symbol:
        return []
    preds = session.exec(
        select(Prediction).where(Prediction.symbol_id == stock_symbol.id)
        .order_by(Prediction.prediction_date.desc())
    ).all()
    return [{
        "id": p.id,
        "prediction_date": str(p.prediction_date),
        "target_date": str(p.target_date),
        "predicted_price": p.predicted_price,
        "actual_price": p.actual_price,
        "confidence_score": p.confidence_score,
        "trend_direction": p.trend_direction,
        "model_source": p.model_source,
    } for p in preds]
