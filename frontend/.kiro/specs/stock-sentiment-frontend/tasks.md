# Implementation Plan: stock-sentiment-frontend

## Overview

Build the MarketMind AI SPA as pure vanilla HTML/CSS/JavaScript ES modules. Tasks progress from
project scaffolding through core infrastructure (router, state, API client, auth) to each page
module, then charts, utilities, and finally wiring everything together. Property-based tests use
fast-check; unit tests use Vitest with jsdom.

## Tasks

- [x] 1. Scaffold project structure and configure test environment
  - Create `frontend/` directory tree: `pages/`, `css/`, `js/`, `assets/`
  - Create empty placeholder files for all HTML pages, CSS files, and JS modules listed in the
    design file structure
  - Add `package.json` with `vitest`, `jsdom`, and `fast-check` dev dependencies
  - Add `vitest.config.js` with `environment: 'jsdom'` and `test/` source root
  - Create `tests/` directory with one smoke test to confirm the environment boots
  - _Requirements: 1.1_

- [x] 2. Implement `index.html` shell and global CSS
  - [x] 2.1 Write `frontend/index.html` with persistent shell layout
    - Include `#app-shell`, `#sidebar`, `#main-wrapper`, `#top-bar`, `#app-content`,
      `#toast-container` elements matching the design spec
    - Load Chart.js 4 from jsDelivr CDN, Inter from Google Fonts, Font Awesome 6 from cdnjs
    - Add `<script type="module" src="js/app.js">` as the single entry point
    - _Requirements: 1.1, 11.3, 11.4, 15.1_
  - [x] 2.2 Write `css/main.css` with glassmorphism design tokens
    - CSS custom properties for colours, blur, border-radius matching `design.html`
    - `.glass-card`, `.btn-primary`, `.btn-outline`, `.ticker-badge`, `.gradient-text`,
      `.sentiment-gauge` / `.gauge-fill`, `.news-card` component classes
    - Custom scrollbar styles and `@keyframes float`
    - _Requirements: 11.1, 11.2, 11.5, 11.6_
  - [x] 2.3 Write `css/components.css` with reusable component styles
    - Toast styles (`.toast`, `.toast-success`, `.toast-error`, stacking in bottom-right)
    - Skeleton shimmer animation (`.skeleton`, `.skeleton-row`, `@keyframes shimmer`)
    - Table styles, chart container (`.chart-container { height: 280px }`)
    - _Requirements: 12.3, 13.1_
  - [x] 2.4 Write `css/dashboard.css` with dashboard grid layout
    - Auto-fit grid (`minmax(340px, 1fr)`) for dashboard cards
    - Sidebar full-width layout for desktop
    - _Requirements: 10.1, 14.1_
  - [x] 2.5 Write `css/responsive.css` with media query breakpoints only
    - `>1024px`: multi-column grid, full sidebar
    - `768–1024px`: two-column grid, icon-only sidebar
    - `<768px`: single-column, hidden sidebar, hamburger visible, reduced font/padding
    - _Requirements: 10.2, 10.3, 14.1, 14.2, 14.3, 14.4_

- [x] 3. Implement `js/state.js` — AppState singleton
  - [x] 3.1 Implement AppState with all required fields and methods
    - Fields: `currentSymbol`, `currentUser`, `token`, `priceData`, `sentimentData`,
      `predictions`, `activeRoute` with correct initial values
    - `setSymbol(symbol)`: updates `currentSymbol`, calls all subscriber callbacks
    - `subscribe(callback)`: registers callback, returns unsubscribe function
    - `setToken(token)`: writes/removes `mm_token` in `localStorage`, updates `token` field
    - `setUser(user)`: updates `currentUser`
    - _Requirements: 16.1, 16.2, 16.3, 16.4_
  - [ ]* 3.2 Write property test for AppState symbol selection (Property 10)
    - **Property 10: Symbol selection updates AppState and notifies subscribers**
    - **Validates: Requirements 4.3, 16.2**
    - File: `tests/state.symbol-selection.test.js`
  - [ ]* 3.3 Write unit tests for AppState initial values and token/user null on init
    - Verify all fields match design spec defaults
    - Verify `setToken(null)` removes `mm_token` from localStorage

- [x] 4. Implement `js/utils.js` — Toast, Skeleton, and helpers
  - [x] 4.1 Implement toast notifications
    - `showToast(message, type, duration)`: creates `.toast` element, appends to
      `#toast-container`, auto-removes after `duration` ms (3000 for success, 5000 for error)
    - Click handler dismisses immediately
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  - [x] 4.2 Implement skeleton helpers
    - `showSkeleton(containerId, rows)`: injects `.skeleton-row` elements into container
    - `hideSkeleton(containerId)`: removes all `.skeleton-row` elements from container
    - _Requirements: 13.1, 13.2, 13.3_
  - [x] 4.3 Implement date and number helpers
    - `formatDate(dateStr)`: `'YYYY-MM-DD'` → `'Mar 1, 2026'`
    - `daysAgo(n)`: returns ISO date string n days before today
    - `today()`: returns today's ISO date string
    - `formatPrice(n)`: → `'$213.45'`
    - `formatPercent(n)`: → `'+2.34%'`
    - `colorClass(n)`: → `'positive'` | `'negative'` | `'neutral'`
    - _Requirements: 11.5_
  - [ ]* 4.4 Write property test for toast auto-dismiss timing (Property 15)
    - **Property 15: Toast auto-dismiss timing (3s success, 5s error)**
    - **Validates: Requirements 12.1, 12.2**
    - File: `tests/utils.toast-timing.test.js`
    - Use `vi.useFakeTimers()`
  - [ ]* 4.5 Write property test for skeleton lifecycle (Property 16)
    - **Property 16: Skeleton replaced on request completion**
    - **Validates: Requirements 13.1, 13.2, 13.3**
    - File: `tests/utils.skeleton-lifecycle.test.js`

- [x] 5. Implement `js/api.js` — HTTP client
  - [x] 5.1 Implement `request`, `get`, `post` with auth header injection and error normalisation
    - `BASE_URL = 'http://localhost:8000'`
    - Attach `Authorization: Bearer <token>` when `AppState.token` is non-null
    - On non-200: parse `data.error`, throw `ApiError(status, message)`
    - On fetch throw: throw `ApiError(0, 'Network error — check your connection')`
    - _Requirements: 2.8_
  - [x] 5.2 Implement all domain helper namespaces on the `api` object
    - `api.auth`: `register`, `login`, `logout`
    - `api.stocks`: `price`, `data`, `indicators`, `collect`
    - `api.sentiment`: `get`, `analyze`
    - `api.predictions`: `get`, `train`, `history`, `backtest`
    - `api.symbols`: `search`
    - `api.agent`: `query`
    - _Requirements: 2.2, 2.5, 2.7, 3.2, 3.3, 3.4, 3.6, 3.7, 3.8, 3.9, 4.2, 5.1, 5.3, 6.1,
      6.3, 7.1, 7.2, 7.3, 8.1, 8.3_
  - [ ]* 5.3 Write property test for Bearer token on all authenticated requests (Property 5)
    - **Property 5: Bearer token attached to all authenticated requests**
    - **Validates: Requirements 2.8**
    - File: `tests/api.bearer-header.test.js`
  - [ ]* 5.4 Write property test for error toast on non-200 API response (Property 8)
    - **Property 8: Error toast shown for any non-200 response**
    - **Validates: Requirements 3.10, 5.5, 6.4**
    - File: `tests/api.error-toast.test.js`

- [x] 6. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement `js/auth.js` — Authentication flows
  - [x] 7.1 Implement register and login form handlers
    - `initRegister()`: binds submit on `#register-form`, calls `api.auth.register`, on 200
      navigates to `#/login`, on 400 calls `showToast(err.message, 'error')`
    - `initLogin()`: binds submit on `#login-form`, calls `api.auth.login`, on 200 calls
      `AppState.setToken(token)`, navigates to `#/dashboard`, on 401 shows toast and clears token
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [x] 7.2 Implement logout
    - `logout()`: calls `api.auth.logout`, then `AppState.setToken(null)`,
      `AppState.setUser(null)`, navigates to `#/login`
    - _Requirements: 2.7_
  - [ ]* 7.3 Write property test for login token round-trip (Property 3)
    - **Property 3: Login stores token in localStorage and AppState**
    - **Validates: Requirements 2.5, 16.3**
    - File: `tests/auth.login-round-trip.test.js`
  - [ ]* 7.4 Write property test for logout clears all auth state (Property 4)
    - **Property 4: Logout clears all auth state**
    - **Validates: Requirements 2.7, 16.4**
    - File: `tests/auth.logout.test.js`
  - [ ]* 7.5 Write unit tests for auth form validation edge cases
    - 400 on register shows server error message in toast
    - 401 on login shows "Invalid credentials" toast

- [x] 8. Implement `js/app.js` — Router and bootstrap
  - [x] 8.1 Implement hash-based router with auth guard
    - Define `ROUTES` map with all 8 routes, `auth` flag, page path, and module import
    - `hashchange` + `DOMContentLoaded` listeners call `navigate()`
    - Auth guard: if no token and `auth: true` → redirect `#/login`; if token and route is
      `/login` or `/register` → redirect `#/dashboard`
    - Unrecognised hash: redirect `#/dashboard` (authenticated) or `#/login` (unauthenticated)
    - Fetch page HTML fragment, inject into `#app-content`, dynamically import module, call
      `module.init()`
    - Update `AppState.activeRoute`, apply active class to matching sidebar nav item
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 10.5_
  - [x] 8.2 Implement `navigate(hash)` and `getCurrentRoute()` public functions
    - _Requirements: 1.2_
  - [x] 8.3 Implement symbol search in top bar
    - Debounce input: call `api.symbols.search(q)` when `q.length >= 2`, within 300 ms of last
      keystroke; show dropdown; on selection call `AppState.setSymbol(symbol)` and
      `navigate(getCurrentRoute())`; on blur without selection restore previous symbol
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 8.4 Implement hamburger menu toggle for mobile
    - Toggle `.drawer-open` class on `#sidebar` when hamburger button clicked
    - _Requirements: 10.3, 10.4_
  - [ ]* 8.5 Write property test for route rendering completeness (Property 1)
    - **Property 1: All routes render correct page fragment**
    - **Validates: Requirements 1.2, 1.3**
    - File: `tests/router.route-rendering.test.js`
  - [ ]* 8.6 Write property test for routing auth guard (Property 2)
    - **Property 2: Auth guard redirects correctly for all hash values**
    - **Validates: Requirements 1.4, 1.5**
    - File: `tests/router.auth-guard.test.js`
  - [ ]* 8.7 Write property test for symbol search debounce (Property 9)
    - **Property 9: Search API called after 2+ chars, not before**
    - **Validates: Requirements 4.2**
    - File: `tests/search.debounce.test.js`
  - [ ]* 8.8 Write property test for active nav item highlighted (Property 14)
    - **Property 14: Active nav item highlighted for any route**
    - **Validates: Requirements 10.5**
    - File: `tests/nav.active-highlight.test.js`

- [x] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement `js/charts.js` — Chart.js wrappers
  - [x] 10.1 Implement chart registry, `destroyChart`, and dark theme defaults
    - Maintain a `Map<id, Chart>` registry
    - `destroyChart(id)`: calls `.destroy()` on existing instance, removes from map; no-op if
      id not found
    - `CHART_DEFAULTS`: transparent background, `#1e1f2a` grid, `#9ca3af` ticks, tooltip
      `mode: 'index'`, `intersect: false`
    - _Requirements: 15.2, 15.3, 15.4, 15.5_
  - [x] 10.2 Implement `createLineChart`, `createBarChart`, `createScatterChart`
    - Each merges caller options with `CHART_DEFAULTS`, registers instance, returns `Chart`
    - _Requirements: 15.1, 15.2, 15.3, 15.4_
  - [ ]* 10.3 Write property test for chart destroy before re-render (Property 18)
    - **Property 18: Chart destroy + re-render no canvas errors**
    - **Validates: Requirements 15.5**
    - File: `tests/charts.destroy-rerender.test.js`
  - [ ]* 10.4 Write property test for chart tooltip mode (Property 19)
    - **Property 19: Chart tooltip mode set to index**
    - **Validates: Requirements 15.4**
    - File: `tests/charts.tooltip-mode.test.js`
  - [ ]* 10.5 Write property test for sentiment bar chart color mapping (Property 11)
    - **Property 11: Sentiment bar color mapping correctness**
    - **Validates: Requirements 6.2**
    - File: `tests/charts.sentiment-color.test.js`

- [x] 11. Write HTML page fragments
  - [x] 11.1 Write `pages/login.html` and `pages/register.html`
    - Login: `#login-form` with username-or-email and password fields, submit button
    - Register: `#register-form` with email, username, full name, password fields
    - Both use `.glass-card` styling
    - _Requirements: 2.1, 2.4_
  - [x] 11.2 Write `pages/dashboard.html`
    - Skeleton-ready containers: `#price-card`, `#prediction-card`, `#sentiment-card`,
      `#history-table`, `#agent-chat`
    - Canvas elements: `#priceChart`, `#sentimentChart`
    - Sentiment gauge: `.sentiment-gauge` > `.gauge-fill`
    - AI agent chat input `#agent-input` and send button `#agent-send`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7, 3.8, 3.9_
  - [x] 11.3 Write `pages/predictions.html`
    - `#predictions-table` container, `#scatter-chart` canvas
    - "Train Model" button `#train-btn`, backtest metrics `#backtest-card`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 11.4 Write `pages/sentiment.html`
    - `#sentiment-table` container, `#sentiment-bar-chart` canvas
    - "Analyze Now" button `#analyze-btn`
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 11.5 Write `pages/stocks.html`
    - `#stocks-table` container, `#stocks-chart` canvas
    - `#indicators-card`, "Collect Data" button `#collect-btn`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [x] 11.6 Write `pages/history.html`
    - `#history-table` with sortable column headers, `#backtest-stats` card
    - _Requirements: 8.1, 8.2, 8.3_
  - [x] 11.7 Write `pages/profile.html`
    - `#profile-username`, `#profile-email`, `#profile-created` display fields
    - Logout button `#logout-btn`
    - _Requirements: 9.1, 9.2_

- [x] 12. Implement `js/dashboard.js` — Dashboard page module
  - [x] 12.1 Implement `init()`: load all dashboard data in parallel
    - Show skeletons, call `api.stocks.price`, `api.predictions.get(symbol, 5)`,
      `api.sentiment.get`, `api.stocks.data` (30 days), `api.predictions.history` in parallel
    - Render price card (price, high, low, volume), prediction card (1-day, 5-day, confidence,
      trend), sentiment gauge (score → percentage fill), history table (5 most recent rows)
    - On any error: `showToast(err.message, 'error')`, leave card in last known state
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.8, 3.10_
  - [x] 12.2 Implement 30-second price polling
    - Start `setInterval` calling `api.stocks.price` every 30 000 ms after initial load
    - Export `cleanup()` that calls `clearInterval`; router calls `cleanup()` on navigation away
    - _Requirements: 3.5_
  - [x] 12.3 Render dashboard charts via Charts Module
    - Price history line chart (`#priceChart`): 30-day close data + predicted overlay
    - Sentiment oscillator line chart (`#sentimentChart`): 7-day `avg_sentiment_score`
    - _Requirements: 3.6, 3.7_
  - [x] 12.4 Implement AI agent chat
    - On `#agent-send` click: call `api.agent.query(text)`, append response to `#agent-chat`
    - _Requirements: 3.9_
  - [ ]* 12.5 Write property test for dashboard history limit (Property 7)
    - **Property 7: Dashboard shows only 5 most recent history records**
    - **Validates: Requirements 3.8**
    - File: `tests/dashboard.history-limit.test.js`
  - [ ]* 12.6 Write property test for dashboard price polling interval (Property 17)
    - **Property 17: Price polling fires every 30 seconds**
    - **Validates: Requirements 3.5**
    - File: `tests/dashboard.polling.test.js`
    - Use `vi.useFakeTimers()`

- [x] 13. Implement `js/predictions.js` — Predictions page module
  - [x] 13.1 Implement `init()`: load predictions and backtest data
    - Call `api.predictions.get(symbol, 7)` and `api.predictions.backtest(symbol)` in parallel
    - Render predictions table (date, price, trend, confidence, model source)
    - Render backtest card (MAE, RMSE, count)
    - _Requirements: 5.1, 5.4_
  - [x] 13.2 Render scatter chart via Charts Module
    - `#scatter-chart`: predicted price (y) vs confidence score (x) per forecast day
    - _Requirements: 5.2_
  - [x] 13.3 Implement "Train Model" button handler
    - Show loading indicator on `#train-btn`, call `api.predictions.train(symbol)`
    - On 200: `showToast('MSE: X, MAE: Y', 'success')`, re-run `init()`
    - On error: `showToast(err.message, 'error')`
    - _Requirements: 5.3, 5.5_

- [x] 14. Implement `js/sentiment.js` — Sentiment page module
  - [x] 14.1 Implement `init()`: load sentiment data
    - Call `api.sentiment.get(symbol)`, render table (date, score, article count, +/=/- counts)
    - _Requirements: 6.1_
  - [x] 14.2 Render sentiment bar chart via Charts Module
    - `#sentiment-bar-chart`: daily `avg_sentiment_score` bars, colour-coded per Property 11
    - _Requirements: 6.2_
  - [x] 14.3 Implement "Analyze Now" button handler
    - Show loading indicator, call `api.sentiment.analyze(symbol)`
    - On 200: re-run `init()` to refresh table and chart
    - On error: `showToast(err.message, 'error')`
    - _Requirements: 6.3, 6.4_

- [x] 15. Implement `js/stocks.js` — Stocks page module
  - [x] 15.1 Implement `init()`: load stock data and indicators
    - Call `api.stocks.data(symbol, daysAgo(30), today())` and `api.stocks.indicators(symbol)`
      in parallel
    - Render OHLCV table with pagination; if data array empty show "No data available — click
      Collect Data to fetch records"
    - Render indicators card (SMA-5, SMA-20, volatility)
    - _Requirements: 7.1, 7.2, 7.5_
  - [x] 15.2 Render stocks chart via Charts Module
    - `#stocks-chart`: 30-day close price line + SMA-5 and SMA-20 overlay lines
    - _Requirements: 7.4_
  - [x] 15.3 Implement "Collect Data" button handler
    - Show loading indicator, call `api.stocks.collect([symbol], 365)`
    - On 200: `showToast('X stock records, Y news articles inserted', 'success')`, re-run `init()`
    - On error: `showToast(err.message, 'error')`
    - _Requirements: 7.3_

- [x] 16. Implement `js/predictions.js` history page (inline in `pages/history.html`)
  - [x] 16.1 Implement history page init (no separate JS module — inline or shared)
    - Call `api.predictions.history(symbol)` and `api.predictions.backtest(symbol)` in parallel
    - Render full history table with all fields; "Pending" for null `actual_price`
    - Render backtest stats (MAE, RMSE, win-rate) above table
    - _Requirements: 8.1, 8.3_
  - [x] 16.2 Implement client-side column sorting
    - Click on any `<th>` toggles ascending/descending sort for that column
    - All rows preserved after sort (no drops or duplicates)
    - _Requirements: 8.2_
  - [ ]* 16.3 Write property test for client-side table sorting (Property 12)
    - **Property 12: Client-side sorting correctness for all columns**
    - **Validates: Requirements 8.2**
    - File: `tests/history.sort.test.js`

- [x] 17. Implement profile page init (inline in `pages/profile.html`)
  - [x] 17.1 Decode JWT payload and render profile fields
    - Read `mm_token` from `localStorage`, base64-decode the payload segment
    - Render `username`, `email`, `created_at` into `#profile-username`, `#profile-email`,
      `#profile-created`
    - _Requirements: 9.1_
  - [x] 17.2 Wire logout button
    - `#logout-btn` click calls `auth.logout()`
    - _Requirements: 9.2_
  - [ ]* 17.3 Write property test for JWT payload decode renders profile fields (Property 13)
    - **Property 13: JWT payload fields rendered correctly**
    - **Validates: Requirements 9.1**
    - File: `tests/profile.jwt-decode.test.js`

- [x] 18. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Wire page data rendering property tests
  - [ ]* 19.1 Write property test for page data rendered from API response (Property 6)
    - **Property 6: Page data matches API response values**
    - **Validates: Requirements 3.2, 3.3, 3.4, 5.1, 6.1, 7.1, 8.1**
    - File: `tests/pages.data-render.test.js`
    - Mock `api.*` with `vi.fn()`, assert DOM values equal mocked response values

- [x] 20. Final integration and wiring
  - [x] 20.1 Wire `AppState.subscribe` in all page modules
    - Each page module subscribes to symbol changes on `init()` and unsubscribes in `cleanup()`
    - _Requirements: 4.3, 16.2_
  - [x] 20.2 Wire router `cleanup()` calls on navigation
    - Before injecting new page fragment, call previous module's `cleanup()` if it exists
    - _Requirements: 3.5_
  - [x] 20.3 Verify 401 handling redirects to login
    - In `api.js` `request()`: if `ApiError.status === 401`, call `AppState.setToken(null)`,
      `AppState.setUser(null)`, `navigate('#/login')`
    - _Requirements: 2.8_
  - [ ]* 20.4 Write property test for AppState symbol selection end-to-end (Property 10)
    - **Property 10: Symbol selection updates AppState and notifies subscribers**
    - **Validates: Requirements 4.3, 16.2**
    - File: `tests/state.symbol-selection.test.js` (extend existing test)

- [x] 21. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical milestones
- Property tests validate universal correctness properties across many generated inputs
- Unit tests validate specific examples, edge cases, and integration points
- Run tests with `npx vitest --run` for a single CI-style execution
