# Requirements Document

## Introduction

MarketMind AI is a pure vanilla HTML/CSS/JavaScript single-page application (SPA) that provides
sentiment-powered stock price predictions. The frontend communicates with a Python aiohttp backend
running at `http://localhost:8000` and presents a dark glassmorphism UI (Inter font, Font Awesome
icons, Chart.js visualisations). Users can browse stocks, view AI-generated price predictions,
explore sentiment analysis, manage their account, and query a natural-language AI agent — all
without any JavaScript framework.

---

## Glossary

- **App**: The MarketMind AI frontend SPA (`index.html` entry point).
- **Router**: The hash-based client-side routing module (`js/app.js`).
- **API_Client**: The HTTP communication module (`js/api.js`) that calls the backend.
- **Auth_Module**: The authentication module (`js/auth.js`) that manages JWT tokens.
- **AppState**: The central in-memory state object (`js/state.js`) shared across all pages.
- **Dashboard_Page**: The main landing page after login (`pages/dashboard.html` + `js/dashboard.js`).
- **Predictions_Page**: The price-prediction page (`pages/predictions.html` + `js/predictions.js`).
- **Sentiment_Page**: The sentiment analysis page (`pages/sentiment.html` + `js/sentiment.js`).
- **Stocks_Page**: The stock browser page (`pages/stocks.html` + `js/stocks.js`).
- **History_Page**: The prediction history page (`pages/history.html`).
- **Profile_Page**: The user profile page (`pages/profile.html`).
- **Charts_Module**: The Chart.js wrapper module (`js/charts.js`).
- **Toast**: A transient on-screen notification rendered by `js/utils.js`.
- **Skeleton**: A placeholder loading animation shown while data is being fetched.
- **JWT**: JSON Web Token stored in `localStorage` under the key `mm_token`.
- **Symbol**: A stock ticker string such as `AAPL`, `NVDA`, or `TSLA`.
- **Backend**: The Python aiohttp server at `http://localhost:8000`.
- **Agent**: The natural-language query endpoint (`POST /agent/query`) on the Backend.

---

## Requirements

### Requirement 1: Application Shell and Hash-Based Routing

**User Story:** As a user, I want to navigate between pages without full page reloads, so that the
application feels fast and responsive.

#### Acceptance Criteria

1. THE App SHALL load `index.html` as the single entry point for all routes.
2. WHEN the URL hash changes, THE Router SHALL render the corresponding page content inside the
   main content container without reloading the page.
3. THE Router SHALL support the following named routes: `#/dashboard`, `#/predictions`,
   `#/sentiment`, `#/stocks`, `#/history`, `#/profile`, `#/login`, and `#/register`.
4. WHEN an unrecognised hash is requested, THE Router SHALL redirect to `#/dashboard` if the user
   is authenticated, or to `#/login` if the user is not authenticated.
5. WHEN a protected route is requested and no valid JWT exists in `localStorage`, THE Router SHALL
   redirect to `#/login`.

---

### Requirement 2: User Authentication

**User Story:** As a visitor, I want to register and log in, so that I can access personalised
predictions and history.

#### Acceptance Criteria

1. THE App SHALL provide a registration page at `#/register` with fields for email, username,
   full name, and password.
2. WHEN the registration form is submitted with valid data, THE Auth_Module SHALL call
   `POST /auth/register` and, on a 200 response, redirect the user to `#/login`.
3. IF `POST /auth/register` returns a 400 error, THEN THE Auth_Module SHALL display the server
   error message in a Toast.
4. THE App SHALL provide a login page at `#/login` with fields for username-or-email and password.
5. WHEN the login form is submitted with valid credentials, THE Auth_Module SHALL call
   `POST /auth/login`, store the returned JWT in `localStorage` under the key `mm_token`, and
   redirect the user to `#/dashboard`.
6. IF `POST /auth/login` returns a 401 error, THEN THE Auth_Module SHALL display "Invalid
   credentials" in a Toast and clear any previously stored JWT.
7. WHEN the user clicks the logout control, THE Auth_Module SHALL call `POST /auth/logout` with
   the `Authorization: Bearer <token>` header, remove the JWT from `localStorage`, and redirect
   to `#/login`.
8. WHILE a JWT is present in `localStorage`, THE App SHALL include an `Authorization: Bearer
   <token>` header on every API_Client request.

---

### Requirement 3: Dashboard Page

**User Story:** As an authenticated user, I want a dashboard overview of key metrics, predictions,
and news, so that I can quickly assess market conditions.

#### Acceptance Criteria

1. WHEN the Dashboard_Page loads, THE Dashboard_Page SHALL display a Skeleton for each data card
   until the corresponding API response is received.
2. WHEN the Dashboard_Page loads for a Symbol, THE API_Client SHALL call
   `GET /stocks/{symbol}/price` and display the current price, daily high, daily low, and volume.
3. WHEN the Dashboard_Page loads for a Symbol, THE API_Client SHALL call
   `GET /predictions/{symbol}?days=5` and display the 1-day and 5-day predicted prices with
   trend direction and confidence score.
4. WHEN the Dashboard_Page loads for a Symbol, THE API_Client SHALL call
   `GET /sentiment/{symbol}` and render a sentiment gauge showing the latest
   `avg_sentiment_score` as a percentage fill from red (−1) through amber (0) to green (+1).
5. WHILE the Dashboard_Page is active, THE Dashboard_Page SHALL refresh price data by calling
   `GET /stocks/{symbol}/price` every 30 seconds.
6. WHEN the Dashboard_Page loads, THE Charts_Module SHALL render a 30-day price history line
   chart using data from `GET /stocks/{symbol}/data` overlaid with the AI predicted line from
   `GET /predictions/{symbol}?days=5`.
7. WHEN the Dashboard_Page loads, THE Charts_Module SHALL render a 7-day sentiment oscillator
   line chart using data from `GET /sentiment/{symbol}`.
8. WHEN the Dashboard_Page loads, THE API_Client SHALL call `GET /predictions/{symbol}/history`
   and display the five most recent backtested predictions in a table showing date, symbol,
   predicted price, actual price, and accuracy delta.
9. WHEN the user submits a query in the AI Agent chat input, THE API_Client SHALL call
   `POST /agent/query` with the query string and display the response text in the chat area.
10. IF any API_Client call returns a non-200 status, THEN THE Dashboard_Page SHALL display an
    error Toast with the response error message and leave the affected card in its last known
    state.

---

### Requirement 4: Symbol Search and Selection

**User Story:** As a user, I want to search for stock symbols by name or ticker, so that I can
quickly switch the active symbol across all pages.

#### Acceptance Criteria

1. THE App SHALL display a symbol search input in the navigation bar on all authenticated pages.
2. WHEN the user types at least 2 characters in the search input, THE API_Client SHALL call
   `GET /symbols/search?q=<query>` and display a dropdown of matching results within 300 ms of
   the last keystroke.
3. WHEN the user selects a result from the dropdown, THE AppState SHALL update the active Symbol
   and THE Router SHALL reload the current page with the new Symbol.
4. IF `GET /symbols/search` returns an empty results array, THEN THE App SHALL display "No
   symbols found" in the dropdown.
5. WHEN the search input loses focus without a selection, THE App SHALL close the dropdown and
   restore the previously active Symbol in the input field.

---

### Requirement 5: Predictions Page

**User Story:** As an authenticated user, I want to view detailed AI price predictions for a
symbol, so that I can evaluate forecast accuracy and confidence.

#### Acceptance Criteria

1. WHEN the Predictions_Page loads, THE API_Client SHALL call `GET /predictions/{symbol}?days=7`
   and display a table of predicted dates, prices, trend direction, confidence score, and model
   source.
2. WHEN the Predictions_Page loads, THE Charts_Module SHALL render a scatter chart plotting
   predicted price against confidence score for each forecast day.
3. WHEN the user clicks "Train Model", THE API_Client SHALL call
   `POST /predictions/{symbol}/train`, display a loading indicator for the duration of the
   request, and show a Toast with the returned MSE and MAE values on completion.
4. WHEN the Predictions_Page loads, THE API_Client SHALL call
   `GET /predictions/{symbol}/backtest` and display MAE, RMSE, and prediction count.
5. IF `POST /predictions/{symbol}/train` returns a non-200 status, THEN THE Predictions_Page
   SHALL display an error Toast with the server error message.

---

### Requirement 6: Sentiment Analysis Page

**User Story:** As an authenticated user, I want to explore sentiment trends for a symbol, so that
I can understand how news is influencing market direction.

#### Acceptance Criteria

1. WHEN the Sentiment_Page loads, THE API_Client SHALL call `GET /sentiment/{symbol}` and display
   a table of daily sentiment records showing date, average score, article count, and positive /
   neutral / negative breakdown.
2. WHEN the Sentiment_Page loads, THE Charts_Module SHALL render a bar chart of daily
   `avg_sentiment_score` values over the available date range, coloured green for positive
   (score > 0.1), amber for neutral (−0.1 ≤ score ≤ 0.1), and red for negative (score < −0.1).
3. WHEN the user clicks "Analyze Now", THE API_Client SHALL call
   `POST /sentiment/{symbol}/analyze`, display a loading indicator, and refresh the sentiment
   table and chart on a 200 response.
4. IF `POST /sentiment/{symbol}/analyze` returns a non-200 status, THEN THE Sentiment_Page SHALL
   display an error Toast with the server error message.

---

### Requirement 7: Stocks Browser Page

**User Story:** As an authenticated user, I want to browse historical stock data and technical
indicators, so that I can perform my own analysis.

#### Acceptance Criteria

1. WHEN the Stocks_Page loads, THE API_Client SHALL call
   `GET /stocks/{symbol}/data?start=<30-days-ago>&end=<today>` and display a paginated table of
   OHLCV records (date, open, high, low, close, volume, adj_close).
2. WHEN the Stocks_Page loads, THE API_Client SHALL call `GET /stocks/{symbol}/indicators` and
   display SMA-5, SMA-20, and volatility values in a summary card.
3. WHEN the user clicks "Collect Data", THE API_Client SHALL call `POST /stocks/collect` with the
   active Symbol and a default of 365 days, display a loading indicator, and show a Toast with
   the number of stock records and news articles inserted on completion.
4. WHEN the Stocks_Page loads, THE Charts_Module SHALL render a candlestick-style line chart of
   the 30-day close price overlaid with SMA-5 and SMA-20 lines.
5. IF `GET /stocks/{symbol}/data` returns an empty data array, THEN THE Stocks_Page SHALL display
   a "No data available — click Collect Data to fetch records" message in place of the table.

---

### Requirement 8: Prediction History Page

**User Story:** As an authenticated user, I want to review all past predictions for a symbol, so
that I can track model performance over time.

#### Acceptance Criteria

1. WHEN the History_Page loads, THE API_Client SHALL call `GET /predictions/{symbol}/history` and
   display a full table of prediction records including prediction date, target date, predicted
   price, actual price (or "Pending"), confidence score, trend direction, and model source.
2. THE History_Page SHALL support client-side sorting of the table by any column when the user
   clicks the column header.
3. WHEN the History_Page loads, THE API_Client SHALL call `GET /predictions/{symbol}/backtest`
   and display aggregate MAE, RMSE, and win-rate statistics above the table.

---

### Requirement 9: User Profile Page

**User Story:** As an authenticated user, I want to view my account details, so that I can confirm
my registration information.

#### Acceptance Criteria

1. WHEN the Profile_Page loads, THE App SHALL read the decoded JWT payload from `localStorage`
   and display the username, email, and account creation date.
2. THE Profile_Page SHALL display a logout button that, when clicked, triggers the logout flow
   defined in Requirement 2, Criterion 7.

---

### Requirement 10: Navigation and Layout

**User Story:** As a user, I want a consistent navigation structure across all pages, so that I
can move between sections without confusion.

#### Acceptance Criteria

1. THE App SHALL render a persistent sidebar navigation on desktop (viewport width > 1024 px)
   containing links to Dashboard, Predictions, Sentiment, Stocks, History, and Profile.
2. WHEN the viewport width is between 768 px and 1024 px (tablet), THE App SHALL collapse the
   sidebar to icon-only display.
3. WHEN the viewport width is less than 768 px (mobile), THE App SHALL hide the sidebar and
   display a hamburger menu button in the top navigation bar.
4. WHEN the hamburger menu button is tapped on mobile, THE App SHALL toggle a full-width
   slide-in navigation drawer.
5. THE App SHALL highlight the navigation item corresponding to the currently active route.

---

### Requirement 11: Visual Design and Theming

**User Story:** As a user, I want a visually consistent dark glassmorphism interface, so that the
application is pleasant and easy to read.

#### Acceptance Criteria

1. THE App SHALL apply a dark background using `background-image.png` fixed and centered with
   `background-size: cover`.
2. THE App SHALL render all content cards using the glassmorphism style: semi-transparent dark
   background (`rgba(18, 20, 28, 0.75)`), `backdrop-filter: blur(12px)`, and an indigo border
   (`rgba(99, 102, 241, 0.15)`).
3. THE App SHALL use the Inter font loaded from Google Fonts for all text.
4. THE App SHALL use Font Awesome 6 icons loaded from cdnjs for all iconography.
5. THE App SHALL colour bullish / positive values in green (`#10b981`), bearish / negative values
   in red (`#ef4444`), and neutral values in amber (`#f59e0b`).
6. THE App SHALL apply the indigo-to-purple gradient (`#6366f1` → `#8b5cf6`) to primary action
   buttons and accent elements.

---

### Requirement 12: Toast Notifications

**User Story:** As a user, I want brief on-screen feedback for actions and errors, so that I know
whether an operation succeeded or failed.

#### Acceptance Criteria

1. WHEN a successful operation completes, THE App SHALL display a green Toast with a success
   message for 3 seconds before automatically dismissing it.
2. WHEN an error occurs, THE App SHALL display a red Toast with the error message for 5 seconds
   before automatically dismissing it.
3. THE App SHALL stack multiple simultaneous Toasts vertically in the bottom-right corner of the
   viewport.
4. WHEN the user clicks a Toast, THE App SHALL dismiss it immediately.

---

### Requirement 13: Skeleton Loading States

**User Story:** As a user, I want placeholder animations while data loads, so that the interface
does not feel broken during network requests.

#### Acceptance Criteria

1. WHEN an API_Client request is in flight, THE App SHALL display a Skeleton placeholder in the
   target card or table area with an animated shimmer effect.
2. WHEN the API_Client request completes, THE App SHALL replace the Skeleton with the actual
   content.
3. IF an API_Client request fails, THE App SHALL replace the Skeleton with an error state
   message.

---

### Requirement 14: Responsive Layout

**User Story:** As a user on any device, I want the layout to adapt to my screen size, so that
the application is usable on mobile, tablet, and desktop.

#### Acceptance Criteria

1. WHEN the viewport width is greater than 1024 px, THE App SHALL display a multi-column grid
   layout for dashboard cards (minimum 340 px per column).
2. WHEN the viewport width is between 768 px and 1024 px, THE App SHALL reduce the grid to two
   columns.
3. WHEN the viewport width is less than 768 px, THE App SHALL display a single-column stacked
   layout and reduce font sizes and button padding proportionally.
4. THE App SHALL use CSS media queries in `css/responsive.css` to implement all breakpoint
   adjustments without JavaScript.

---

### Requirement 15: Chart Visualisations

**User Story:** As a user, I want interactive charts for price, sentiment, and prediction data, so
that I can visually interpret trends.

#### Acceptance Criteria

1. THE Charts_Module SHALL use Chart.js 4 loaded from the jsDelivr CDN for all chart rendering.
2. THE Charts_Module SHALL render all chart backgrounds as transparent and all grid lines in
   `#1e1f2a` to match the dark theme.
3. THE Charts_Module SHALL colour all chart tick labels and legend text in `#9ca3af`.
4. WHEN a chart is rendered, THE Charts_Module SHALL enable the Chart.js tooltip in `index`
   mode so that all datasets show values on hover.
5. THE Charts_Module SHALL expose a `destroyChart(id)` function that destroys an existing Chart.js
   instance before re-rendering to prevent canvas reuse errors.

---

### Requirement 16: State Management

**User Story:** As a developer, I want a central state object, so that all modules share a
consistent view of application data without prop-drilling.

#### Acceptance Criteria

1. THE AppState SHALL maintain the following fields: `currentSymbol` (string), `currentUser`
   (object or null), `token` (string or null), `priceData` (array), `sentimentData` (array),
   `predictions` (array), and `activeRoute` (string).
2. WHEN the active Symbol changes, THE AppState SHALL update `currentSymbol` and notify all
   registered subscriber callbacks.
3. WHEN the JWT is written to `localStorage`, THE AppState SHALL also update the `token` field.
4. WHEN the JWT is removed from `localStorage` on logout, THE AppState SHALL set `token` and
   `currentUser` to null.
