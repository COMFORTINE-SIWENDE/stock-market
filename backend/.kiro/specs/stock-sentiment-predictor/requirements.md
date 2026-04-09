# Requirements Document

## Introduction

A pure Python backend system (no web framework) that collects stock market data and financial news,
performs dual-algorithm sentiment analysis, trains and runs LSTM-based price predictions, and
coordinates all operations through a GPT-Nano agent. The system exposes a click-based CLI and
uses PostgreSQL for persistence, with Azure ML as a cloud prediction fallback.

## Glossary

- **System**: The stock-sentiment-predictor backend application
- **Agent**: The GPT-Nano (Azure OpenAI) orchestrator that interprets user intent and drives tool/node selection
- **Auth_Service**: The authentication and session management service
- **Data_Collector**: The service responsible for fetching stock prices and news articles from external APIs
- **Sentiment_Analyzer**: The service that runs TextBlob and VADER on news article text
- **Prediction_Service**: The service that prepares features, trains/loads LSTM models, and generates forecasts
- **Azure_ML_Client**: The client that calls the Azure ML REST endpoint for cloud-based predictions
- **Scheduler**: The background job runner using the `schedule` library
- **Node**: A single processing unit in the pipeline (data collection, preprocessing, analysis, prediction, aggregation, output)
- **Pipeline**: An ordered sequence of Nodes constructed by the Agent for a given user intent
- **CLI**: The click-based command-line interface entry point
- **DB**: The PostgreSQL database accessed via SQLModel ORM
- **Alembic**: The migration tool managing DB schema changes
- **LSTM_Model**: A TensorFlow/Keras sequential model stored as `{symbol}_lstm.keras` under `app/models/trained/`
- **Scaler**: A MinMaxScaler persisted alongside each LSTM_Model for consistent feature normalization
- **JWT**: JSON Web Token used for stateless user authentication (HS256)
- **Session**: A DB-backed record tracking an authenticated user's activity

## Requirements

### Requirement 1: Configuration Management

**User Story:** As a developer, I want all runtime parameters loaded from environment variables, so that the system can be configured without code changes.

#### Acceptance Criteria

1. THE System SHALL load all configuration values from a `.env` file at startup using Pydantic Settings with type validation.
2. THE System SHALL construct the synchronous PostgreSQL URI (`postgresql+psycopg2://...`) and asynchronous URI (`postgresql+asyncpg://...`) from individual host, port, user, password, and database name settings.
3. IF a required configuration value is missing or invalid, THEN THE System SHALL raise a descriptive startup error and halt initialization.
4. THE System SHALL expose Azure OpenAI endpoint, API key, deployment name, and API version as validated configuration fields.
5. THE System SHALL expose Azure ML endpoint URL and API key as optional configuration fields, defaulting to empty strings when not provided.

---

### Requirement 2: Database Schema and Migrations

**User Story:** As a developer, I want a well-structured PostgreSQL schema managed by Alembic, so that data is stored consistently and migrations are reproducible.

#### Acceptance Criteria

1. THE DB SHALL contain tables: `users`, `user_sessions`, `stock_symbols`, `stock_data`, `news_articles`, `sentiment_analysis`, `daily_sentiment`, and `predictions`, each defined as SQLModel classes.
2. THE DB SHALL enforce foreign key constraints: `user_sessions.user_id → users.id`, `stock_data.symbol_id → stock_symbols.id`, `news_articles.symbol_id → stock_symbols.id`, `sentiment_analysis.article_id → news_articles.id`, `daily_sentiment.symbol_id → stock_symbols.id`, `predictions.symbol_id → stock_symbols.id`, `predictions.user_id → users.id`.
3. THE DB SHALL have composite indexes on `(symbol_id, date)` for `stock_data`, `sentiment_analysis`, `daily_sentiment`, and `predictions` tables to support time-series queries.
4. THE DB SHALL have unique indexes on `users.email`, `users.username`, `user_sessions.token`, `news_articles.url`, and `stock_symbols.symbol`.
5. WHEN Alembic autogenerate is run, THE System SHALL detect all SQLModel table definitions and produce correct migration scripts without manual edits to `alembic/env.py` or `alembic.ini`.

---

### Requirement 3: Authentication and Session Management

**User Story:** As a user, I want to register and log in securely, so that my data and predictions are protected.

#### Acceptance Criteria

1. THE Auth_Service SHALL hash passwords using bcrypt via Passlib before storing them in the DB.
2. WHEN a user provides valid credentials, THE Auth_Service SHALL generate a JWT (HS256) containing `user_id` and `username` with a configurable expiration duration.
3. WHEN a user provides valid credentials, THE Auth_Service SHALL create a `user_sessions` record containing the session token, IP address, user agent, and expiration timestamp.
4. WHEN a JWT is presented for verification, THE Auth_Service SHALL validate the signature, expiration, and payload structure before granting access.
5. IF a session record is expired or not found in the DB, THEN THE Auth_Service SHALL reject the request with an authentication error.
6. THE Auth_Service SHALL provide a logout operation that marks the session record as inactive in the DB.

---

### Requirement 4: Stock Data Collection

**User Story:** As a data analyst, I want historical and current stock price data collected automatically, so that predictions are based on up-to-date market information.

#### Acceptance Criteria

1. WHEN the `collect-data` CLI command is invoked for a symbol, THE Data_Collector SHALL fetch daily OHLCV data from Yahoo Finance for the requested date range.
2. IF Yahoo Finance returns an error or empty response, THEN THE Data_Collector SHALL retry the request up to 3 times with exponential backoff before logging an error and continuing.
3. WHEN fetching stock data, THE Data_Collector SHALL check the DB for existing records and only insert rows for dates not already present (deduplication by `symbol_id` + `date`).
4. THE Scheduler SHALL trigger stock data collection daily after market close (configurable time) as a background thread.
5. IF Alpha Vantage API key is configured, THE Data_Collector SHALL use Alpha Vantage as a secondary source when Yahoo Finance data is unavailable for a given date range.

---

### Requirement 5: News Article Collection

**User Story:** As a data analyst, I want financial news articles collected continuously, so that sentiment analysis reflects current market narratives.

#### Acceptance Criteria

1. WHEN the `collect-data` CLI command is invoked, THE Data_Collector SHALL fetch news articles mentioning the target stock symbol from NewsAPI for the last 24 hours by default.
2. THE Data_Collector SHALL deduplicate articles using `url` as the unique identifier, skipping articles already present in the DB.
3. THE Scheduler SHALL trigger news article collection every hour as a background thread.
4. WHEN new articles are stored, THE Data_Collector SHALL immediately enqueue them for sentiment analysis.
5. IF NewsAPI returns an error, THEN THE Data_Collector SHALL log the error with the HTTP status code and continue without halting the collection run.
6. WHERE RSS feed URLs are configured, THE Data_Collector SHALL also collect articles from those feeds and store them using the same deduplication logic.

---

### Requirement 6: Sentiment Analysis

**User Story:** As a data analyst, I want news articles analyzed for sentiment using two algorithms, so that I get a robust, combined sentiment signal.

#### Acceptance Criteria

1. WHEN an article is submitted for analysis, THE Sentiment_Analyzer SHALL preprocess the text by removing HTML tags, special characters, and extra whitespace, and converting to lowercase.
2. THE Sentiment_Analyzer SHALL compute a TextBlob polarity score (range -1 to 1) and subjectivity score (range 0 to 1) for each article.
3. THE Sentiment_Analyzer SHALL compute a VADER compound score (range -1 to 1) and individual positive, neutral, and negative scores for each article.
4. THE Sentiment_Analyzer SHALL calculate a combined sentiment score as a weighted average of the TextBlob polarity and VADER compound scores, with configurable weights defaulting to 0.5 each.
5. THE Sentiment_Analyzer SHALL classify the combined score as `positive` (> 0.05), `negative` (< -0.05), or `neutral` (otherwise) and store the classification in the `sentiment_analysis` table.
6. WHEN daily aggregation is triggered for a symbol and date, THE Sentiment_Analyzer SHALL compute the average combined score, count articles per classification, and upsert a record in the `daily_sentiment` table.

---

### Requirement 7: LSTM Model Training

**User Story:** As a data scientist, I want to train an LSTM model locally on historical data, so that I can generate price predictions without depending on Azure ML.

#### Acceptance Criteria

1. WHEN the `train-model` CLI command is invoked for a symbol, THE Prediction_Service SHALL retrieve at least 60 days of stock and daily sentiment data from the DB.
2. THE Prediction_Service SHALL engineer the following 9 features per day: `open`, `high`, `low`, `close`, `volume`, `sentiment_score`, `sma_5`, `sma_20`, `volatility` (20-day rolling std of returns).
3. THE Prediction_Service SHALL normalize all features to the range [0, 1] using a MinMaxScaler and persist the fitted Scaler alongside the model.
4. THE Prediction_Service SHALL create input sequences of 60 consecutive days with the next day's closing price as the target, splitting data 80% training / 20% testing.
5. THE Prediction_Service SHALL build a sequential LSTM architecture: LSTM(50, return_sequences=True) → Dropout → LSTM(50) → Dense(25, relu) → Dense(1), compiled with Adam (lr=0.001) and MSE loss.
6. THE Prediction_Service SHALL train for 50 epochs with batch size 32 and save the trained model to `app/models/trained/{symbol}_lstm.keras`.
7. WHEN training completes, THE Prediction_Service SHALL evaluate the model on the test set and log the mean squared error and mean absolute error.

---

### Requirement 8: Price Prediction

**User Story:** As a trader, I want price predictions with confidence scores for a given stock symbol, so that I can make informed decisions.

#### Acceptance Criteria

1. WHEN the `predict` CLI command is invoked, THE Prediction_Service SHALL check for a trained LSTM_Model at `app/models/trained/{symbol}_lstm.keras` and load it if present.
2. IF no local LSTM_Model exists for the symbol, THEN THE Prediction_Service SHALL attempt to train one on demand before generating a prediction.
3. THE Prediction_Service SHALL retrieve the last 60 days of feature data, apply the persisted Scaler, and feed the normalized sequence into the LSTM_Model to produce a single-day price prediction.
4. WHEN multi-day prediction is requested, THE Prediction_Service SHALL iteratively use each predicted value as input for the next day, repeating for the specified number of days.
5. THE Prediction_Service SHALL calculate a confidence score between 0 and 1 based on recent prediction accuracy, sentiment volatility, and market volatility.
6. IF the Azure_ML_Client is configured and the local model is unavailable, THEN THE Prediction_Service SHALL send a POST request to the Azure ML endpoint with the prepared feature JSON and parse the response as the prediction.
7. THE Prediction_Service SHALL store each prediction in the `predictions` table with predicted price, confidence score, trend direction, and the model source (`local` or `azure`).

---

### Requirement 9: Azure ML Integration

**User Story:** As a system operator, I want the system to fall back to Azure ML for predictions when the local model is unavailable, so that predictions remain available during model transitions.

#### Acceptance Criteria

1. WHEN Azure ML endpoint URL and API key are configured, THE Azure_ML_Client SHALL send prediction requests as authenticated POST requests with feature data formatted as JSON.
2. IF the Azure ML endpoint returns an HTTP error or times out, THEN THE Azure_ML_Client SHALL log the error and signal the Prediction_Service to fall back to local prediction.
3. THE Azure_ML_Client SHALL validate that the response contains a numeric predicted price before returning it to the Prediction_Service.
4. WHEN the `sentiment-model.keras` file is placed in `app/models/trained/`, THE Prediction_Service SHALL detect and load it on the next prediction request without requiring a restart.

---

### Requirement 10: Agent Coordination (GPT-Nano)

**User Story:** As a user, I want to interact with the system in natural language, so that I can get predictions and analysis without knowing the underlying commands.

#### Acceptance Criteria

1. THE Agent SHALL initialize an AzureOpenAI client using the configured endpoint, API key, deployment name, and API version at startup.
2. WHEN a user query is received, THE Agent SHALL send it to GPT-Nano with a system prompt defining available tools and expected JSON response format for intent classification.
3. THE Agent SHALL recognize at least the following intent types: `get_prediction`, `analyze_sentiment`, `view_stock_data`, `compare_stocks`, `explain_trends`, and `general_question`.
4. WHEN an intent is recognized, THE Agent SHALL extract entities (stock symbols, timeframes, parameters) and select the appropriate tools and Nodes to fulfill the request.
5. THE Agent SHALL execute selected tools sequentially, passing outputs between steps, and synthesize a final natural-language response from the aggregated results.
6. IF GPT-Nano returns a malformed or unrecognized intent, THEN THE Agent SHALL default to `general_question` handling and ask the user for clarification.

---

### Requirement 11: Node-Based Processing Pipeline

**User Story:** As a developer, I want a composable node pipeline, so that processing flows can be assembled dynamically by the agent.

#### Acceptance Criteria

1. THE System SHALL define a `BaseNode` abstract class with `execute(inputs: dict) -> dict` interface that all Nodes implement.
2. THE System SHALL provide the following concrete Node types: `DataCollectionNode`, `PreprocessingNode`, `AnalysisNode`, `PredictionNode`, `AggregationNode`, and `OutputNode`.
3. WHEN the Agent constructs a Pipeline, THE System SHALL execute Nodes in the specified order, passing each Node's output dict as the next Node's input dict.
4. IF a Node raises an exception during execution, THEN THE System SHALL log the error with full context and halt the Pipeline, returning an error result to the Agent.
5. THE System SHALL allow the Agent to construct different Pipelines for different intents without code changes, using Node class references and configuration dicts.

---

### Requirement 12: Tool System

**User Story:** As a developer, I want a library of single-purpose tools callable by the agent, so that complex operations are composed from simple, testable units.

#### Acceptance Criteria

1. THE System SHALL provide stock data tools: `fetch_historical_data(symbol, start_date, end_date)`, `fetch_current_price(symbol)`, and `get_technical_indicators(symbol, date_range)`.
2. THE System SHALL provide sentiment tools: `analyze_article_sentiment(article_id)`, `get_daily_sentiment(symbol, date_range)`, and `compare_sentiment(symbols, date_range)`.
3. THE System SHALL provide prediction tools: `predict_price(symbol, horizon_days)`, `batch_predict(symbols)`, and `get_prediction_history(symbol)`.
4. THE System SHALL provide utility tools: `search_symbols(query)`, `format_response(data)`, and `validate_input(params, schema)`.
5. WHEN a tool is called with invalid parameters, THE System SHALL return a structured error dict rather than raising an unhandled exception.

---

### Requirement 13: Command-Line Interface

**User Story:** As a user, I want a CLI to interact with all system capabilities, so that I can run operations without writing Python code.

#### Acceptance Criteria

1. THE CLI SHALL provide the following commands via click: `run`, `train-model`, `collect-data`, `predict`, `analyze-sentiment`, and `backtest`.
2. WHEN `run` is invoked, THE CLI SHALL start an interactive loop that passes user input to the Agent and prints the response.
3. WHEN `train-model --symbol SYMBOL` is invoked, THE CLI SHALL call the Prediction_Service to train an LSTM_Model for the given symbol and print training metrics on completion.
4. WHEN `collect-data --symbols SYMBOL [SYMBOL ...]` is invoked, THE CLI SHALL trigger the Data_Collector for each symbol and print a summary of records inserted.
5. WHEN `predict --symbol SYMBOL --days N` is invoked, THE CLI SHALL call the Prediction_Service and print the predicted prices, trend, and confidence score for each day.
6. WHEN `analyze-sentiment --symbol SYMBOL` is invoked, THE CLI SHALL trigger sentiment analysis for recent articles and print the daily aggregated sentiment score.
7. WHEN `backtest --symbol SYMBOL` is invoked, THE CLI SHALL retrieve historical predictions and actual prices from the DB and print accuracy metrics (MAE, RMSE).

---

### Requirement 14: Logging

**User Story:** As a developer, I want structured, rotating logs, so that I can diagnose issues in both development and production.

#### Acceptance Criteria

1. THE System SHALL configure loguru at startup with console output (DEBUG level in development, INFO in production) and a rotating file sink with daily rotation and compression.
2. THE System SHALL log the start time, symbols, and record counts for every data collection run.
3. THE System SHALL log the article ID, combined sentiment score, and processing duration for every sentiment analysis operation.
4. THE System SHALL log the symbol, horizon, confidence score, and model source for every prediction generated.
5. IF an unhandled exception occurs, THEN THE System SHALL log the full stack trace with contextual metadata (user ID if available, operation name, input parameters) before propagating the error.

---

### Requirement 15: Testing

**User Story:** As a developer, I want unit and integration tests, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. THE System SHALL include pytest unit tests for Auth_Service covering password hashing, JWT generation, JWT verification, and session creation with mocked DB sessions.
2. THE System SHALL include pytest unit tests for Sentiment_Analyzer covering text preprocessing, TextBlob scoring, VADER scoring, combined score calculation, and daily aggregation.
3. THE System SHALL include pytest unit tests for Prediction_Service covering feature engineering, sequence creation, Scaler normalization, and confidence score calculation with synthetic data.
4. THE System SHALL include pytest integration tests for Data_Collector that mock external API responses and verify correct DB insertion and deduplication behavior.
5. THE System SHALL include a round-trip property test: FOR ALL valid `stock_data` records serialized to JSON and deserialized back, THE resulting record SHALL be equivalent to the original (round-trip property).
6. THE System SHALL include a pytest integration test for the Agent that sends a predefined query and verifies the correct intent type and tool selection are returned.
