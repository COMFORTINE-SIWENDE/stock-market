# Implementation Plan: NSE Market Adaptation

## Overview

This implementation plan adapts the Stock Market Prediction System to support the Nairobi Securities Exchange (NSE) alongside existing US market support. The system will maintain multi-market architecture with market-specific data sources, trading hours, currencies, and sentiment analysis for Kenyan financial news.

**Implementation Language**: Python

**Key Components**:
- Database schema extensions for multi-market support
- NSE symbol parser and validator
- Market detector and routing logic
- NSE data collectors (Yahoo Finance .NR, Alpha Vantage, CSV import)
- Timezone handler for EAT (UTC+3)
- Trading hours validator with NSE holidays
- Data quality validation pipeline
- Kenyan news collector and sentiment analyzer
- NSE prediction engine with LSTM model
- API endpoint modifications for multi-market support

## Tasks

- [ ] 1. Database schema migration for multi-market support
  - [x] 1.1 Create Alembic migration script for NSE support
    - Add `market`, `currency`, `base_symbol` columns to `stock_symbols` table
    - Add `market`, `currency` columns to `stock_data` table
    - Add `market`, `language` columns to `news_articles` table
    - Create `data_quality_metrics` table with indexes
    - Create `nse_holidays` table with date index
    - Add indexes on market columns for query performance
    - Set default values: market='US', currency='USD'
    - _Requirements: 1.4, 2.3, 5.1, 12.6_

  - [ ] 1.2 Run migration and verify schema changes
    - Execute `alembic upgrade head` in test environment
    - Verify all new columns exist with correct types
    - Verify indexes are created
    - Verify default values are applied to existing records
    - _Requirements: 1.4, 2.3_

  - [ ]* 1.3 Write unit tests for migration rollback
    - Test `alembic downgrade` removes new columns and tables
    - Verify data integrity after rollback
    - _Requirements: 1.4_

- [ ] 2. Implement core NSE data models and enums
  - [x] 2.1 Create MarketType enum and NSESymbol dataclass
    - Create `app/models/market.py` with `MarketType` enum (US, NSE)
    - Create `NSESymbol` dataclass with `base` and `suffix` fields
    - Implement `__str__` method for NSESymbol
    - _Requirements: 1.1, 8.1, 10.2_

  - [ ] 2.2 Update SQLModel classes with new fields
    - Modify `StockSymbol` model to include market, currency, base_symbol fields
    - Modify `StockData` model to include market, currency fields
    - Modify `NewsArticle` model to include market, language fields
    - Create `DataQualityMetrics` model
    - Create `NSEHoliday` model
    - _Requirements: 1.4, 2.3, 3.5, 12.6_

  - [ ] 2.3 Create OHLCVRecord and ValidationResult dataclasses
    - Create `app/models/ohlcv.py` with `OHLCVRecord` dataclass
    - Include symbol, date, open, high, low, close, volume, currency, market fields
    - Create `ValidationResult` dataclass with passed, errors, warnings fields
    - _Requirements: 2.1, 12.1_

  - [ ]* 2.4 Write property test for NSE symbol round-trip
    - **Property 1: NSE Symbol Round-Trip Preservation**
    - **Validates: Requirements 8.6**
    - Use hypothesis to generate valid base symbols (2-6 uppercase letters)
    - Test: parse(format(parse(symbol))) == parse(symbol)
    - _Requirements: 8.6_

- [ ] 3. Implement NSE symbol parser and validator
  - [ ] 3.1 Create NSESymbolParser class
    - Create `app/services/nse_symbol_parser.py`
    - Implement `parse(symbol: str) -> NSESymbol` method
    - Implement `validate(symbol: str) -> bool` method
    - Implement `format(base: str) -> str` method
    - Define `VALID_SYMBOLS` set with NSE 20 Index constituents
    - Handle symbols with and without .NR suffix
    - _Requirements: 1.1, 1.2, 1.5, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 3.2 Write unit tests for NSE 20 constituents
    - Test all NSE 20 symbols are valid: SCOM.NR, KCB.NR, EQTY.NR, EABL.NR, COOP.NR
    - Test invalid symbols raise ValueError with descriptive message
    - Test case-insensitive parsing
    - _Requirements: 1.3, 1.5, 8.4_

- [ ] 4. Implement market detector and routing
  - [ ] 4.1 Create MarketDetector class
    - Create `app/services/market_detector.py`
    - Implement `detect_market(symbol: str) -> MarketType` static method
    - Check for .NR suffix to identify NSE stocks
    - Default to US market if no suffix
    - Implement `normalize_symbol(symbol: str, market: MarketType) -> str` method
    - _Requirements: 10.2, 10.7_

  - [ ]* 4.2 Write unit tests for market detection
    - Test symbols with .NR detected as NSE
    - Test symbols without suffix detected as US
    - Test case sensitivity
    - Test edge cases (empty string, multiple dots)
    - _Requirements: 10.2_

- [ ] 5. Implement timezone handler for EAT
  - [ ] 5.1 Create TimezoneHandler class
    - Create `app/services/timezone_handler.py`
    - Define `EAT = timezone(timedelta(hours=3))` constant
    - Implement `to_eat(dt: datetime) -> datetime` static method
    - Implement `to_utc(dt: datetime) -> datetime` static method
    - Implement `now_eat() -> datetime` static method
    - Implement `format_eat(dt: datetime) -> str` method with timezone indicator
    - _Requirements: 6.1, 6.5, 6.6_

  - [ ]* 5.2 Write property test for timezone conversion bidirectionality
    - **Property 15: Timezone Conversion Bidirectionality**
    - **Validates: Requirements 6.6**
    - Use hypothesis to generate datetime values
    - Test: to_eat(to_utc(dt_eat)) == dt_eat
    - Test: to_utc(to_eat(dt_utc)) == dt_utc
    - _Requirements: 6.6_

  - [ ]* 5.3 Write unit tests for specific dates
    - Test daylight saving time transitions (EAT has no DST)
    - Test midnight conversions
    - Test leap year dates
    - _Requirements: 6.1, 6.6_

- [ ] 6. Implement trading hours validator with NSE holidays
  - [x] 6.1 Create NSE holidays configuration file
    - Create `config/nse_holidays.yaml` with 2024-2025 holidays
    - Include: New Year's Day, Good Friday, Labour Day, Madaraka Day, Mashujaa Day, Jamhuri Day, Christmas, Boxing Day
    - Format: date, name, is_recurring fields
    - _Requirements: 6.3, 13.2_

  - [ ] 6.2 Create TradingHoursValidator class
    - Create `app/services/trading_hours_validator.py`
    - Define `TRADING_START = time(9, 0)` and `TRADING_END = time(15, 0)` constants
    - Define `TRADING_DAYS = [0, 1, 2, 3, 4]` (Monday-Friday)
    - Implement `__init__(holidays_config: Path)` to load holidays from YAML
    - Implement `is_trading_hours(dt: datetime) -> bool` method
    - Implement `is_trading_day(dt: datetime) -> bool` method
    - Implement `is_market_open() -> bool` method
    - Implement `next_trading_day(dt: datetime) -> datetime` method
    - _Requirements: 2.4, 6.2, 6.3, 13.1, 13.2, 13.3_

  - [ ]* 6.3 Write property test for trading hours validation
    - **Property 4: Trading Hours Validation**
    - **Validates: Requirements 2.4, 6.2, 13.1**
    - Use hypothesis to generate datetime values
    - Test: is_trading_hours correctly identifies 9 AM - 3 PM EAT, Mon-Fri
    - Test: holidays are excluded
    - _Requirements: 2.4, 6.2, 13.1_

  - [ ]* 6.4 Write unit tests for specific holidays
    - Test known NSE holidays (2024-12-25 Christmas)
    - Test weekend detection
    - Test next_trading_day skips weekends and holidays
    - _Requirements: 6.3, 13.2_

- [ ] 7. Implement data quality validator
  - [ ] 7.1 Create DataQualityValidator class
    - Create `app/services/data_quality_validator.py`
    - Implement `__init__(metrics_tracker: MetricsTracker)` constructor
    - Implement `validate_ohlcv(record: OHLCVRecord) -> ValidationResult` method
    - Check: Low <= Open <= High, Low <= Close <= High
    - Check: All prices > 0, Volume >= 0
    - Implement `detect_outliers(current: OHLCVRecord, previous: Optional[OHLCVRecord]) -> bool` method
    - Check: price change < 50% from previous day
    - Implement `track_failure(symbol, source, error_type, details)` method
    - _Requirements: 2.8, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 7.2 Write property test for OHLCV constraints
    - **Property 5: OHLCV Data Quality Constraints**
    - **Validates: Requirements 2.8, 12.1, 12.2, 12.3**
    - Use hypothesis to generate OHLCV values
    - Test: validation passes when Low <= Open <= High and Low <= Close <= High
    - Test: validation fails when constraints violated
    - Test: Close > 0 and Volume >= 0
    - _Requirements: 2.8, 12.1, 12.2, 12.3_

  - [ ]* 7.3 Write unit tests for edge cases
    - Test zero prices rejection
    - Test negative volume rejection
    - Test exact 50% price change (boundary)
    - _Requirements: 12.2, 12.3, 12.4_

- [ ] 8. Checkpoint - Verify core infrastructure
  - Ensure all tests pass for models, parsers, validators
  - Verify database migration applied successfully
  - Ask the user if questions arise


- [ ] 9. Implement NSE data collectors
  - [ ] 9.1 Create YahooFinanceNSE adapter
    - Create `app/services/data_sources/yahoo_finance_nse.py`
    - Implement `fetch(symbol: str, start: date, end: date) -> List[OHLCVRecord]` method
    - Use yfinance library with .NR suffix symbols
    - Convert data to OHLCVRecord format with market="NSE", currency="KES"
    - Handle API errors and return empty list on failure
    - _Requirements: 2.1, 2.2, 2.3, 7.3_

  - [ ] 9.2 Create AlphaVantageNSE adapter
    - Create `app/services/data_sources/alpha_vantage_nse.py`
    - Implement `fetch(symbol: str, start: date, end: date) -> List[OHLCVRecord]` method
    - Use Alpha Vantage TIME_SERIES_DAILY function
    - Convert data to OHLCVRecord format with market="NSE", currency="KES"
    - Handle API rate limiting and errors
    - _Requirements: 2.1, 2.2, 2.3, 7.3_

  - [ ] 9.3 Create CSVImporter for manual data
    - Create `app/services/data_sources/csv_importer.py`
    - Implement `import_file(filepath: Path, symbol: str) -> List[OHLCVRecord]` method
    - Expected CSV columns: date, open, high, low, close, volume
    - Validate CSV structure and data types
    - Convert to OHLCVRecord format
    - _Requirements: 2.1, 7.3_

  - [ ] 9.4 Create NSEDataCollector with fallback logic
    - Create `app/services/nse_data_collector.py`
    - Implement `__init__(config: NSEDataSourceConfig)` with primary/fallback sources
    - Implement `fetch_historical(symbol, start_date, end_date) -> List[OHLCVRecord]` method
    - Try primary source (Yahoo Finance), fallback to Alpha Vantage, then CSV
    - Log source used for each successful fetch
    - Implement `fetch_current_price(symbol: str) -> float` method
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 7.2, 7.3, 7.4_

  - [ ]* 9.5 Write property test for currency consistency
    - **Property 3: Currency Consistency for NSE Stocks**
    - **Validates: Requirements 2.3, 5.1, 5.2**
    - Test: all NSE stock records have currency="KES"
    - Test: predictions for NSE stocks are in KES
    - _Requirements: 2.3, 5.1, 5.2_

  - [ ]* 9.6 Write unit tests for data source fallback
    - Mock Yahoo Finance failure, verify Alpha Vantage called
    - Mock both failures, verify CSV importer called
    - Test DataSourceError raised when all sources fail
    - _Requirements: 7.2, 7.4_

- [ ] 10. Implement NSE data collection service with validation
  - [ ] 10.1 Modify data_service.py for multi-market support
    - Update `collect_stock_data` function to detect market type
    - Route NSE symbols to NSEDataCollector
    - Apply DataQualityValidator to all collected records
    - Apply TradingHoursValidator for NSE stocks
    - Deduplicate by (symbol_id, date) before insertion
    - Store records with market and currency fields
    - Handle validation failures by logging and skipping invalid records
    - _Requirements: 1.4, 2.3, 2.4, 2.6, 2.7, 10.3, 10.6, 12.5_

  - [ ]* 10.2 Write property test for deduplication idempotence
    - **Property 6: Stock Data Deduplication Idempotence**
    - **Validates: Requirements 2.6**
    - Test: inserting same (symbol_id, date) multiple times results in one record
    - Use hypothesis to generate duplicate records
    - _Requirements: 2.6_

  - [ ]* 10.3 Write property test for market identifier consistency
    - **Property 2: Market Identifier Consistency**
    - **Validates: Requirements 1.4**
    - Test: all NSE symbols in database have market="NSE"
    - Test: all US symbols have market="US"
    - _Requirements: 1.4_

  - [ ]* 10.4 Write integration test for end-to-end data collection
    - Test collecting NSE data from Yahoo Finance (with test symbol)
    - Verify data stored in database with correct market and currency
    - Verify validation applied
    - _Requirements: 2.1, 2.3, 2.6, 12.1_

- [ ] 11. Implement Kenyan news source configuration
  - [x] 11.1 Create Kenyan news sources configuration file
    - Create `config/kenyan_news_sources.yaml`
    - Add Business Daily RSS feed
    - Add The Nation Business RSS feed
    - Add The Standard Business RSS feed
    - Add Capital FM Business RSS feed
    - Include name, type (rss/api), url, enabled status for each source
    - _Requirements: 3.1, 3.2, 3.3, 11.1, 11.2_

  - [ ] 11.2 Create NewsSourceConfig parser
    - Create `app/config/news_source_config.py`
    - Implement `load(config_path: Path) -> NewsSourceConfig` method
    - Parse YAML structure with validation
    - Implement `validate()` method to check required fields
    - Implement `to_yaml() -> str` method for serialization
    - Handle invalid config by logging errors and using defaults
    - _Requirements: 11.2, 11.3, 11.4, 11.5_

  - [ ]* 11.3 Write unit tests for config parsing
    - Test valid YAML parsing
    - Test invalid YAML handling
    - Test missing fields handling
    - Test config reload without restart
    - _Requirements: 11.3, 11.4, 11.7_

- [ ] 12. Implement Kenyan news collector
  - [ ] 12.1 Create RSSParser for Kenyan news feeds
    - Create `app/services/news_sources/rss_parser.py`
    - Implement `parse_feed(feed_url: str) -> List[NewsArticle]` method
    - Use feedparser library
    - Extract title, content, url, published_at from RSS entries
    - Handle parsing errors gracefully
    - _Requirements: 3.2_

  - [ ] 12.2 Create KenyanNewsCollector class
    - Create `app/services/kenyan_news_collector.py`
    - Implement `__init__(config: NewsSourceConfig)` to load sources
    - Implement `collect_news(symbol: str, hours_back: int = 24) -> List[NewsArticle]` method
    - Implement `collect_from_rss(feed_url: str, symbol: str) -> List[NewsArticle]` method
    - Filter articles mentioning symbol or company name
    - Deduplicate by URL
    - Filter by time window (hours_back)
    - Set market="NSE", language="en" for all articles
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 12.3 Write property test for news deduplication
    - **Property 7: News Article Deduplication Idempotence**
    - **Validates: Requirements 3.6**
    - Test: inserting same URL multiple times results in one article
    - Use hypothesis to generate duplicate articles
    - _Requirements: 3.6_

  - [ ]* 12.4 Write property test for time window filtering
    - **Property 8: News Article Time Window Filtering**
    - **Validates: Requirements 3.7**
    - Test: all returned articles within specified time window
    - Use hypothesis to generate articles with various timestamps
    - _Requirements: 3.7_

  - [ ]* 12.5 Write property test for symbol filtering
    - **Property 9: News Article Symbol Filtering**
    - **Validates: Requirements 3.4**
    - Test: all returned articles mention symbol or company name
    - _Requirements: 3.4_

  - [ ]* 12.6 Write property test for source attribution
    - **Property 10: News Source Attribution Preservation**
    - **Validates: Requirements 3.5**
    - Test: stored article has source field matching originating source
    - _Requirements: 3.5_

  - [ ]* 12.7 Write unit tests for RSS parsing
    - Test parsing valid RSS feed
    - Test handling malformed RSS
    - Test empty feed handling
    - _Requirements: 3.2_

- [ ] 13. Implement Kenyan sentiment analyzer
  - [ ] 13.1 Create Kenyan financial lexicon
    - Create `app/config/kenyan_financial_lexicon.py`
    - Define `KENYAN_FINANCIAL_TERMS` dictionary with sentiment scores
    - Include positive terms: "m-pesa", "shilling strengthens", "bourse gains", "nse rallies"
    - Include negative terms: "shilling weakens", "bourse declines", "nse drops"
    - Include neutral terms: "nse trading", "nairobi bourse", "central bank"
    - _Requirements: 4.4, 4.5_

  - [ ] 13.2 Create KenyanSentimentAnalyzer class
    - Create `app/services/kenyan_sentiment_analyzer.py`
    - Implement `__init__()` to load TextBlob and VADER analyzers
    - Implement `analyze(article: NewsArticle) -> SentimentScore` method
    - Combine TextBlob and VADER scores
    - Implement `_adjust_for_kenyan_context(text: str, base_score: float) -> float` method
    - Apply Kenyan lexicon adjustments to base sentiment score
    - Classify sentiment as positive/neutral/negative based on thresholds
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

  - [ ] 13.3 Implement daily sentiment aggregation
    - Create `app/services/sentiment_aggregator.py`
    - Implement `aggregate_daily(symbol: str, date: date, session: Session) -> DailySentiment` method
    - Compute average sentiment score for the day
    - Count total articles analyzed
    - Calculate sentiment distribution (positive/neutral/negative percentages)
    - Store with EAT timezone
    - _Requirements: 4.3, 4.6_

  - [ ]* 13.4 Write property test for sentiment score bounds
    - **Property 11: Sentiment Score Bounds**
    - **Validates: Requirements 4.7**
    - Use hypothesis to generate article text
    - Test: sentiment score always between -1.0 and 1.0
    - _Requirements: 4.7_

  - [ ]* 13.5 Write property test for sentiment classification consistency
    - **Property 12: Sentiment Classification Consistency**
    - **Validates: Requirements 4.2**
    - Test: classification matches score based on thresholds
    - Test: score > 0.1 → positive, score < -0.1 → negative, else neutral
    - _Requirements: 4.2_

  - [ ]* 13.6 Write property test for daily aggregation correctness
    - **Property 13: Daily Sentiment Aggregation Correctness**
    - **Validates: Requirements 4.3**
    - Use hypothesis to generate sets of sentiment scores
    - Test: average, count, distribution calculated correctly
    - _Requirements: 4.3_

  - [ ]* 13.7 Write unit tests for Kenyan context adjustment
    - Test "M-Pesa" increases Safaricom sentiment
    - Test "shilling weakens" decreases sentiment
    - Test neutral terms don't change sentiment
    - _Requirements: 4.4, 4.5_

- [ ] 14. Checkpoint - Verify news and sentiment pipeline
  - Ensure all tests pass for news collection and sentiment analysis
  - Verify Kenyan news sources configuration loaded correctly
  - Test end-to-end: collect news → analyze sentiment → aggregate daily
  - Ask the user if questions arise


- [ ] 15. Implement NSE prediction engine
  - [ ] 15.1 Create NSEFeatureEngineer class
    - Create `app/services/nse_feature_engineer.py`
    - Implement `engineer_features(symbol: str, session: Session) -> pd.DataFrame` method
    - Extract OHLCV data from database
    - Calculate SMA-5 and SMA-20
    - Calculate 20-day rolling volatility
    - Join with daily sentiment scores
    - Add day of week and month features
    - Handle missing sentiment data (fill with neutral 0.0)
    - _Requirements: 9.2, 9.3_

  - [ ] 15.2 Create NSEPredictionEngine class
    - Create `app/services/nse_prediction_engine.py`
    - Implement `__init__(model_dir: Path)` constructor
    - Implement `train_model(symbol: str, min_days: int = 365) -> TrainingResult` method
    - Check for minimum 365 days of data, raise InsufficientDataError if not met
    - Use NSEFeatureEngineer to prepare features
    - Train LSTM model with same architecture as US stocks
    - Save model to `{model_dir}/{symbol}_lstm.keras`
    - Save scaler to `{model_dir}/{symbol}_scaler.joblib`
    - Calculate MAE and verify < 5% of average price
    - Implement `predict(symbol: str, horizons: List[int] = [1, 5, 30]) -> List[Prediction]` method
    - Load trained model and scaler
    - Generate predictions for 1, 5, 30 days ahead
    - Return predictions in KES currency
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [ ]* 15.3 Write unit tests for insufficient data handling
    - Test InsufficientDataError raised when < 365 days
    - Test error message includes required vs available days
    - _Requirements: 9.7_

  - [ ]* 15.4 Write integration test for model training
    - Test training with 365+ days of NSE data
    - Verify model and scaler files created
    - Verify MAE within 5% threshold
    - _Requirements: 9.1, 9.6_

- [ ] 16. Implement NSE data backfill functionality
  - [ ] 16.1 Create BackfillService class
    - Create `app/services/backfill_service.py`
    - Implement `backfill_historical(symbols: List[str], start_date: date, end_date: date, session: Session) -> BackfillResult` method
    - Iterate through symbols and date ranges
    - Use NSEDataCollector with exponential backoff for rate limiting
    - Apply DataQualityValidator to all backfilled data
    - Track progress and log every 100 records
    - Support resume from last successful date if interrupted
    - Return summary with total records collected per symbol
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [ ]* 16.2 Write unit tests for backfill resume
    - Test resume from last successful date after interruption
    - Test progress logging
    - Test rate limiting with exponential backoff
    - _Requirements: 15.3, 15.4, 15.5_

  - [ ]* 16.3 Write integration test for multi-symbol backfill
    - Test backfilling multiple NSE symbols
    - Verify summary includes all symbols
    - Verify data stored correctly
    - _Requirements: 15.2, 15.6_

- [ ] 17. Implement API endpoints for NSE support
  - [ ] 17.1 Create NSE market status endpoint
    - Add `GET /api/v1/market/nse/status` endpoint in `app/server.py`
    - Return MarketStatusResponse with is_open, current_time_eat, trading_hours
    - Use TradingHoursValidator to check market status
    - Include next_open time if market closed
    - _Requirements: 13.5, 13.6_

  - [ ] 17.2 Create stock search endpoint
    - Add `GET /api/v1/stocks/search` endpoint
    - Accept query parameter `q` (search term)
    - Accept optional `market` filter (US or NSE)
    - Accept optional `limit` parameter (default 20, max 100)
    - Search by symbol or company name (case-insensitive)
    - Order by relevance: exact matches first, then partial
    - Include market identifier and featured flag for NSE 20
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [ ] 17.3 Create data quality metrics endpoint
    - Add `GET /api/v1/data-quality/metrics` endpoint
    - Accept optional `symbol`, `market`, `days` parameters
    - Query DataQualityMetrics table
    - Aggregate by error_type and source
    - Return total failures and breakdowns
    - _Requirements: 12.7_

  - [ ] 17.4 Create backfill endpoint
    - Add `POST /api/v1/data/backfill` endpoint
    - Accept BackfillRequest with symbols, start_date, end_date
    - Validate NSE symbols using NSESymbolParser
    - Run backfill in background task
    - Return task_id for tracking
    - _Requirements: 15.1, 15.2_

  - [ ] 17.5 Modify stock data collection endpoint
    - Update `POST /api/v1/data/collect` endpoint
    - Use MarketDetector to detect market from symbol
    - Route to NSEDataCollector for NSE symbols
    - Apply TradingHoursValidator for NSE stocks
    - Return market type in response
    - _Requirements: 2.4, 10.3, 10.7_

  - [ ]* 17.6 Write integration tests for API endpoints
    - Test market status endpoint returns correct status
    - Test search endpoint with various queries
    - Test data quality metrics endpoint
    - Test backfill endpoint creates background task
    - Test modified collection endpoint routes correctly
    - _Requirements: 10.3, 12.7, 13.5, 14.1, 15.1_

- [ ] 18. Implement KES price formatting
  - [ ] 18.1 Create PriceFormatter utility
    - Create `app/utils/price_formatter.py`
    - Implement `format_kes(amount: float) -> str` function
    - Format with exactly 2 decimal places
    - Include "KES" currency label
    - Handle None and zero values
    - _Requirements: 5.3, 5.4_

  - [ ] 18.2 Update API responses to use PriceFormatter
    - Modify stock data endpoints to format NSE prices
    - Modify prediction endpoints to format NSE predictions
    - Ensure US prices still formatted with USD
    - _Requirements: 5.3, 5.4_

  - [ ]* 18.3 Write unit tests for price formatting
    - Test formatting with 2 decimal places
    - Test KES label inclusion
    - Test zero amount formatting
    - Test very large amounts
    - _Requirements: 5.3, 5.4_

- [ ] 19. Update scheduler for NSE data collection
  - [ ] 19.1 Modify scheduler to support multi-market
    - Update `app/services/scheduler.py`
    - Add NSE symbols to scheduled collection
    - Use TradingHoursValidator to check NSE market hours
    - Skip NSE collection outside trading hours and on holidays
    - Schedule NSE news collection every 6 hours
    - Schedule NSE sentiment analysis after news collection
    - _Requirements: 2.4, 6.2, 6.3, 10.6_

  - [ ]* 19.2 Write unit tests for scheduler logic
    - Test NSE collection skipped outside trading hours
    - Test NSE collection skipped on holidays
    - Test news collection scheduled correctly
    - _Requirements: 2.4, 6.3_

- [ ] 20. Update existing US pipeline for backward compatibility
  - [ ] 20.1 Verify US stock functionality unchanged
    - Test existing US stock data collection still works
    - Test existing US sentiment analysis still works
    - Test existing US predictions still work
    - Verify US stocks have market="US" and currency="USD"
    - _Requirements: 10.6_

  - [ ] 20.2 Add market filter to existing endpoints
    - Update stock list endpoint to support market filter
    - Update prediction endpoint to support market filter
    - Update sentiment endpoint to support market filter
    - _Requirements: 10.5_

  - [ ]* 20.3 Write integration tests for backward compatibility
    - Test US stock end-to-end flow unchanged
    - Test mixed US and NSE stock queries
    - Test market filtering works correctly
    - _Requirements: 10.6_

- [ ] 21. Final checkpoint and integration testing
  - Ensure all unit tests pass
  - Ensure all property tests pass
  - Run end-to-end integration tests for NSE pipeline
  - Run end-to-end integration tests for US pipeline (backward compatibility)
  - Test multi-market scenarios (US and NSE together)
  - Verify database schema migration successful
  - Verify all API endpoints working correctly
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- The implementation uses Python as specified in the design document
- Database migration must be run before implementing data collection
- Configuration files (holidays, news sources) must be created before their respective services
- Data quality validation is applied at ingestion time for all NSE data
- Backward compatibility with US stocks is maintained throughout


## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "2.1", "6.1", "11.1"]
    },
    {
      "id": 1,
      "tasks": ["1.2", "2.2", "2.3", "3.1", "4.1", "5.1", "11.2"]
    },
    {
      "id": 2,
      "tasks": ["1.3", "2.4", "3.2", "4.2", "5.2", "5.3", "6.2", "7.1", "11.3"]
    },
    {
      "id": 3,
      "tasks": ["6.3", "6.4", "7.2", "7.3", "9.1", "9.2", "9.3", "12.1", "13.1"]
    },
    {
      "id": 4,
      "tasks": ["9.4", "12.2", "13.2", "13.3"]
    },
    {
      "id": 5,
      "tasks": ["9.5", "9.6", "10.1", "12.3", "12.4", "12.5", "12.6", "12.7", "13.4", "13.5", "13.6", "13.7"]
    },
    {
      "id": 6,
      "tasks": ["10.2", "10.3", "10.4", "15.1"]
    },
    {
      "id": 7,
      "tasks": ["15.2", "16.1", "18.1"]
    },
    {
      "id": 8,
      "tasks": ["15.3", "15.4", "16.2", "16.3", "17.1", "17.2", "17.3", "17.4", "17.5", "18.2", "19.1"]
    },
    {
      "id": 9,
      "tasks": ["17.6", "18.3", "19.2", "20.1", "20.2"]
    },
    {
      "id": 10,
      "tasks": ["20.3"]
    }
  ]
}
```
