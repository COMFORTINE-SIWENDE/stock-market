# Requirements Document

## Introduction

This document specifies the requirements for adapting the existing Stock Market Prediction System to support the Kenyan market, specifically the Nairobi Securities Exchange (NSE). The system currently supports US stocks (AAPL, MSFT, GOOGL, TSLA) using Yahoo Finance data. The adaptation will enable the system to collect NSE trading data, analyze Kenyan financial news sentiment, and generate predictions for NSE stocks including the NSE 20 Index constituents (Safaricom, KCB Group, Equity Group, EABL, Co-op Bank).

## Glossary

- **NSE**: Nairobi Securities Exchange - Kenya's principal stock exchange
- **NSE_20_Index**: The top 20 most actively traded stocks on the NSE
- **Data_Pipeline**: The system component responsible for collecting and storing stock market data
- **Sentiment_Engine**: The system component that analyzes financial news and social media to determine market sentiment
- **Prediction_Model**: The LSTM-based machine learning model that forecasts stock prices
- **Stock_Symbol**: A unique identifier for a traded security (e.g., SCOM.NR for Safaricom)
- **Trading_Hours**: The period during which the NSE is open for trading (9:00 AM - 3:00 PM EAT, Monday-Friday)
- **KES**: Kenyan Shillings - the currency used for NSE stock prices
- **Data_Source**: External service or API providing stock market or news data
- **Yahoo_Finance**: Current data source for US stock market data
- **Kenyan_News_Source**: Local Kenyan media outlets providing financial news (Business Daily, Nation, Standard, etc.)
- **Market_Data_Record**: A single data point containing OHLCV (Open, High, Low, Close, Volume) information for a stock on a specific date
- **News_Article**: A piece of financial news content with title, content, source, and publication date
- **Sentiment_Score**: A numerical value representing the positive, neutral, or negative sentiment of a news article
- **EAT**: East Africa Time - the timezone used by the NSE (UTC+3)
- **Pretty_Printer**: A component that formats data structures into human-readable text format

## Requirements

### Requirement 1: NSE Stock Symbol Support

**User Story:** As a system administrator, I want the system to support NSE stock symbols, so that users can track and predict Kenyan stocks.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL accept NSE stock symbols in the format "SYMBOL.NR" (e.g., SCOM.NR, KCB.NR)
2. THE Data_Pipeline SHALL validate NSE stock symbols against a configurable list of valid NSE symbols
3. WHEN an invalid NSE stock symbol is provided, THE Data_Pipeline SHALL return a descriptive error message
4. THE Data_Pipeline SHALL store NSE stock symbols in the StockSymbol table with a market identifier field set to "NSE"
5. THE Data_Pipeline SHALL support at minimum the NSE 20 Index constituents: Safaricom (SCOM.NR), KCB Group (KCB.NR), Equity Group (EQTY.NR), EABL (EABL.NR), and Co-op Bank (COOP.NR)

### Requirement 2: NSE Market Data Collection

**User Story:** As a system administrator, I want to collect historical and real-time trading data for NSE stocks, so that the prediction model has accurate input data.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL fetch historical OHLCV data for NSE stocks from available data sources
2. WHEN Yahoo Finance does not provide NSE data, THE Data_Pipeline SHALL use alternative data sources for NSE stocks
3. THE Data_Pipeline SHALL store NSE stock prices in KES currency
4. THE Data_Pipeline SHALL collect data only during NSE trading hours (9:00 AM - 3:00 PM EAT, Monday-Friday)
5. WHEN collecting data outside trading hours, THE Data_Pipeline SHALL fetch the most recent available closing price
6. THE Data_Pipeline SHALL deduplicate Market_Data_Records by (symbol_id, date) to prevent duplicate entries
7. THE Data_Pipeline SHALL handle missing or incomplete data by logging warnings and continuing with available data
8. FOR ALL Market_Data_Records collected, the close price SHALL be greater than zero and volume SHALL be non-negative

### Requirement 3: Kenyan News Source Integration

**User Story:** As a data analyst, I want the system to collect financial news from Kenyan media sources, so that sentiment analysis reflects local market conditions.

#### Acceptance Criteria

1. THE Sentiment_Engine SHALL collect news articles from Kenyan_News_Sources including Business Daily, The Nation, The Standard, and Capital FM Business
2. THE Sentiment_Engine SHALL support RSS feed parsing for Kenyan_News_Sources
3. WHEN a Kenyan_News_Source provides an API, THE Sentiment_Engine SHALL use the API for data collection
4. THE Sentiment_Engine SHALL filter news articles to include only those mentioning NSE stock symbols or company names
5. THE Sentiment_Engine SHALL store News_Articles with source attribution to the Kenyan_News_Source
6. THE Sentiment_Engine SHALL deduplicate News_Articles by URL to prevent duplicate analysis
7. THE Sentiment_Engine SHALL collect news articles published within a configurable time window (default 24 hours)

### Requirement 4: Kenyan Market Sentiment Analysis

**User Story:** As a trader, I want sentiment analysis to reflect Kenyan market sentiment, so that predictions account for local market conditions.

#### Acceptance Criteria

1. THE Sentiment_Engine SHALL analyze News_Articles from Kenyan_News_Sources to generate Sentiment_Scores
2. THE Sentiment_Engine SHALL classify sentiment as positive, neutral, or negative based on Sentiment_Score thresholds
3. THE Sentiment_Engine SHALL aggregate daily sentiment by computing average Sentiment_Score, article count, and sentiment distribution
4. THE Sentiment_Engine SHALL handle Kenyan English language variations and local financial terminology
5. WHEN analyzing sentiment, THE Sentiment_Engine SHALL consider context-specific terms like "Safaricom M-Pesa", "NSE trading", "Nairobi bourse"
6. THE Sentiment_Engine SHALL store sentiment analysis results with timestamps in EAT timezone
7. FOR ALL News_Articles analyzed, the Sentiment_Score SHALL be between -1.0 and 1.0 inclusive

### Requirement 5: Currency Conversion to KES

**User Story:** As a user, I want all NSE stock prices displayed in Kenyan Shillings, so that I can understand prices in the local currency.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL store all NSE stock prices in KES currency
2. THE Prediction_Model SHALL generate price predictions in KES for NSE stocks
3. THE system SHALL display all NSE stock prices with the "KES" currency label
4. WHEN displaying prices, THE system SHALL format KES amounts with two decimal places
5. THE system SHALL not perform currency conversion for NSE stocks (data is already in KES)

### Requirement 6: NSE Trading Hours and Timezone Support

**User Story:** As a system administrator, I want the system to respect NSE trading hours and use EAT timezone, so that data collection and predictions align with market operations.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL use EAT (UTC+3) timezone for all NSE-related timestamps
2. THE Data_Pipeline SHALL recognize NSE trading hours as 9:00 AM - 3:00 PM EAT, Monday through Friday
3. THE Data_Pipeline SHALL recognize NSE holidays and skip data collection on those days
4. WHEN the current time is outside trading hours, THE Data_Pipeline SHALL fetch the most recent closing price
5. THE system SHALL display all NSE timestamps in EAT timezone with clear timezone indication
6. THE Data_Pipeline SHALL handle timezone conversion correctly when comparing NSE data with system time

### Requirement 7: NSE Data Source Configuration

**User Story:** As a system administrator, I want to configure data sources for NSE stocks, so that the system can adapt to available data providers.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL support configurable data sources for NSE stocks via environment variables or configuration files
2. THE Data_Pipeline SHALL attempt primary data source first, then fall back to secondary sources if primary fails
3. THE Data_Pipeline SHALL support at minimum: Yahoo Finance (with .NR suffix), Alpha Vantage, and custom CSV file import
4. WHEN all configured data sources fail, THE Data_Pipeline SHALL log an error and return an empty result set
5. THE Data_Pipeline SHALL validate data source responses for completeness and data quality
6. THE system SHALL allow administrators to add new data sources without code changes through configuration

### Requirement 8: NSE Stock Symbol Parser

**User Story:** As a developer, I want a parser for NSE stock symbols, so that the system can correctly interpret and validate symbol formats.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL parse NSE stock symbols in the format "SYMBOL.NR"
2. WHEN a stock symbol is provided without the ".NR" suffix, THE Data_Pipeline SHALL append ".NR" for NSE stocks
3. THE Data_Pipeline SHALL extract the base symbol (e.g., "SCOM" from "SCOM.NR") for display purposes
4. THE Parser SHALL validate that the base symbol contains only uppercase letters and is 2-6 characters long
5. THE Pretty_Printer SHALL format NSE stock symbols consistently as "SYMBOL.NR" in all outputs
6. FOR ALL valid NSE stock symbols, parsing then printing then parsing SHALL produce an equivalent symbol (round-trip property)

### Requirement 9: NSE Prediction Model Adaptation

**User Story:** As a data scientist, I want the LSTM prediction model to work with NSE stock data, so that predictions are accurate for the Kenyan market.

#### Acceptance Criteria

1. THE Prediction_Model SHALL train on NSE historical data with minimum 365 days of trading data
2. THE Prediction_Model SHALL incorporate NSE-specific technical indicators (SMA-5, SMA-20, volatility)
3. THE Prediction_Model SHALL combine NSE stock price data with Kenyan market sentiment scores
4. THE Prediction_Model SHALL generate predictions for 1, 5, and 30 days ahead for NSE stocks
5. THE Prediction_Model SHALL store trained models separately for each NSE stock symbol
6. THE Prediction_Model SHALL achieve mean absolute error (MAE) within 5% of actual prices on validation data
7. WHEN insufficient training data is available, THE Prediction_Model SHALL return an error indicating minimum data requirements

### Requirement 10: Multi-Market Support

**User Story:** As a user, I want the system to support both US and NSE markets simultaneously, so that I can track stocks from both markets.

#### Acceptance Criteria

1. THE system SHALL maintain separate data pipelines for US stocks and NSE stocks
2. THE system SHALL identify market type (US or NSE) based on stock symbol format
3. THE system SHALL route data collection requests to the appropriate market-specific pipeline
4. THE system SHALL display market identifier (US or NSE) alongside stock symbols in the user interface
5. THE system SHALL allow users to filter stocks by market in the user interface
6. THE system SHALL maintain backward compatibility with existing US stock functionality
7. WHEN a user requests data for a stock symbol, THE system SHALL automatically detect the market and use appropriate data sources

### Requirement 11: NSE News Source Configuration Parser

**User Story:** As a system administrator, I want to configure Kenyan news sources through a configuration file, so that I can easily add or modify news sources.

#### Acceptance Criteria

1. THE Sentiment_Engine SHALL read Kenyan news source configurations from a JSON or YAML configuration file
2. THE configuration file SHALL specify for each source: name, type (RSS/API), URL, and enabled status
3. THE Parser SHALL validate the configuration file structure on system startup
4. WHEN the configuration file is invalid, THE Parser SHALL log descriptive errors and use default sources
5. THE Pretty_Printer SHALL format news source configurations into valid JSON/YAML format
6. FOR ALL valid news source configurations, parsing then printing then parsing SHALL produce an equivalent configuration (round-trip property)
7. THE system SHALL reload news source configuration without restart when configuration file changes

### Requirement 12: NSE Data Quality Validation

**User Story:** As a data analyst, I want the system to validate NSE data quality, so that predictions are based on reliable data.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL validate that OHLCV data follows the constraint: Low ≤ Open ≤ High, Low ≤ Close ≤ High
2. THE Data_Pipeline SHALL reject Market_Data_Records with zero or negative prices
3. THE Data_Pipeline SHALL reject Market_Data_Records with negative volume
4. THE Data_Pipeline SHALL detect and flag outliers where price changes exceed 50% in a single day
5. WHEN invalid data is detected, THE Data_Pipeline SHALL log a warning with details and skip the invalid record
6. THE Data_Pipeline SHALL maintain a data quality metrics table tracking validation failures by source and symbol
7. THE system SHALL provide an API endpoint to retrieve data quality metrics for monitoring

### Requirement 13: NSE Market Hours Validator

**User Story:** As a system administrator, I want the system to validate operations against NSE market hours, so that data collection occurs at appropriate times.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL validate that the current time is within NSE trading hours before attempting real-time data collection
2. THE Data_Pipeline SHALL maintain a configurable list of NSE public holidays
3. WHEN the current date is an NSE holiday, THE Data_Pipeline SHALL skip data collection and log an informational message
4. THE Data_Pipeline SHALL allow manual override of market hours validation for historical data collection
5. THE system SHALL provide an API endpoint to check if the NSE market is currently open
6. THE system SHALL display market status (Open/Closed) in the user interface for NSE stocks

### Requirement 14: NSE Stock Search and Discovery

**User Story:** As a user, I want to search for NSE stocks by company name or symbol, so that I can easily find stocks to track.

#### Acceptance Criteria

1. THE system SHALL provide a search endpoint that accepts partial company names or stock symbols
2. THE system SHALL return matching NSE stocks with symbol, company name, and market identifier
3. THE system SHALL support case-insensitive search for NSE stock symbols and company names
4. THE system SHALL rank search results by relevance (exact matches first, then partial matches)
5. THE system SHALL limit search results to a maximum of 20 matches
6. WHEN no matches are found, THE system SHALL return an empty result set with a descriptive message
7. THE system SHALL include NSE 20 Index constituents in search results with a "featured" indicator

### Requirement 15: NSE Historical Data Backfill

**User Story:** As a system administrator, I want to backfill historical NSE data, so that the prediction model has sufficient training data.

#### Acceptance Criteria

1. THE Data_Pipeline SHALL provide a backfill operation that collects historical data for a specified date range
2. THE Data_Pipeline SHALL support backfilling data for multiple NSE stocks in a single operation
3. THE Data_Pipeline SHALL handle rate limiting from data sources by implementing exponential backoff retry logic
4. THE Data_Pipeline SHALL resume backfill operations from the last successful date if interrupted
5. THE Data_Pipeline SHALL log progress during backfill operations (e.g., "Collected 100/365 days for SCOM.NR")
6. WHEN backfill completes, THE Data_Pipeline SHALL return a summary with total records collected per symbol
7. THE Data_Pipeline SHALL validate backfilled data using the same quality checks as real-time data collection
