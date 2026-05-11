# Frontend User Guide

## Accessing the Application

**URL**: http://localhost:3000/frontend/

---

## Getting Started

### 1. Register an Account

1. Open http://localhost:3000/frontend/
2. Click **"Register"** or navigate to the registration page
3. Fill in:
   - **Email**: Your email address
   - **Username**: Choose a username
   - **Password**: Strong password (min 8 characters)
   - **Full Name**: Your full name
4. Click **"Register"**
5. You'll be redirected to the login page

### 2. Login

1. Enter your **username or email**
2. Enter your **password**
3. Click **"Login"**
4. You'll be redirected to the dashboard

---

## Dashboard Overview

The dashboard shows:
- **Quick Stats**: Portfolio summary, active stocks, predictions
- **Recent Predictions**: Latest price predictions
- **Market Overview**: Current market status
- **Quick Actions**: Shortcuts to common tasks

---

## Features

### 📊 Stocks Page

**View and manage stock data**

1. Navigate to **"Stocks"** from the menu
2. **Search for a symbol**: Use the search bar (e.g., "AAPL")
3. **View stock details**:
   - Current price
   - Historical data chart
   - Technical indicators (SMA, volatility)
4. **Collect new data**: Click "Collect Data" to fetch latest prices

**Important**: Before viewing a stock, make sure data has been collected for it.

### 🔮 Predictions Page

**Generate and view price predictions**

1. Navigate to **"Predictions"**
2. **Select a symbol** from the dropdown
3. **Choose time horizon**: 1, 5, 10, or 30 days
4. Click **"Generate Prediction"**
5. View results:
   - Predicted prices for each day
   - Trend direction (up/down)
   - Confidence score
   - Model source (local/azure)

**First-time prediction**: May take 30-60 seconds while the model trains. Subsequent predictions are instant.

### 📰 Sentiment Analysis

**Analyze news sentiment for stocks**

1. Navigate to **"Sentiment"**
2. **Select a symbol**
3. Click **"Analyze Sentiment"**
4. View results:
   - Average sentiment score (-1 to +1)
   - Article count
   - Positive/Neutral/Negative distribution
   - Sentiment trend over time

**Note**: Requires news data collection. If no articles are found, sentiment will show as neutral (0.0).

### 📈 History Page

**View prediction history and accuracy**

1. Navigate to **"History"**
2. **Select a symbol**
3. View:
   - All past predictions
   - Actual vs predicted prices
   - Accuracy metrics (MAE, RMSE)
   - Prediction trends

### 👤 Profile Page

**Manage your account**

1. Navigate to **"Profile"**
2. View your account information
3. Update settings (if available)
4. Logout

---

## Common Workflows

### Workflow 1: Analyze a New Stock

1. **Collect Data**:
   - Go to Stocks page
   - Search for symbol (e.g., "TSLA")
   - Click "Collect Data"
   - Wait for confirmation

2. **View Current Data**:
   - Check current price
   - View historical chart
   - Review technical indicators

3. **Generate Prediction**:
   - Go to Predictions page
   - Select the symbol
   - Choose time horizon (5 days recommended)
   - Click "Generate Prediction"
   - Wait for results (first time may take 1 minute)

4. **Analyze Sentiment** (Optional):
   - Go to Sentiment page
   - Select the symbol
   - Click "Analyze Sentiment"
   - Review sentiment scores

### Workflow 2: Track Multiple Stocks

1. **Collect Data for All Symbols**:
   ```bash
   # Run this in terminal
   curl -X POST http://localhost:8000/stocks/collect \
     -H "Content-Type: application/json" \
     -d '{"symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"], "days": 365}'
   ```

2. **Generate Predictions**:
   - Go to Predictions page
   - Generate predictions for each symbol
   - Compare results

3. **Monitor Dashboard**:
   - Return to Dashboard
   - View all predictions at a glance
   - Track performance

### Workflow 3: Backtest Predictions

1. **Generate Predictions** for a symbol
2. **Wait for target dates** to pass
3. **Collect new data** to get actual prices
4. **Go to History page**
5. **View accuracy metrics**:
   - MAE (Mean Absolute Error)
   - RMSE (Root Mean Square Error)
   - Prediction vs Actual chart

---

## Tips and Best Practices

### Data Collection

- ✅ **Collect at least 90 days** of data for accurate predictions
- ✅ **Collect 365 days** for best model training
- ✅ **Update data daily** for current prices
- ❌ Don't collect data too frequently (rate limits)

### Predictions

- ✅ **Pre-train models** for frequently used symbols
- ✅ **Use 1-5 day horizons** for most accurate predictions
- ✅ **Check confidence scores** before making decisions
- ❌ Don't rely solely on predictions for trading decisions

### Performance

- ✅ **First prediction takes time** (model training)
- ✅ **Subsequent predictions are instant**
- ✅ **Train models during off-hours** if possible
- ❌ Don't generate 30-day predictions repeatedly (slow)

---

## Keyboard Shortcuts

- **Ctrl/Cmd + K**: Quick search (if implemented)
- **Esc**: Close modals/dialogs
- **Tab**: Navigate form fields

---

## Understanding the Data

### Price Predictions

- **Predicted Price**: Model's forecast for closing price
- **Confidence Score**: 0-100% (higher = more confident)
- **Trend Direction**: "up" or "down" from previous day
- **Model Source**: "local" (your trained model) or "azure" (cloud model)

### Sentiment Scores

- **+1.0**: Extremely positive sentiment
- **+0.5**: Moderately positive
- **0.0**: Neutral
- **-0.5**: Moderately negative
- **-1.0**: Extremely negative

### Technical Indicators

- **SMA 5**: 5-day Simple Moving Average
- **SMA 20**: 20-day Simple Moving Average
- **Volatility**: 20-day rolling standard deviation of returns

---

## Troubleshooting

### "Symbol not found"

**Solution**: Collect data for the symbol first via Stocks page.

### Predictions taking too long

**Solution**: First prediction trains the model (30-60 seconds). Subsequent predictions are instant.

### No sentiment data

**Solution**: 
1. Check if NEWS_API_KEY is configured
2. News data may not be available for all symbols
3. System works without sentiment data

### Login issues

**Solution**:
1. Verify username/password
2. Try registering a new account
3. Check browser console for errors

### Charts not loading

**Solution**:
1. Ensure data has been collected
2. Refresh the page
3. Check browser console for errors

---

## Browser Compatibility

**Supported Browsers**:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Required Features**:
- JavaScript enabled
- Cookies enabled (for authentication)
- LocalStorage enabled (for session management)

---

## Security Notes

- 🔒 **Passwords are hashed** using bcrypt
- 🔒 **Sessions use JWT tokens** with expiration
- 🔒 **HTTPS recommended** for production
- 🔒 **Never share your credentials**

---

## API Integration

The frontend communicates with the backend via REST API:

**Base URL**: `http://localhost:8000`

All API calls are handled automatically by the frontend. You don't need to make manual API calls unless you're developing custom integrations.

---

## Mobile Support

The frontend is responsive and works on mobile devices:

- ✅ Tablets (iPad, Android tablets)
- ✅ Large phones (iPhone 12+, Android)
- ⚠️ Small phones (limited functionality)

**Recommended**: Use desktop or tablet for best experience.

---

## Data Privacy

- ✅ All data stored in your Neon PostgreSQL database
- ✅ No data shared with third parties
- ✅ You control all data collection
- ✅ Can delete account and data anytime

---

## Getting Help

1. **Check TROUBLESHOOTING.md** for common issues
2. **Review API documentation** in `backend/docs/api.md`
3. **Check browser console** for error messages
4. **Run test script**: `./test_endpoints.sh`

---

## Next Steps

1. ✅ Register an account
2. ✅ Collect data for your favorite stocks
3. ✅ Generate predictions
4. ✅ Analyze sentiment
5. ✅ Track accuracy over time

**Happy trading! 📈**
