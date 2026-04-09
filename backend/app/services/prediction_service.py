from __future__ import annotations
from datetime import date
from typing import Optional
from sqlmodel import Session, select

from app.models.prediction import Prediction
from app.models.stock import StockSymbol
from app.tools.prediction_tools import (
    engineer_features, create_sequences, build_lstm_model,
    save_model_artifacts, load_model_artifacts, predict_price, FEATURE_COLS
)
from app.utils.logger import logger


def train_model(session: Session, symbol: str) -> dict:
    """Train LSTM model for a symbol. Returns {mse, mae}."""
    import numpy as np
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error

    logger.info(f"Training model for {symbol}")
    end_date = date.today().isoformat()
    df = engineer_features(session, symbol, end_date, window=500)

    if df.empty or len(df) < 80:
        raise ValueError(f"Insufficient data for {symbol}: need at least 80 rows, got {len(df)}")

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df.values)

    import pandas as pd
    scaled_df = pd.DataFrame(scaled, columns=FEATURE_COLS)
    X, y = create_sequences(scaled_df, seq_len=60)

    if len(X) < 10:
        raise ValueError(f"Not enough sequences for {symbol}")

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = build_lstm_model((60, len(FEATURE_COLS)))
    model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)

    y_pred = model.predict(X_test, verbose=0).flatten()
    mse = float(mean_squared_error(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))

    save_model_artifacts(symbol, model, scaler)
    logger.info(f"Model trained for {symbol}: MSE={mse:.6f} MAE={mae:.6f}")
    return {"mse": mse, "mae": mae}


def generate_prediction(
    session: Session,
    symbol: str,
    horizon_days: int,
    user_id: Optional[int] = None,
) -> list[Prediction]:
    """Generate predictions and store them in the DB."""
    stock_symbol = session.exec(select(StockSymbol).where(StockSymbol.symbol == symbol)).first()
    if not stock_symbol:
        raise ValueError(f"Symbol {symbol} not found")

    raw_preds = predict_price(symbol, horizon_days, session)
    if not raw_preds:
        return []

    stored = []
    for p in raw_preds:
        pred = Prediction(
            symbol_id=stock_symbol.id,
            user_id=user_id,
            predicted_price=p["predicted_price"],
            confidence_score=p["confidence"],
            trend_direction=p["trend"],
            model_source=p["model_source"],
            prediction_date=date.today(),
            target_date=date.fromisoformat(p["date"]),
        )
        session.add(pred)
        stored.append(pred)

    session.commit()
    for p in stored:
        session.refresh(p)
    return stored
