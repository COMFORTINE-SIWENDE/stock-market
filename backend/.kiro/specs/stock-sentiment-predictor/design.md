# Design Document: stock-sentiment-predictor

## Overview

A pure Python backend (no web framework) that collects stock market data and financial news,
performs dual-algorithm sentiment analysis (TextBlob + VADER), trains and runs LSTM-based
price predictions, and coordinates all operations through a GPT-Nano agent. The system exposes
a click-based CLI, uses PostgreSQL for persistence via SQLModel, and supports Azure ML as a
cloud prediction fallback.

### Key Design Decisions

- **No web framework**: All user interaction is through the click CLI; no HTTP server is started.
- **SQLModel over raw SQLAlchemy**: Combines Pydantic validation with SQLAlchemy ORM in one class hierarchy.
- **Dual DB engines**: Synchronous (psycopg2) for CLI/scheduler operations; async (asyncpg) reserved for future extension.
- **Alembic integration via metadata import**: `alembic/env.py` imports `SQLModel.metadata` so autogenerate works.
- **Node pipeline**: Composable processing units assembled dynamically by the agent per intent.
- **Loguru**: Single structured logger replacing stdlib logging throughout.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI (click)                              │
│  run | train-model | collect-data | predict | analyze-sentiment │
│  backtest                                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ user input / commands
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Coordinator                             │
│  AzureOpenAI (gpt-5.4-nano) – intent recognition               │
│  Tool selection loop → Pipeline construction                    │
└──────┬──────────────────────────────────────────────────────────┘
       │ selects tools & nodes
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Tool Library (12 tools)                      │
│  Stock: fetch_historical_data, fetch_current_price,              │
│         get_technical_indicators                                 │
│  Sentiment: analyze_article_sentiment, get_daily_sentiment,      │
│             compare_sentiment                                    │
│  Prediction: predict_price, batch_predict,                       │
│              get_prediction_history                              │
│  Utility: search_symbols, format_response, validate_input        │
└──────┬───────────────────────────────────────────────────────────┘
       │ calls into
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Service Layer                                │
│  AuthService | DataCollector | SentimentAnalyzer                 │
│  PredictionService | AzureMLClient                               │
└──────┬───────────────────────────────────────────────────────────┘
       │ reads/writes
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Data / Infrastructure Layer                     │
│  PostgreSQL (SQLModel ORM, Alembic migrations)                   │
│  Yahoo Finance / NewsAPI / Alpha Vantage (external APIs)         │
│  Azure OpenAI (GPT-Nano) / Azure ML (LSTM endpoint)             │
│  TensorFlow LSTM models (local .keras files)                     │
│  Scheduler (schedule library, background threads)                │
│  Loguru (structured rotating logs)                               │
└──────────────────────────────────────────────────────────────────┘
```


### Component Interaction Flow

1. User invokes a CLI command or enters interactive mode (`run`).
2. CLI passes input to the Agent Coordinator.
3. Agent sends query to GPT-Nano → receives structured intent + entities.
4. Agent selects tools and constructs a Node pipeline.
5. Nodes execute sequentially; each node's output dict feeds the next.
6. Services are called from within nodes/tools; they read/write the DB.
7. Final result is formatted and printed to stdout.
8. Scheduler runs data collection and sentiment aggregation in background threads independently.

---

## Components and Interfaces

### Config (`app/config/config.py`)

```python
class Settings(BaseSettings):
    app_name: str = "stock-sentiment-predictor"
    debug: bool = False
    log_level: str = "INFO"
    db_host: str
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str

    @property
    def sync_db_uri(self) -> str: ...
    @property
    def async_db_uri(self) -> str: ...

    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str
    azure_openai_api_version: str
    azure_ml_endpoint: str = ""
    azure_ml_api_key: str = ""
    secret_key: str
    algorithm: str = "HS256"
    token_expire_minutes: int = 60
    news_api_key: str = ""
    alpha_vantage_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")
```

### Database (`app/config/database.py`)

```python
sync_engine = create_engine(settings.sync_db_uri, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

async_engine = create_async_engine(settings.async_db_uri, poolclass=NullPool)
AsyncSession = async_sessionmaker(bind=async_engine, autocommit=False, autoflush=False)

def get_sync_session() -> Generator[Session, None, None]: ...
async def get_async_session() -> AsyncGenerator[AsyncSession, None]: ...
```

### AuthService (`app/services/auth_service.py`)

```python
class AuthService:
    def hash_password(self, plain: str) -> str: ...
    def verify_password(self, plain: str, hashed: str) -> bool: ...
    def create_token(self, user_id: int, username: str) -> str: ...
    def verify_token(self, token: str) -> dict: ...
    def create_session(self, db, user_id, token, ip, user_agent) -> UserSession: ...
    def invalidate_session(self, db, token: str) -> None: ...
    def get_active_session(self, db, token: str) -> UserSession | None: ...
```

### DataCollector (`app/services/data_collector.py`)

```python
class DataCollector:
    def fetch_stock_data(self, db, symbol: str, start: date, end: date) -> int: ...
    def fetch_news_articles(self, db, symbol: str, hours_back: int = 24) -> int: ...
    def _fetch_yfinance(self, symbol: str, start: date, end: date) -> list[dict]: ...
    def _fetch_alpha_vantage(self, symbol: str, start: date, end: date) -> list[dict]: ...
    def _fetch_newsapi(self, symbol: str, hours_back: int) -> list[dict]: ...
    def _retry(self, fn, retries: int = 3): ...
```

### SentimentAnalyzer (`app/services/sentiment_analyzer.py`)

```python
class SentimentAnalyzer:
    def preprocess(self, text: str) -> str: ...
    def analyze_textblob(self, text: str) -> tuple[float, float]: ...
    def analyze_vader(self, text: str) -> dict: ...
    def combined_score(self, tb_polarity: float, vader_compound: float,
                       tb_weight: float = 0.5) -> float: ...
    def classify(self, score: float) -> str: ...
    def analyze_article(self, db, article_id: int) -> SentimentAnalysis: ...
    def aggregate_daily(self, db, symbol_id: int, date: date) -> DailySentiment: ...
```

### PredictionService (`app/services/prediction_service.py`)

```python
class PredictionService:
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame: ...
    def create_sequences(self, data: np.ndarray, seq_len: int = 60
                         ) -> tuple[np.ndarray, np.ndarray]: ...
    def build_model(self) -> Sequential: ...
    def train(self, db, symbol: str) -> dict: ...
    def load_model(self, symbol: str) -> tuple[Sequential, MinMaxScaler] | None: ...
    def predict(self, db, symbol: str, horizon: int = 1) -> list[dict]: ...
    def confidence_score(self, symbol: str, sentiment_vol: float,
                         market_vol: float) -> float: ...
```

### AzureMLClient (`app/services/azure_ml_client.py`)

```python
class AzureMLClient:
    def predict(self, features: dict) -> float: ...
    def is_configured(self) -> bool: ...
```

### AgentCoordinator (`app/agent/coordinator.py`)

```python
class AgentCoordinator:
    def __init__(self, settings: Settings): ...
    def process_query(self, db, query: str) -> str: ...
    def _recognize_intent(self, query: str) -> dict: ...
    def _build_pipeline(self, intent: dict) -> list[BaseNode]: ...
    def _run_pipeline(self, db, nodes: list[BaseNode], inputs: dict) -> dict: ...
```

### Scheduler (`app/services/scheduler.py`)

```python
def start_scheduler(settings: Settings) -> threading.Thread: ...
def _stock_collection_job(settings: Settings) -> None: ...
def _news_collection_job(settings: Settings) -> None: ...
```


---

## Data Models

All models are `SQLModel` classes with `table=True`. Indexes are declared via `__table_args__`.

### User

```python
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    username: str = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### UserSession

```python
class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token: str = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
```

### StockSymbol

```python
class StockSymbol(SQLModel, table=True):
    __tablename__ = "stock_symbols"
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    company_name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool = True
```

### StockData

```python
class StockData(SQLModel, table=True):
    __tablename__ = "stock_data"
    __table_args__ = (
        UniqueConstraint("symbol_id", "date"),
        Index("ix_stock_data_symbol_date", "symbol_id", "date"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id", nullable=False)
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None
```

### NewsArticle

```python
class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id", nullable=False)
    title: str
    content: Optional[str] = None
    url: str = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    source: Optional[str] = None
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.utcnow)
```

### SentimentAnalysis

```python
class SentimentAnalysis(SQLModel, table=True):
    __tablename__ = "sentiment_analysis"
    __table_args__ = (Index("ix_sentiment_symbol_date", "symbol_id", "date"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="news_articles.id", nullable=False)
    symbol_id: int = Field(foreign_key="stock_symbols.id", nullable=False)
    date: date
    tb_polarity: float
    tb_subjectivity: float
    vader_compound: float
    vader_positive: float
    vader_neutral: float
    vader_negative: float
    combined_score: float
    classification: str  # positive | neutral | negative
    processed_at: datetime = Field(default_factory=datetime.utcnow)
```

### DailySentiment

```python
class DailySentiment(SQLModel, table=True):
    __tablename__ = "daily_sentiment"
    __table_args__ = (
        UniqueConstraint("symbol_id", "date"),
        Index("ix_daily_sentiment_symbol_date", "symbol_id", "date"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id", nullable=False)
    date: date
    avg_combined_score: float
    article_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Prediction

```python
class Prediction(SQLModel, table=True):
    __tablename__ = "predictions"
    __table_args__ = (Index("ix_predictions_symbol_date", "symbol_id", "prediction_date"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol_id: int = Field(foreign_key="stock_symbols.id", nullable=False)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    prediction_date: date
    predicted_price: float
    confidence_score: float
    trend: str  # up | down | neutral
    model_source: str  # local | azure
    actual_price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Alembic Integration Approach

The constraint is that `alembic/env.py` and `alembic.ini` must not be modified during normal
development. The bootstrap approach:

1. All SQLModel table classes are imported in `app/models/__init__.py`, registering them in
   `SQLModel.metadata`.
2. A shim `app/config/alembic_metadata.py` exports `target_metadata = SQLModel.metadata`.
3. A one-time bootstrap edit adds to `alembic/env.py`:
   ```python
   from app.config.alembic_metadata import target_metadata
   ```
   replacing the existing `target_metadata = None` line. This is the only required edit and is
   documented in the implementation tasks.

---

## Tool System Design

All tools live in `app/tools/` as pure functions. They accept a `db: Session` where DB access is
needed and return a result dict or `{"error": str, "code": str}` on failure.

### Stock Data Tools (`app/tools/stock_tools.py`)

```python
def fetch_historical_data(db: Session, symbol: str,
                          start_date: str, end_date: str) -> dict: ...
# {"symbol": str, "data": list[dict], "count": int}

def fetch_current_price(db: Session, symbol: str) -> dict: ...
# {"symbol": str, "price": float, "date": str}

def get_technical_indicators(db: Session, symbol: str, date_range: int = 30) -> dict: ...
# {"symbol": str, "sma_5": list, "sma_20": list, "rsi": list, "macd": list}
```

### Sentiment Tools (`app/tools/sentiment_tools.py`)

```python
def analyze_article_sentiment(db: Session, article_id: int) -> dict: ...
# {"article_id": int, "combined_score": float, "classification": str}

def get_daily_sentiment(db: Session, symbol: str, date_range: int = 7) -> dict: ...
# {"symbol": str, "daily": list[dict]}

def compare_sentiment(db: Session, symbols: list[str], date_range: int = 7) -> dict: ...
# {"comparison": dict[str, list[dict]]}
```

### Prediction Tools (`app/tools/prediction_tools.py`)

```python
def predict_price(db: Session, symbol: str, horizon_days: int = 1) -> dict: ...
# {"symbol": str, "predictions": list[dict], "confidence": float}

def batch_predict(db: Session, symbols: list[str]) -> dict: ...
# {"results": dict[str, dict]}

def get_prediction_history(db: Session, symbol: str) -> dict: ...
# {"symbol": str, "history": list[dict]}
```

### Utility Tools (`app/tools/utility_tools.py`)

```python
def search_symbols(db: Session, query: str) -> dict: ...
# {"results": list[{"symbol": str, "company_name": str}]}

def format_response(data: dict) -> dict: ...
# Normalizes any tool output into a consistent envelope

def validate_input(params: dict, schema: dict) -> dict: ...
# {"valid": bool, "errors": list[str]}
```

---

## Node Pipeline Design

### BaseNode (`app/nodes/base_node.py`)

```python
from abc import ABC, abstractmethod

class BaseNode(ABC):
    name: str

    @abstractmethod
    def execute(self, inputs: dict) -> dict: ...
```

### Concrete Nodes (`app/nodes/`)

| Node | File | Responsibility |
|---|---|---|
| `DataCollectionNode` | `data_collection_node.py` | Calls DataCollector to fetch stock/news data |
| `PreprocessingNode` | `preprocessing_node.py` | Cleans text, normalizes features, fills gaps |
| `AnalysisNode` | `analysis_node.py` | Runs SentimentAnalyzer on collected articles |
| `PredictionNode` | `prediction_node.py` | Calls PredictionService to generate forecasts |
| `AggregationNode` | `aggregation_node.py` | Merges outputs from multiple upstream nodes |
| `OutputNode` | `output_node.py` | Formats final result dict for CLI display |

Each node receives the accumulated `inputs` dict from the previous node and returns an updated dict.
On exception, the pipeline halts and returns `{"error": str, "node": node.name}`.

---

## Agent Coordinator Design

### Intent Types

```
get_prediction | analyze_sentiment | view_stock_data |
compare_stocks | explain_trends | general_question
```

### GPT-Nano System Prompt Structure

```
You are a financial analyst assistant. Given a user query, respond with JSON:
{
  "intent": "<intent_type>",
  "entities": {
    "symbols": ["AAPL"],
    "horizon_days": 5,
    "date_range": 7
  }
}
Available intents: get_prediction, analyze_sentiment, view_stock_data,
compare_stocks, explain_trends, general_question.
```

### Tool Selection Loop

```
1. Recognize intent via GPT-Nano
2. Map intent → default pipeline (list of Node classes + tool calls)
3. Execute pipeline
4. If tool returns error, log and continue with partial results
5. Send aggregated results back to GPT-Nano for natural-language synthesis
6. Return final string to CLI
```

### Intent → Pipeline Mapping

| Intent | Pipeline |
|---|---|
| `get_prediction` | DataCollectionNode → PreprocessingNode → PredictionNode → OutputNode |
| `analyze_sentiment` | DataCollectionNode → AnalysisNode → AggregationNode → OutputNode |
| `view_stock_data` | DataCollectionNode → OutputNode |
| `compare_stocks` | DataCollectionNode → AnalysisNode → AggregationNode → OutputNode |
| `explain_trends` | DataCollectionNode → AnalysisNode → PredictionNode → AggregationNode → OutputNode |
| `general_question` | OutputNode (direct GPT-Nano response) |

---

## CLI Design

Entry point: `app/main.py` using `@click.group()`.

```
python -m app.main run
python -m app.main train-model --symbol AAPL
python -m app.main collect-data --symbols AAPL MSFT TSLA
python -m app.main predict --symbol AAPL --days 5
python -m app.main analyze-sentiment --symbol AAPL
python -m app.main backtest --symbol AAPL
```

Each command:
1. Loads `Settings` from `.env`
2. Opens a `SyncSession`
3. Calls the appropriate service or agent method
4. Prints structured output to stdout
5. Closes session

---

## Scheduler Design

`app/services/scheduler.py` uses the `schedule` library in a daemon thread.

```python
schedule.every().day.at("17:00").do(_stock_collection_job, settings)
schedule.every(1).hours.do(_news_collection_job, settings)
```

- Each job opens its own `SyncSession`, runs the collection, commits, and closes.
- Errors are caught, logged with loguru, and do not crash the scheduler thread.
- The scheduler thread is started by the `run` CLI command alongside the interactive loop.

---

## Logging Setup

`app/utils/logger.py` configures loguru at import time:

```python
from loguru import logger

def setup_logging(log_level: str = "INFO", debug: bool = False) -> None:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if debug else log_level,
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function} | {message}")
    logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="1 day",
               compression="zip", level="INFO", retention="30 days")
```

All modules import `from loguru import logger` directly — no passing logger instances around.

---

## File Structure Additions

```
app/
├── agent/
│   ├── __init__.py
│   └── coordinator.py          # AgentCoordinator
├── config/
│   ├── config.py               # Settings (pydantic-settings)
│   ├── database.py             # sync/async engines + session factories
│   ├── security.py             # JWT helpers
│   └── alembic_metadata.py     # exports SQLModel.metadata for alembic
├── models/
│   ├── __init__.py             # imports all table classes → registers metadata
│   ├── user.py                 # User, UserSession
│   ├── stock.py                # StockSymbol, StockData
│   ├── news.py                 # NewsArticle
│   └── sentiment.py            # SentimentAnalysis, DailySentiment, Prediction
├── nodes/
│   ├── base_node.py            # BaseNode ABC
│   ├── data_collection_node.py
│   ├── preprocessing_node.py
│   ├── analysis_node.py
│   ├── prediction_node.py
│   ├── aggregation_node.py
│   └── output_node.py
├── services/
│   ├── auth_service.py
│   ├── data_collector.py
│   ├── sentiment_analyzer.py
│   ├── prediction_service.py
│   ├── azure_ml_client.py
│   └── scheduler.py
├── tools/
│   ├── stock_tools.py
│   ├── sentiment_tools.py
│   ├── prediction_tools.py
│   └── utility_tools.py
├── utils/
│   ├── __init__.py
│   └── logger.py
├── test/
│   ├── test_auth_service.py
│   ├── test_sentiment_analyzer.py
│   ├── test_prediction_service.py
│   ├── test_data_collector.py
│   ├── test_agent.py
│   └── test_properties.py      # hypothesis property-based tests
└── main.py                     # click CLI entry point
models/
└── trained/                    # {symbol}_lstm.keras + {symbol}_scaler.pkl
logs/                           # rotating log files
```


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Database URI construction is deterministic

*For any* valid combination of host, port, user, password, and database name, the constructed
synchronous URI must match `postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}` and the
async URI must match `postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}`.

**Validates: Requirements 1.2**

---

### Property 2: Password hashing is a one-way function with correct verification

*For any* plaintext password string, the hashed value must not equal the plaintext, and
`verify_password(plain, hash_password(plain))` must return `True`. Additionally,
`verify_password(plain, hash_password(plain + "x"))` must return `False`.

**Validates: Requirements 3.1**

---

### Property 3: JWT round-trip preserves user identity

*For any* `user_id` (positive integer) and `username` (non-empty string), encoding then decoding
a JWT token must produce a payload containing the original `user_id` and `username` unchanged.

**Validates: Requirements 3.2, 3.4**

---

### Property 4: Stock data deduplication inserts only new dates

*For any* set of existing `StockData` records for a symbol and any incoming batch of records
(which may overlap), the number of newly inserted rows must equal the count of dates in the
incoming batch that are not already present in the DB for that symbol.

**Validates: Requirements 4.3**

---

### Property 5: Article deduplication inserts only new URLs

*For any* set of existing `NewsArticle` records and any incoming batch of articles (which may
overlap by URL), the number of newly inserted articles must equal the count of URLs in the
incoming batch not already present in the DB.

**Validates: Requirements 5.2**

---

### Property 6: Text preprocessing removes HTML and lowercases

*For any* input string, the preprocessed output must contain no HTML tags (no `<...>` patterns),
must be entirely lowercase, and must contain no leading/trailing whitespace.

**Validates: Requirements 6.1**

---

### Property 7: Sentiment scores are always within valid ranges

*For any* text input, the TextBlob polarity must be in `[-1.0, 1.0]`, the TextBlob subjectivity
must be in `[0.0, 1.0]`, and the VADER compound score must be in `[-1.0, 1.0]`. Additionally,
the VADER positive, neutral, and negative scores must each be in `[0.0, 1.0]` and sum to
approximately `1.0` (within floating-point tolerance).

**Validates: Requirements 6.2, 6.3**

---

### Property 8: Combined sentiment score is a weighted average

*For any* TextBlob polarity `p` in `[-1, 1]`, VADER compound `v` in `[-1, 1]`, and weight `w`
in `[0, 1]`, the combined score must equal `w * p + (1 - w) * v` within floating-point tolerance.

**Validates: Requirements 6.4**

---

### Property 9: Sentiment classification matches threshold rules

*For any* combined score `s`, the classification must be `"positive"` if `s > 0.05`,
`"negative"` if `s < -0.05`, and `"neutral"` otherwise. No other classification values are valid.

**Validates: Requirements 6.5**

---

### Property 10: Daily sentiment average equals arithmetic mean of individual scores

*For any* non-empty list of `SentimentAnalysis` records for a given symbol and date, the
`avg_combined_score` in the resulting `DailySentiment` record must equal the arithmetic mean of
all individual `combined_score` values, and the per-classification counts must sum to the total
article count.

**Validates: Requirements 6.6**

---

### Property 11: Feature engineering produces exactly 9 named columns

*For any* valid DataFrame with OHLCV and sentiment columns covering at least 20 rows (needed for
rolling windows), the output of `engineer_features` must contain exactly the columns: `open`,
`high`, `low`, `close`, `volume`, `sentiment_score`, `sma_5`, `sma_20`, `volatility`.

**Validates: Requirements 7.2**

---

### Property 12: MinMaxScaler normalization keeps all values in [0, 1]

*For any* 2D numeric array (representing feature data), after fitting and transforming with
`MinMaxScaler`, every value in the output array must be in the closed interval `[0.0, 1.0]`.

**Validates: Requirements 7.3**

---

### Property 13: Sequence creation produces correct shapes

*For any* array of `N` rows and `F` features where `N > 60`, `create_sequences` must return
`X` of shape `(N - 60, 60, F)` and `y` of shape `(N - 60,)`.

**Validates: Requirements 7.4**

---

### Property 14: Multi-day prediction returns exactly `horizon` results

*For any* symbol with a loaded model and any `horizon` value `h >= 1`, the `predict` method
must return a list of exactly `h` prediction dicts, each containing `predicted_price`,
`confidence_score`, and `trend`.

**Validates: Requirements 8.4**

---

### Property 15: Confidence score is always in [0, 1]

*For any* combination of recent prediction accuracy, sentiment volatility, and market volatility
inputs, the `confidence_score` method must return a float in the closed interval `[0.0, 1.0]`.

**Validates: Requirements 8.5**

---

### Property 16: Azure ML client validates numeric response

*For any* response dict that does not contain a numeric predicted price field, the
`AzureMLClient.predict` method must raise an exception rather than returning a non-numeric value.

**Validates: Requirements 9.3**

---

### Property 17: Agent intent recognition always returns a valid intent type

*For any* user query string (including empty strings, gibberish, and malformed GPT responses),
the recognized intent must be one of the six valid types: `get_prediction`, `analyze_sentiment`,
`view_stock_data`, `compare_stocks`, `explain_trends`, or `general_question`. Malformed or
unrecognized GPT responses must default to `general_question`.

**Validates: Requirements 10.3, 10.6**

---

### Property 18: Pipeline output chaining passes data between nodes

*For any* ordered list of nodes where each node's `execute` method returns a dict, the pipeline
executor must pass the output dict of node `i` as the input dict to node `i+1`, and the final
output must be the return value of the last node.

**Validates: Requirements 11.3**

---

### Property 19: Pipeline halts and returns error dict on node exception

*For any* pipeline where node `k` raises an exception, the pipeline must halt (not execute nodes
after `k`) and return a dict containing an `"error"` key with the exception message and a
`"node"` key identifying the failing node.

**Validates: Requirements 11.4**

---

### Property 20: Tools return error dict on invalid parameters (never raise)

*For any* tool function called with parameters that fail validation (wrong types, out-of-range
values, missing required fields), the function must return a dict containing an `"error"` key
rather than propagating an unhandled exception.

**Validates: Requirements 12.5**

---

### Property 21: StockData JSON round-trip preserves all fields

*For any* valid `StockData` instance, serializing to JSON via `.model_dump()` and reconstructing
via `StockData.model_validate(json.loads(json.dumps(record.model_dump())))` must produce an
instance where all fields are equal to the original.

**Validates: Requirements 15.5**

---

## Error Handling

### Configuration Errors

- Missing required env vars → `ValidationError` from pydantic-settings at startup; logged and process exits.
- Invalid DB URI → `OperationalError` on first connection attempt; logged with full context.

### External API Errors

- Yahoo Finance / NewsAPI failures → retry up to 3 times with exponential backoff (1s, 2s, 4s); after exhaustion, log error and continue.
- Azure ML HTTP errors → log error, signal `PredictionService` to fall back to local model.
- Azure OpenAI errors → log error, return `general_question` intent with clarification prompt.

### Database Errors

- Unique constraint violations on insert → caught, treated as deduplication (skip silently, log at DEBUG).
- Connection errors → logged at ERROR level; operation fails with descriptive message returned to caller.
- Transaction failures → session rolled back automatically in `get_sync_session` context manager.

### Model Errors

- Missing `.keras` file → `PredictionService` triggers on-demand training; if training fails, returns error dict.
- Scaler mismatch (wrong feature count) → caught, logged, prediction aborted with error dict.
- TensorFlow inference errors → caught, logged, fallback to Azure ML attempted.

### Node Pipeline Errors

- Any `Exception` in a node's `execute` → pipeline halts, returns `{"error": str(e), "node": node.name}`.
- Agent receives error result → synthesizes user-friendly error message via GPT-Nano.

### Tool Errors

- Invalid parameters → `validate_input` called first; returns `{"error": "...", "code": "INVALID_PARAMS"}`.
- DB session errors within tools → caught, returns `{"error": "...", "code": "DB_ERROR"}`.

---

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are required. Unit tests catch concrete bugs with specific
examples; property tests verify universal correctness across randomized inputs.

### Unit Tests (`app/test/`)

**`test_auth_service.py`**
- Password hashing produces non-plaintext output
- `verify_password` returns True for correct password, False for wrong
- JWT generation includes correct `user_id` and `username`
- JWT verification rejects expired tokens
- JWT verification rejects tampered tokens
- Session creation stores all required fields (mocked DB)
- Logout marks session inactive (mocked DB)

**`test_sentiment_analyzer.py`**
- `preprocess` removes HTML tags
- `preprocess` converts to lowercase
- `preprocess` strips extra whitespace
- `analyze_textblob` returns (polarity, subjectivity) tuple
- `analyze_vader` returns dict with compound, pos, neu, neg keys
- `combined_score` with equal weights returns average of two scores
- `classify` returns correct label for boundary values (0.05, -0.05)
- `aggregate_daily` upserts correctly with mocked DB

**`test_prediction_service.py`**
- `engineer_features` returns DataFrame with exactly 9 columns
- `create_sequences` returns correct shapes for known input
- `build_model` returns Sequential with correct layer count
- `confidence_score` returns value in [0, 1] for edge inputs (0.0, 1.0)
- Training metrics dict contains `mse` and `mae` keys

**`test_data_collector.py`** (integration, mocked APIs)
- `fetch_stock_data` inserts only new dates (deduplication)
- `fetch_news_articles` skips duplicate URLs
- Retry logic calls underlying function up to 3 times on failure
- NewsAPI error does not propagate exception

**`test_agent.py`** (integration, mocked OpenAI)
- Predefined query "predict AAPL for 5 days" → intent `get_prediction`, symbol `AAPL`
- Malformed GPT response → intent defaults to `general_question`
- All 6 intent types are recognized from representative queries

### Property-Based Tests (`app/test/test_properties.py`)

Uses `hypothesis` library. Each test runs a minimum of 100 iterations.

```python
# Feature: stock-sentiment-predictor, Property 1: Database URI construction is deterministic
@given(host=text(min_size=1), port=integers(1, 65535), user=text(min_size=1),
       password=text(min_size=1), db=text(min_size=1))
def test_db_uri_construction(host, port, user, password, db): ...

# Feature: stock-sentiment-predictor, Property 2: Password hashing is a one-way function
@given(password=text(min_size=1, max_size=72))
def test_password_hash_roundtrip(password): ...

# Feature: stock-sentiment-predictor, Property 3: JWT round-trip preserves user identity
@given(user_id=integers(min_value=1), username=text(min_size=1, max_size=50))
def test_jwt_roundtrip(user_id, username): ...

# Feature: stock-sentiment-predictor, Property 4: Stock data deduplication inserts only new dates
@given(existing=lists(dates()), incoming=lists(dates()))
def test_stock_deduplication(existing, incoming): ...

# Feature: stock-sentiment-predictor, Property 5: Article deduplication inserts only new URLs
@given(existing=lists(text(min_size=5)), incoming=lists(text(min_size=5)))
def test_article_deduplication(existing, incoming): ...

# Feature: stock-sentiment-predictor, Property 6: Text preprocessing removes HTML and lowercases
@given(text=text())
def test_preprocess_no_html_lowercase(text): ...

# Feature: stock-sentiment-predictor, Property 7: Sentiment scores are always within valid ranges
@given(text=text(min_size=1))
def test_sentiment_score_ranges(text): ...

# Feature: stock-sentiment-predictor, Property 8: Combined score is a weighted average
@given(p=floats(-1, 1), v=floats(-1, 1), w=floats(0, 1))
def test_combined_score_formula(p, v, w): ...

# Feature: stock-sentiment-predictor, Property 9: Classification matches threshold rules
@given(score=floats(-1, 1))
def test_classification_thresholds(score): ...

# Feature: stock-sentiment-predictor, Property 10: Daily sentiment average equals arithmetic mean
@given(scores=lists(floats(-1, 1), min_size=1))
def test_daily_sentiment_average(scores): ...

# Feature: stock-sentiment-predictor, Property 11: Feature engineering produces exactly 9 columns
@given(n_rows=integers(min_value=25, max_value=500))
def test_feature_engineering_columns(n_rows): ...

# Feature: stock-sentiment-predictor, Property 12: MinMaxScaler normalization keeps values in [0,1]
@given(data=arrays(dtype=float, shape=array_shapes(min_dims=2, max_dims=2)))
def test_minmax_scaler_range(data): ...

# Feature: stock-sentiment-predictor, Property 13: Sequence creation produces correct shapes
@given(n=integers(min_value=61, max_value=500), f=integers(min_value=1, max_value=20))
def test_sequence_shapes(n, f): ...

# Feature: stock-sentiment-predictor, Property 14: Multi-day prediction returns exactly horizon results
@given(horizon=integers(min_value=1, max_value=30))
def test_prediction_horizon_length(horizon): ...

# Feature: stock-sentiment-predictor, Property 15: Confidence score is always in [0, 1]
@given(accuracy=floats(0, 1), sent_vol=floats(0, 1), mkt_vol=floats(0, 1))
def test_confidence_score_range(accuracy, sent_vol, mkt_vol): ...

# Feature: stock-sentiment-predictor, Property 16: Azure ML client validates numeric response
@given(response=dictionaries(text(), text()))  # no numeric price key
def test_azure_ml_invalid_response(response): ...

# Feature: stock-sentiment-predictor, Property 17: Agent intent recognition always returns valid intent
@given(query=text())
def test_intent_always_valid(query): ...

# Feature: stock-sentiment-predictor, Property 18: Pipeline output chaining passes data between nodes
@given(n_nodes=integers(min_value=2, max_value=6))
def test_pipeline_chaining(n_nodes): ...

# Feature: stock-sentiment-predictor, Property 19: Pipeline halts and returns error dict on node exception
@given(fail_at=integers(min_value=0, max_value=4))
def test_pipeline_error_halts(fail_at): ...

# Feature: stock-sentiment-predictor, Property 20: Tools return error dict on invalid parameters
@given(params=dictionaries(text(), text()))
def test_tool_invalid_params_no_raise(params): ...

# Feature: stock-sentiment-predictor, Property 21: StockData JSON round-trip preserves all fields
@given(...)  # hypothesis strategies for StockData fields
def test_stock_data_json_roundtrip(): ...
```

**Configuration**: All property tests use `@settings(max_examples=100)` minimum. Tests that
involve floating-point arithmetic use `assume(not math.isnan(x) and not math.isinf(x))` guards.

### Test Isolation

- All DB-dependent tests use mocked sessions (no real DB required for unit tests).
- External API calls are mocked with `unittest.mock.patch`.
- Property tests for pure functions (sentiment scoring, feature engineering) require no mocking.
- Integration tests that need a real DB are marked `@pytest.mark.integration` and skipped by default.
