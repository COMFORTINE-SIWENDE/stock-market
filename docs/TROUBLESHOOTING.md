# Troubleshooting Guide

## ✅ All Endpoints Tested Successfully

All 12 critical endpoints have been tested and are working correctly:

1. ✓ Symbol Search
2. ✓ Stock Price
3. ✓ Historical Data
4. ✓ Technical Indicators
5. ✓ Predictions
6. ✓ Sentiment Analysis
7. ✓ User Registration
8. ✓ User Login
9. ✓ Authenticated Logout
10. ✓ Prediction History
11. ✓ AI Agent Query
12. ✓ Data Collection

---

## Common Issues and Solutions

### 1. "Symbol AAPL not found" Error

**Problem**: Frontend shows "Symbol not found" when trying to get predictions or data.

**Cause**: The stock symbol hasn't been added to the database yet.

**Solution**: Collect data for the symbol first:

```bash
# Via API
curl -X POST http://localhost:8000/stocks/collect \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"], "days": 365}'

# Via CLI
cd backend
source .venv/bin/activate
python -m app.main collect-data --symbols AAPL MSFT GOOGL --days 365
```

**Prevention**: Always collect data for a symbol before requesting predictions or analysis.

---

### 2. Predictions Taking Too Long

**Problem**: First prediction request for a symbol takes 30-60 seconds.

**Cause**: The system is training the LSTM model on-demand when no trained model exists.

**Solution**: Pre-train models for frequently used symbols:

```bash
cd backend
source .venv/bin/activate

# Train models for your main symbols
python -m app.main train-model --symbol AAPL
python -m app.main train-model --symbol MSFT
python -m app.main train-model --symbol GOOGL
```

**Note**: After training once, subsequent predictions will be instant (< 1 second).

---

### 3. No News Articles / Sentiment Data

**Problem**: Sentiment analysis returns 0 articles.

**Cause**: 
- No NEWS_API_KEY configured in `.env`
- News API rate limits reached
- No recent news for the symbol

**Solution**:

1. **Add News API Key** (Optional but recommended):
   - Get a free key from https://newsapi.org/
   - Add to `backend/.env`:
     ```env
     NEWS_API_KEY=your_api_key_here
     ```

2. **Collect news manually**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -m app.main collect-data --symbols AAPL --days 1
   ```

**Note**: The system works without news data - predictions use only price data and technical indicators.

---

### 4. Frontend Not Loading / CORS Errors

**Problem**: Frontend shows connection errors or CORS issues.

**Cause**: Backend not running or wrong URL.

**Solution**:

1. **Check backend is running**:
   ```bash
   curl http://localhost:8000/symbols/search?q=test
   ```
   Should return JSON response.

2. **Verify frontend API URL**:
   - Check `frontend/frontend/js/api.js`
   - Should have: `const BASE_URL = 'http://localhost:8000';`

3. **Restart backend if needed**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -m app.server
   ```

---

### 5. Database Connection Errors

**Problem**: Backend fails to start with database connection error.

**Cause**: Neon PostgreSQL connection issue.

**Solution**:

1. **Verify .env credentials**:
   ```bash
   cd backend
   cat .env | grep POSTGRES
   ```

2. **Test connection**:
   ```bash
   source .venv/bin/activate
   python -c "from app.config.database import sync_engine; sync_engine.connect(); print('✓ Connected')"
   ```

3. **Check Neon dashboard**: Ensure database is active at https://console.neon.tech/

---

### 6. Model Training Fails

**Problem**: "Insufficient data for AAPL: need at least 80 rows"

**Cause**: Not enough historical data collected.

**Solution**: Collect more data (at least 90 days):

```bash
cd backend
source .venv/bin/activate
python -m app.main collect-data --symbols AAPL --days 365
```

**Minimum Requirements**:
- 80+ days of historical data for training
- 60+ days for predictions without training

---

### 7. Authentication Issues

**Problem**: Login fails with "Invalid credentials"

**Cause**: 
- Wrong password
- User doesn't exist
- Password hashing issue

**Solution**:

1. **Register new user**:
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","username":"testuser","password":"Test1234!","full_name":"Test User"}'
   ```

2. **Check user exists**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -c "
   from app.config.database import get_sync_session
   from app.models.user import User
   from sqlmodel import select
   with get_sync_session() as s:
       users = s.exec(select(User)).all()
       for u in users: print(f'{u.id}: {u.username} ({u.email})')
   "
   ```

---

### 8. AI Agent Not Responding

**Problem**: Agent query returns error or empty response.

**Cause**: Azure OpenAI configuration issue.

**Solution**:

1. **Verify Azure OpenAI credentials in .env**:
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_DEPLOYMENT=gpt-5.4-nano
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   ```

2. **Test agent**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -m app.main run
   # Type: What is the price of AAPL?
   ```

---

### 9. Port Already in Use

**Problem**: "Address already in use" when starting backend.

**Cause**: Another process is using port 8000.

**Solution**:

1. **Find and kill the process**:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Or use a different port**:
   ```bash
   cd backend
   source .venv/bin/activate
   python -c "from app.server import create_app; from aiohttp import web; app=create_app(); web.run_app(app, port=8001)"
   ```
   Then update `frontend/frontend/js/api.js` to use port 8001.

---

### 10. TensorFlow / Model Loading Errors

**Problem**: "Failed to load model" or TensorFlow errors.

**Cause**: 
- Model file corrupted
- TensorFlow version mismatch
- Insufficient memory

**Solution**:

1. **Delete and retrain model**:
   ```bash
   cd backend
   rm -rf app/models/trained/AAPL_*
   source .venv/bin/activate
   python -m app.main train-model --symbol AAPL
   ```

2. **Check TensorFlow installation**:
   ```bash
   source .venv/bin/activate
   python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"
   ```

---

## Performance Optimization

### Speed Up Predictions

1. **Pre-train models** for all symbols you'll use
2. **Collect data in bulk** rather than one symbol at a time
3. **Use shorter time horizons** (1-5 days instead of 30)

### Reduce Memory Usage

1. **Train models one at a time** instead of batch training
2. **Limit historical data** to 365 days instead of all-time
3. **Clear old predictions** periodically:
   ```sql
   DELETE FROM predictions WHERE prediction_date < NOW() - INTERVAL '30 days';
   ```

---

## Monitoring and Logs

### Check Backend Logs

Backend logs are displayed in the terminal where you started the server:

```bash
cd backend
source .venv/bin/activate
python -m app.server
# Logs appear here in real-time
```

### Log Levels

- **INFO**: Normal operations (data collection, predictions)
- **WARNING**: Non-critical issues (missing data, fallbacks)
- **ERROR**: Failures that need attention

### Enable Debug Mode

Edit `backend/.env`:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

This will show SQL queries and detailed operation logs.

---

## Quick Health Check

Run this command to verify everything is working:

```bash
./test_endpoints.sh
```

All tests should show ✓ (green checkmarks).

---

## Getting Help

### Check Documentation

1. **API Reference**: `backend/docs/api.md`
2. **Implementation Guide**: `backend/docs/implementation.md`
3. **Backend Guide**: `backend/docs/python-backend-guide.md`

### Common Commands Reference

```bash
# Start backend
cd backend && source .venv/bin/activate && python -m app.server

# Start frontend
cd frontend && python3 -m http.server 3000 --directory frontend

# Collect data
cd backend && source .venv/bin/activate && python -m app.main collect-data --symbols AAPL --days 365

# Train model
cd backend && source .venv/bin/activate && python -m app.main train-model --symbol AAPL

# Generate predictions
cd backend && source .venv/bin/activate && python -m app.main predict --symbol AAPL --days 5

# Interactive agent
cd backend && source .venv/bin/activate && python -m app.main run

# Run tests
./test_endpoints.sh
```

---

## System Requirements Met ✅

- ✅ Python 3.11+ (using 3.12)
- ✅ PostgreSQL (Neon cloud database)
- ✅ TensorFlow 2.15 (compatible with macOS x86_64)
- ✅ 8GB RAM recommended
- ✅ Internet connection for data collection

---

## Known Limitations

1. **News Collection**: Requires NEWS_API_KEY for full functionality
2. **Prediction Accuracy**: Confidence scores start at 50% until backtesting data accumulates
3. **First Prediction**: Takes 30-60 seconds while training model on-demand
4. **Rate Limits**: Yahoo Finance may rate-limit if collecting data for many symbols rapidly

---

**All systems operational! 🚀**
