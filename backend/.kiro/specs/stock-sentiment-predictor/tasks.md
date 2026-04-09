# Implementation Plan: Stock Sentiment Predictor

## Overview

Implement a pure Python backend (no web framework) that collects stock data and financial news,
performs dual-algorithm sentiment analysis, trains and runs LSTM-based price predictions, and
coordinates all operations through a GPT-Nano agent with a click-based CLI.

All commands run from `backend/` with `source .venv/bin/activate` active.
Package installation uses `uv add <package>`.

## Tasks

- [ ] 1. Install dependencies
  - Run: `uv add sqlmodel psycopg2-binary asyncpg pydantic-settings "passlib[bcrypt]" "python-jose[cryptography]"`
  - Run: `uv add textblob vaderSentiment yfinance requests schedule click loguru`
  - Run: `uv add tensorflow scikit-learn joblib numpy pandas`
  - Run: `uv add pytest hypothesis --dev`
  - _Requirements: all_


- [ ] 2. Configuration layer
  - [ ] 2.1 Implement `app/config/config.py` with Pydantic Settings
    - Define `Settings` class loading from `.env` with fields: `APP_NAME`, `DEBUG`, `LOG_LEVEL`
    - Add DB fields: `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
    - Add computed properties `sync_database_url` (`postgresql+psycopg2://...`) and `async_database_url` (`postgresql+asyncpg://...`)
    - Add Azure OpenAI fields: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`
    - Add Azure ML fields (optional, default `""`): `AZURE_ML_ENDPOINT`, `AZURE_ML_API_KEY`
    - Add security fields: `SECRET_KEY`, `ALGORITHM` (default `"HS256"`), `ACCESS_TOKEN_EXPIRE_MINUTES`
    - Add external API fields: `NEWS_API_KEY`, `ALPHA_VANTAGE_API_KEY` (optional)
    - Raise `ValidationError` on missing required fields
    - Expose a module-level `settings = Settings()` singleton
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 2.2 Implement `app/config/database.py`
    - Create sync SQLAlchemy engine using `settings.sync_database_url` with `pool_pre_ping=True`
    - Create async SQLAlchemy engine using `settings.async_database_url` with `NullPool` and `pool_pre_ping=True`
    - Define `SyncSessionLocal` and `AsyncSessionLocal` session factories
    - Implement `get_sync_session()` context manager (yields session, commits on success, rolls back on exception)
    - Implement `async get_async_session()` async context manager with same semantics
    - _Requirements: 2.1, 2.5_

  - [ ] 2.3 Implement `app/config/security.py`
    - Implement `hash_password(plain: str) -> str` using `passlib` bcrypt
    - Implement `verify_password(plain: str, hashed: str) -> bool`
    - Implement `create_access_token(data: dict, expires_delta: timedelta | None) -> str` using `python-jose` HS256
    - Implement `decode_access_token(token: str) -> dict` — raises `JWTError` on invalid/expired token
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ] 2.4 Create `.env` template file at project root
    - Include all required keys with placeholder values and inline comments
    - _Requirements: 1.1_


- [ ] 3. SQLModel data models
  - [ ] 3.1 Implement `app/models/user.py` — `User` and `UserSession` SQLModel tables
    - `User`: `id` (PK), `email` (unique), `username` (unique), `hashed_password`, `full_name`, `is_active` (default True), `created_at`, `updated_at`
    - `UserSession`: `id` (PK), `user_id` (FK → users.id), `token` (unique), `ip_address`, `user_agent`, `expires_at`, `last_activity`, `is_active` (default True)
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ] 3.2 Implement `app/models/stock.py` — `StockSymbol` and `StockData` SQLModel tables
    - `StockSymbol`: `id` (PK), `symbol` (unique), `company_name`, `exchange`, `sector`, `industry`, `is_active` (default True)
    - `StockData`: `id` (PK), `symbol_id` (FK → stock_symbols.id), `date`, `open`, `high`, `low`, `close`, `volume`, `adj_close`
    - Add composite index on `(symbol_id, date)` for `StockData`
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.3 Implement `app/models/news.py` — `NewsArticle` and `SentimentAnalysis` SQLModel tables
    - `NewsArticle`: `id` (PK), `symbol_id` (FK → stock_symbols.id), `title`, `content`, `url` (unique), `source`, `published_at`
    - `SentimentAnalysis`: `id` (PK), `article_id` (FK → news_articles.id), `textblob_polarity`, `textblob_subjectivity`, `vader_compound`, `vader_positive`, `vader_neutral`, `vader_negative`, `combined_score`, `classification` (positive/neutral/negative), `processed_at`
    - Add composite index on `(symbol_id, published_at)` for `NewsArticle`
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.4 Implement `app/models/sentiment.py` — `DailySentiment` SQLModel table
    - `DailySentiment`: `id` (PK), `symbol_id` (FK → stock_symbols.id), `date`, `avg_sentiment_score`, `article_count`, `positive_count`, `neutral_count`, `negative_count`
    - Add composite index on `(symbol_id, date)`
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 3.5 Implement `app/models/prediction.py` — `Prediction` SQLModel table
    - `Prediction`: `id` (PK), `symbol_id` (FK → stock_symbols.id), `user_id` (FK → users.id, nullable), `predicted_price`, `confidence_score`, `trend_direction`, `model_source` (`local` or `azure`), `prediction_date`, `target_date`, `actual_price` (nullable), `created_at`
    - Add composite index on `(symbol_id, prediction_date)`
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 3.6 Create `app/models/__init__.py` exporting all models and a shared `SQLModel` metadata
    - Import all table classes so Alembic autogenerate can discover them
    - _Requirements: 2.1, 2.5_

  - [ ] 3.7 Update `alembic/env.py` — set `target_metadata` only
    - Import `SQLModel` from `sqlmodel` and set `target_metadata = SQLModel.metadata`
    - Import `app.models` to ensure all table classes are registered before autogenerate runs
    - Do NOT modify any other part of `env.py` or `alembic.ini`
    - _Requirements: 2.5_


- [ ] 4. Authentication service
  - [ ] 4.1 Implement `app/services/auth_service.py`
    - `register_user(session, email, username, password, full_name) -> User`: hash password, insert `User`, return model
    - `login_user(session, username_or_email, password, ip, user_agent) -> tuple[str, UserSession]`: verify credentials, call `create_access_token`, insert `UserSession`, return (token, session)
    - `verify_token(session, token) -> User`: decode JWT, look up `UserSession` by token, check `is_active` and `expires_at`, return `User`
    - `logout_user(session, token) -> None`: set `UserSession.is_active = False`
    - Raise descriptive exceptions (`ValueError`, `PermissionError`) on failure paths
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 4.2 Write unit tests for `auth_service` in `app/test/test_auth_service.py`
    - Test password hashing and verification (correct + wrong password)
    - Test JWT generation and decoding (valid token, expired token, tampered token)
    - Test `login_user` with mocked DB session — verify session record created
    - Test `verify_token` rejects expired/inactive sessions
    - Test `logout_user` marks session inactive
    - _Requirements: 15.1_


- [ ] 5. Logging setup
  - [ ] 5.1 Implement `app/utils/logger.py`
    - Configure `loguru` with console sink: DEBUG level when `settings.DEBUG` is True, INFO otherwise
    - Add rotating file sink: `logs/app_{date}.log`, daily rotation, `zip` compression, 30-day retention
    - Expose `logger` instance for import by all modules
    - _Requirements: 14.1_

  - [ ] 5.2 Create `logs/` directory placeholder (`.gitkeep`)
    - _Requirements: 14.1_


- [ ] 6. Data collection service and tools
  - [ ] 6.1 Implement `app/tools/data_tools.py`
    - `fetch_historical_data(symbol: str, start_date: str, end_date: str) -> list[dict]`: call `yfinance`, return list of OHLCV dicts; retry up to 3× with exponential backoff on failure
    - `fetch_current_price(symbol: str) -> float`: return latest close from yfinance
    - `get_technical_indicators(symbol: str, date_range: tuple) -> dict`: compute SMA-5, SMA-20, 20-day rolling volatility from DB records; return as dict
    - `fetch_news_articles(symbol: str, hours_back: int = 24) -> list[dict]`: call NewsAPI; log HTTP errors and return `[]` on failure
    - `fetch_rss_articles(feed_urls: list[str], symbol: str) -> list[dict]`: parse RSS feeds via `requests` + basic XML parsing
    - All tools return structured error dicts (not raise) on invalid params
    - _Requirements: 4.1, 4.2, 4.5, 5.1, 5.5, 5.6, 12.1, 12.4_

  - [ ] 6.2 Implement `app/services/data_service.py`
    - `collect_stock_data(session, symbol: str, start_date: str, end_date: str) -> int`: upsert `StockSymbol`, call `fetch_historical_data`, deduplicate by `(symbol_id, date)`, bulk-insert new rows, return count inserted; log start/end/count
    - `collect_news(session, symbol: str, hours_back: int = 24) -> int`: call `fetch_news_articles` + `fetch_rss_articles`, deduplicate by `url`, insert new `NewsArticle` rows, return count; log errors
    - `alpha_vantage_fallback(session, symbol: str, date: str) -> dict | None`: call Alpha Vantage API if `settings.ALPHA_VANTAGE_API_KEY` set, return OHLCV dict or None
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 5.1, 5.2, 5.3, 5.5, 14.2_

  - [ ]* 6.3 Write integration tests for `data_service` in `app/test/test_data_service.py`
    - Mock `yfinance` and `requests` responses
    - Verify correct DB insertion for new records
    - Verify deduplication skips existing `(symbol_id, date)` rows
    - Verify NewsAPI error is logged and collection continues
    - _Requirements: 15.4_


- [ ] 7. Sentiment analysis service and tools
  - [ ] 7.1 Implement `app/tools/sentiment_tools.py`
    - `preprocess_text(text: str) -> str`: strip HTML tags, remove special chars, collapse whitespace, lowercase
    - `analyze_article_sentiment(article_id: int, session) -> dict`: load article, preprocess, run TextBlob + VADER, compute combined score (weighted avg, default 0.5/0.5), classify, upsert `SentimentAnalysis`, return result dict; log article_id, score, duration
    - `get_daily_sentiment(symbol: str, date_range: tuple, session) -> list[dict]`: query `DailySentiment` for symbol+range
    - `compare_sentiment(symbols: list[str], date_range: tuple, session) -> dict`: call `get_daily_sentiment` per symbol, return comparison dict
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 12.2, 14.3_

  - [ ] 7.2 Implement `app/services/sentiment_service.py`
    - `analyze_pending_articles(session, symbol: str) -> int`: query `NewsArticle` rows without a `SentimentAnalysis` record, call `analyze_article_sentiment` for each, return count processed
    - `aggregate_daily_sentiment(session, symbol: str, date: str) -> DailySentiment`: compute avg score + counts from `SentimentAnalysis` joined to `NewsArticle` for symbol+date, upsert `DailySentiment`
    - _Requirements: 6.5, 6.6_

  - [ ]* 7.3 Write unit tests for sentiment in `app/test/test_sentiment_service.py`
    - Test `preprocess_text` strips HTML, lowercases, collapses whitespace
    - Test TextBlob score range [-1, 1] on sample texts
    - Test VADER compound score range [-1, 1] on sample texts
    - Test combined score calculation with custom weights
    - Test classification thresholds (>0.05 positive, <-0.05 negative, else neutral)
    - Test `aggregate_daily_sentiment` with synthetic article set
    - _Requirements: 15.2_


- [ ] 8. Checkpoint — core data pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Prediction service and LSTM model
  - [ ] 9.1 Create `app/models/trained/` directory with `.gitkeep`
    - _Requirements: 7.6_

  - [ ] 9.2 Implement `app/tools/prediction_tools.py`
    - `engineer_features(session, symbol: str, end_date: str, window: int = 60) -> pd.DataFrame`: query `StockData` + `DailySentiment`, compute `sma_5`, `sma_20`, `volatility` (20-day rolling std of returns), return DataFrame with 9 columns: `open`, `high`, `low`, `close`, `volume`, `sentiment_score`, `sma_5`, `sma_20`, `volatility`
    - `create_sequences(df: pd.DataFrame, seq_len: int = 60) -> tuple[np.ndarray, np.ndarray]`: build (X, y) arrays for LSTM input
    - `build_lstm_model(input_shape: tuple) -> tf.keras.Model`: LSTM(50, return_sequences=True) → Dropout(0.2) → LSTM(50) → Dense(25, relu) → Dense(1); compile Adam lr=0.001, MSE
    - `save_model_artifacts(symbol: str, model, scaler) -> None`: save `.keras` and scaler via `joblib` to `app/models/trained/`
    - `load_model_artifacts(symbol: str) -> tuple[model, scaler] | None`: load from disk, return None if not found
    - `predict_price(symbol: str, horizon_days: int, session) -> list[dict]`: load or train model, prepare last-60-day sequence, iteratively predict, inverse-transform, return list of `{date, predicted_price, confidence, trend}`; log symbol, horizon, confidence, model_source
    - `batch_predict(symbols: list[str], session) -> dict`: call `predict_price` per symbol
    - `get_prediction_history(symbol: str, session) -> list[dict]`: query `Prediction` table
    - `calculate_confidence(session, symbol: str, scaler) -> float`: based on recent MAE, sentiment volatility, market volatility
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7, 12.3, 14.4_

  - [ ] 9.3 Implement `app/services/prediction_service.py`
    - `train_model(session, symbol: str) -> dict`: orchestrate feature engineering → sequence creation → model build → train 50 epochs batch 32 → evaluate on test set → save artifacts; return `{mse, mae}`; log metrics
    - `generate_prediction(session, symbol: str, horizon_days: int, user_id: int | None) -> list[Prediction]`: call `predict_price`, insert `Prediction` rows, return list
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.1, 8.2_

  - [ ]* 9.4 Write unit tests for prediction in `app/test/test_prediction_service.py`
    - Test `engineer_features` returns DataFrame with exactly 9 columns
    - Test `create_sequences` output shapes match expected `(n_samples, 60, 9)` and `(n_samples,)`
    - Test MinMaxScaler normalization keeps values in [0, 1]
    - Test `calculate_confidence` returns value in [0, 1]
    - Use synthetic data (no DB required)
    - _Requirements: 15.3_


- [ ] 10. Azure ML client
  - [ ] 10.1 Implement `app/services/azure_ml_client.py`
    - `AzureMLClient` class initialized with `settings.AZURE_ML_ENDPOINT` and `settings.AZURE_ML_API_KEY`
    - `predict(features: dict) -> float`: POST JSON to endpoint with `Authorization: Bearer` header, validate response contains numeric price, return float; log errors and raise `RuntimeError` on HTTP error or timeout
    - `is_configured() -> bool`: return True only when both endpoint and key are non-empty
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 10.2 Wire Azure ML fallback into `prediction_service.generate_prediction`
    - If no local model and `AzureMLClient.is_configured()`, call `azure_ml_client.predict(features)` and store with `model_source="azure"`
    - If Azure ML also fails, fall back to on-demand local training
    - _Requirements: 8.6, 9.1, 9.2, 9.4_


- [ ] 11. Node-based processing pipeline
  - [ ] 11.1 Implement `app/nodes/base_node.py` — `BaseNode` abstract class
    - Abstract method `execute(inputs: dict) -> dict`
    - Wrap execution in try/except: log full context on exception, re-raise as `NodeExecutionError`
    - _Requirements: 11.1, 11.4_

  - [ ] 11.2 Implement `app/nodes/data_collection_node.py` — `DataCollectionNode`
    - `execute(inputs)`: expects `symbol`, `start_date`, `end_date`; calls `data_service.collect_stock_data` + `data_service.collect_news`; returns `{stock_count, news_count}`
    - _Requirements: 11.2, 11.3_

  - [ ] 11.3 Implement `app/nodes/preprocessing_node.py` — `PreprocessingNode`
    - `execute(inputs)`: expects `symbol`, `date_range`; calls `engineer_features`; returns `{features_df}` (serialized as records list)
    - _Requirements: 11.2, 11.3_

  - [ ] 11.4 Implement `app/nodes/analysis_node.py` — `AnalysisNode`
    - `execute(inputs)`: expects `symbol`, `date_range`; calls `sentiment_service.analyze_pending_articles` + `aggregate_daily_sentiment`; returns `{daily_sentiment}`
    - _Requirements: 11.2, 11.3_

  - [ ] 11.5 Implement `app/nodes/prediction_node.py` — `PredictionNode`
    - `execute(inputs)`: expects `symbol`, `horizon_days`, optional `user_id`; calls `prediction_service.generate_prediction`; returns `{predictions}`
    - _Requirements: 11.2, 11.3_

  - [ ] 11.6 Implement `app/nodes/aggregation_node.py` — `AggregationNode`
    - `execute(inputs)`: merges outputs from previous nodes into a unified result dict; computes summary stats
    - _Requirements: 11.2, 11.3_

  - [ ] 11.7 Implement `app/nodes/output_node.py` — `OutputNode`
    - `execute(inputs)`: formats aggregated result into human-readable string/dict for CLI display
    - _Requirements: 11.2, 11.3_

  - [ ] 11.8 Implement `app/nodes/pipeline.py` — `Pipeline` executor
    - `Pipeline(nodes: list[BaseNode])` — `run(initial_inputs: dict) -> dict`: execute nodes sequentially, passing each output as next input; catch `NodeExecutionError` and return error result
    - _Requirements: 11.3, 11.4, 11.5_


- [ ] 12. Utility tools
  - [ ] 12.1 Implement `app/tools/utility_tools.py`
    - `search_symbols(query: str, session) -> list[dict]`: query `StockSymbol` table with ILIKE on symbol/company_name
    - `format_response(data: dict) -> str`: pretty-print dict as formatted string
    - `validate_input(params: dict, schema: dict) -> dict | None`: validate types/ranges, return error dict or None
    - _Requirements: 12.4, 12.5_


- [ ] 13. Agent coordinator
  - [ ] 13.1 Implement `app/agent/agent.py` — `Agent` class
    - `__init__`: initialize `AzureOpenAI` client from `settings`; define system prompt with tool descriptions and JSON response format for intent classification
    - `classify_intent(query: str) -> dict`: send query to GPT-Nano, parse JSON response for `intent_type` and `entities`; on malformed response default to `{"intent_type": "general_question", "entities": {}}`
    - Supported intents: `get_prediction`, `analyze_sentiment`, `view_stock_data`, `compare_stocks`, `explain_trends`, `general_question`
    - `run(query: str, session) -> str`: call `classify_intent`, select and execute appropriate tools/pipeline based on intent, synthesize natural-language response from results
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ]* 13.2 Write integration test for agent in `app/test/test_agent.py`
    - Mock `AzureOpenAI` client to return predefined intent JSON
    - Send `"What is the predicted price for AAPL?"` and verify `intent_type == "get_prediction"` and `entities["symbol"] == "AAPL"`
    - Send malformed GPT response and verify fallback to `general_question`
    - _Requirements: 15.6_


- [ ] 14. Scheduler
  - [ ] 14.1 Implement `app/services/scheduler.py`
    - Use `schedule` library with background thread (`threading.Thread(daemon=True)`)
    - Job 1: daily stock data collection at configurable time (default `"18:00"`) — calls `data_service.collect_stock_data` for all active symbols
    - Job 2: hourly news collection — calls `data_service.collect_news` for all active symbols
    - `start_scheduler(session_factory) -> None`: register jobs and start background thread
    - `stop_scheduler() -> None`: clear all jobs
    - _Requirements: 4.4, 5.3_


- [ ] 15. CLI entry point
  - [ ] 15.1 Implement `app/main.py` with click CLI
    - `@cli.command() run`: start interactive loop — read user input, pass to `Agent.run(query, session)`, print response; Ctrl-C exits gracefully
    - `@cli.command() train-model --symbol TEXT`: call `prediction_service.train_model`, print `{mse, mae}` on completion
    - `@cli.command() collect-data --symbols TEXT... [--days INT]`: call `data_service.collect_stock_data` + `collect_news` per symbol, print summary of records inserted
    - `@cli.command() predict --symbol TEXT --days INT`: call `prediction_service.generate_prediction`, print predicted prices, trend, confidence per day
    - `@cli.command() analyze-sentiment --symbol TEXT`: call `sentiment_service.analyze_pending_articles` + `aggregate_daily_sentiment`, print daily aggregated score
    - `@cli.command() backtest --symbol TEXT`: query `Prediction` table for rows with non-null `actual_price`, compute MAE and RMSE, print metrics
    - Initialize logging, DB, and scheduler (for `run` command) at startup
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_


- [ ] 16. Checkpoint — full pipeline wiring
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Property-based and integration tests
  - [ ]* 17.1 Write property test: stock data round-trip serialization in `app/test/test_properties.py`
    - **Property 1: Round-trip consistency** — for all valid `StockData` records serialized to JSON and deserialized back, the result SHALL equal the original
    - Use `hypothesis` strategies to generate synthetic `StockData` field values
    - **Validates: Requirements 15.5**

  - [ ]* 17.2 Write property test: sentiment score bounds
    - **Property 2: Combined sentiment score is always in [-1, 1]** — for all article texts generated by hypothesis, `analyze_article_sentiment` combined score SHALL be in [-1, 1]
    - **Validates: Requirements 6.4**

  - [ ]* 17.3 Write property test: confidence score bounds
    - **Property 3: Confidence score is always in [0, 1]** — for all synthetic feature inputs, `calculate_confidence` SHALL return a value in [0, 1]
    - **Validates: Requirements 8.5**

  - [ ]* 17.4 Write integration test for full node pipeline in `app/test/test_pipeline.py`
    - Construct a pipeline: `DataCollectionNode → PreprocessingNode → AnalysisNode → PredictionNode → AggregationNode → OutputNode`
    - Mock all external API calls and DB sessions
    - Verify output dict contains `predictions` key with at least one entry
    - _Requirements: 11.3, 11.4, 11.5_

- [ ] 18. Final checkpoint — all tests pass
  - Run `pytest app/test/ -v` and ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- All code uses Python 3.12 type hints throughout
- Package installation uses `uv add` — never `pip install`
- Do NOT modify `alembic/env.py` beyond setting `target_metadata`, and do NOT touch `alembic.ini`
- After models are defined (task 3), run: `alembic revision --autogenerate -m "initial"` then `alembic upgrade head`
- LSTM model files saved to `app/models/trained/{symbol}_lstm.keras`; scalers saved as `{symbol}_scaler.joblib`
- Property tests use `hypothesis` library; annotate each with the property number and requirement clause
