# Stock Sentiment Predictor — API Reference

This backend exposes its functionality through **Python function calls** (not HTTP endpoints), since it uses no web framework. The frontend (HTML/CSS/JS) must communicate with the backend via one of the patterns below.

---

## Integration Pattern for HTML/CSS Frontend

Since there is no HTTP server, the frontend has two options:

### Option A — Add a lightweight HTTP layer (recommended)
Add `aiohttp` or `http.server` to expose the functions below as JSON endpoints.
Run: `uv add aiohttp`

### Option B — Use the CLI via subprocess
The frontend can shell out to the CLI commands documented below.

---

## CLI Commands (subprocess-callable)

All commands run from the `backend/` directory with the virtualenv active.

```
python -m app.main <command> [options]
```

---

### `run`
Start the interactive GPT-Nano agent session.
```bash
python -m app.main run
```
Interactive — reads stdin, writes to stdout.

---

### `collect-data`
Collect historical stock prices and news articles.
```bash
python -m app.main collect-data --symbols AAPL MSFT --days 365
```
| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--symbols` / `-s` | string (multiple) | yes | — | Ticker symbols |
| `--days` | int | no | 365 | Days of history |

Output:
```
AAPL: 252 stock records, 18 news articles inserted
MSFT: 251 stock records, 12 news articles inserted
```

---

### `analyze-sentiment`
Analyze pending news articles and aggregate daily sentiment.
```bash
python -m app.main analyze-sentiment --symbol AAPL
```
| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--symbol` | string | yes | Ticker symbol |

Output:
```
Analyzed 5 new articles for AAPL
Daily sentiment (2026-04-01): score=0.142  articles=12  +7 =3 -2
```

---

### `predict`
Generate price predictions using the LSTM model.
```bash
python -m app.main predict --symbol AAPL --days 5
```
| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--symbol` | string | yes | — | Ticker symbol |
| `--days` | int | no | 1 | Forecast horizon |

Output:
```
Predictions for AAPL:
  2026-04-02  $213.45  trend=up  confidence=72%  [local]
  2026-04-03  $214.10  trend=up  confidence=72%  [local]
```

---

### `train-model`
Train a local LSTM model for a symbol.
```bash
python -m app.main train-model --symbol AAPL
```
| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--symbol` | string | yes | Ticker symbol |

Output:
```
Training model for AAPL...
Done. MSE=0.000412  MAE=0.014823
```

---

### `backtest`
Evaluate historical prediction accuracy.
```bash
python -m app.main backtest --symbol AAPL
```
Output:
```
Backtest results for AAPL (45 predictions):
  MAE:  $1.2340
  RMSE: $1.8920
```

---

## Python API (direct import)

If the frontend is served by a Python process, import and call these directly.

### Authentication

```python
from app.services.auth_service import register_user, login_user, verify_token, logout_user
from app.config.database import get_sync_session

# Register
with get_sync_session() as session:
    user = register_user(session, email="user@example.com", username="alice", password="secret")

# Login → returns (jwt_token, session_record)
with get_sync_session() as session:
    token, sess = login_user(session, username_or_email="alice", password="secret", ip="127.0.0.1")

# Verify token → returns User
with get_sync_session() as session:
    user = verify_token(session, token)

# Logout
with get_sync_session() as session:
    logout_user(session, token)
```

**Errors raised:**
- `ValueError("Email or username already registered")` — on duplicate registration
- `ValueError("Invalid credentials")` — on bad login
- `PermissionError("Session expired")` — on expired/invalid token

---

### Data Collection

```python
from app.services.data_service import collect_stock_data, collect_news

with get_sync_session() as session:
    # Returns: int (records inserted)
    count = collect_stock_data(session, symbol="AAPL", start_date="2025-01-01", end_date="2026-04-01")
    news_count = collect_news(session, symbol="AAPL", hours_back=24)
```

---

### Sentiment Analysis

```python
from app.services.sentiment_service import analyze_pending_articles, aggregate_daily_sentiment

with get_sync_session() as session:
    # Analyze all unprocessed articles for a symbol
    count = analyze_pending_articles(session, symbol="AAPL")

    # Aggregate into daily_sentiment table
    daily = aggregate_daily_sentiment(session, symbol="AAPL", date_str="2026-04-01")
    # daily.avg_sentiment_score  → float [-1, 1]
    # daily.article_count        → int
    # daily.positive_count       → int
    # daily.neutral_count        → int
    # daily.negative_count       → int
```

---

### Price Prediction

```python
from app.services.prediction_service import generate_prediction, train_model

with get_sync_session() as session:
    # Train model (returns {mse, mae})
    metrics = train_model(session, symbol="AAPL")

    # Generate predictions (returns list[Prediction])
    preds = generate_prediction(session, symbol="AAPL", horizon_days=5, user_id=None)
    for p in preds:
        print(p.target_date, p.predicted_price, p.confidence_score, p.trend_direction, p.model_source)
```

**Prediction fields:**
| Field | Type | Description |
|-------|------|-------------|
| `target_date` | date | Date being predicted |
| `predicted_price` | float | Predicted closing price |
| `confidence_score` | float [0–1] | Model confidence |
| `trend_direction` | str | `"up"` or `"down"` |
| `model_source` | str | `"local"` or `"azure"` |

---

### Agent (Natural Language)

```python
from app.agent.agent import Agent

agent = Agent()
with get_sync_session() as session:
    response = agent.run("What is the predicted price for AAPL next week?", session)
    print(response)
```

**Supported intents the agent recognises:**
| Intent | Example query |
|--------|--------------|
| `get_prediction` | "Predict AAPL for 3 days" |
| `analyze_sentiment` | "What's the sentiment on TSLA?" |
| `view_stock_data` | "Current price of MSFT?" |
| `compare_stocks` | "Compare AAPL and GOOGL" |
| `explain_trends` | "Why is NVDA trending up?" |
| `general_question` | Anything else |

---

### Tools (low-level)

```python
from app.tools.data_tools import fetch_historical_data, fetch_current_price, get_technical_indicators
from app.tools.sentiment_tools import preprocess_text, get_daily_sentiment, compare_sentiment
from app.tools.prediction_tools import engineer_features, predict_price, get_prediction_history
from app.tools.utility_tools import search_symbols, format_response, validate_input
```

#### `fetch_historical_data(symbol, start_date, end_date) → list[dict]`
Returns list of `{date, open, high, low, close, volume, adj_close}`.

#### `fetch_current_price(symbol) → float`
Returns latest closing price.

#### `get_technical_indicators(symbol, date_range) → dict`
Returns `{sma_5, sma_20, volatility}`.

#### `get_daily_sentiment(symbol, date_range, session) → list[dict]`
Returns list of `{date, avg_sentiment_score, article_count, positive_count, neutral_count, negative_count}`.

#### `search_symbols(query, session) → list[dict]`
Returns list of `{symbol, company_name, exchange}` matching the query.

---

## Data Models (JSON shapes for frontend)

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "alice",
  "full_name": "Alice Smith",
  "is_active": true,
  "created_at": "2026-04-01T10:00:00"
}
```

### StockData
```json
{
  "date": "2026-04-01",
  "open": 210.50,
  "high": 215.00,
  "low": 209.80,
  "close": 213.45,
  "volume": 52000000,
  "adj_close": 213.45
}
```

### SentimentResult
```json
{
  "date": "2026-04-01",
  "avg_sentiment_score": 0.142,
  "article_count": 12,
  "positive_count": 7,
  "neutral_count": 3,
  "negative_count": 2
}
```

### Prediction
```json
{
  "target_date": "2026-04-02",
  "predicted_price": 213.45,
  "confidence_score": 0.72,
  "trend_direction": "up",
  "model_source": "local"
}
```

---

## HTTP Server (aiohttp — `app/server.py`)

The HTTP server is implemented and ready. Start it with:

```bash
source .venv/bin/activate
python -m app.server
# Listening on http://0.0.0.0:8000
```

All responses are `application/json`. CORS is enabled for all origins (`*`).

---

## HTTP Endpoints

Base URL: `http://localhost:8000`

### Auth

#### `POST /auth/register`
```json
// Request
{ "email": "user@example.com", "username": "alice", "password": "secret", "full_name": "Alice" }

// Response 200
{ "id": 1, "username": "alice", "email": "user@example.com" }

// Error 400
{ "error": "Email or username already registered" }
```

#### `POST /auth/login`
```json
// Request
{ "username_or_email": "alice", "password": "secret" }

// Response 200
{ "token": "eyJ...", "session_id": 1, "expires_at": "2026-04-01 10:30:00" }

// Error 401
{ "error": "Invalid credentials" }
```

#### `POST /auth/logout`
```
Authorization: Bearer <token>
```
```json
// Response 200
{ "message": "Logged out" }
```

---

### Stocks

#### `GET /stocks/{symbol}/data?start=YYYY-MM-DD&end=YYYY-MM-DD`
```json
// Response 200
{
  "symbol": "AAPL",
  "data": [
    { "date": "2026-03-31", "open": 210.5, "high": 215.0, "low": 209.8, "close": 213.45, "volume": 52000000, "adj_close": 213.45 }
  ]
}
```

#### `GET /stocks/{symbol}/price`
```json
{ "symbol": "AAPL", "price": 213.45 }
```

#### `GET /stocks/{symbol}/indicators?start=YYYY-MM-DD&end=YYYY-MM-DD`
```json
{ "symbol": "AAPL", "indicators": { "sma_5": 212.1, "sma_20": 209.8, "volatility": 0.0142 } }
```

#### `POST /stocks/collect`
```json
// Request
{ "symbols": ["AAPL", "MSFT"], "days": 365 }

// Response 200
{ "AAPL": { "stock_records": 252, "news_articles": 18 }, "MSFT": { "stock_records": 251, "news_articles": 12 } }
```

---

### Sentiment

#### `GET /sentiment/{symbol}?start=YYYY-MM-DD&end=YYYY-MM-DD`
```json
{
  "symbol": "AAPL",
  "sentiment": [
    {
      "date": "2026-04-01",
      "avg_sentiment_score": 0.142,
      "article_count": 12,
      "positive_count": 7,
      "neutral_count": 3,
      "negative_count": 2
    }
  ]
}
```

#### `POST /sentiment/{symbol}/analyze`
```json
{
  "articles_analyzed": 5,
  "daily_sentiment": {
    "date": "2026-04-01",
    "avg_sentiment_score": 0.142,
    "article_count": 12,
    "positive_count": 7,
    "neutral_count": 3,
    "negative_count": 2
  }
}
```

---

### Predictions

#### `GET /predictions/{symbol}?days=N`
```json
{
  "symbol": "AAPL",
  "predictions": [
    { "target_date": "2026-04-02", "predicted_price": 213.45, "confidence_score": 0.72, "trend_direction": "up", "model_source": "local" }
  ]
}
```

#### `POST /predictions/{symbol}/train`
```json
{ "symbol": "AAPL", "mse": 0.000412, "mae": 0.014823 }
```

#### `GET /predictions/{symbol}/history`
```json
{
  "symbol": "AAPL",
  "history": [
    { "id": 1, "prediction_date": "2026-04-01", "target_date": "2026-04-02", "predicted_price": 213.45, "actual_price": null, "confidence_score": 0.72, "trend_direction": "up", "model_source": "local" }
  ]
}
```

#### `GET /predictions/{symbol}/backtest`
```json
{ "symbol": "AAPL", "count": 45, "mae": 1.234, "rmse": 1.892 }
```

---

### Agent

#### `POST /agent/query`
```json
// Request
{ "query": "What is the predicted price for AAPL next week?" }

// Response 200
{ "query": "What is the predicted price for AAPL next week?", "response": "Price predictions for AAPL:\n  2026-04-07: $215.20 (up) confidence=72% [local]" }
```

---

### Symbols

#### `GET /symbols/search?q=apple`
```json
{ "results": [{ "symbol": "AAPL", "company_name": "Apple Inc.", "exchange": null }] }
```
