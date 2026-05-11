# Stock Market Prediction System - Running Guide

## ✅ System Status

Your stock market prediction system is now **RUNNING**!

### Backend Server
- **URL**: http://localhost:8000
- **Status**: ✅ Running
- **Database**: Neon PostgreSQL (connected)
- **Framework**: aiohttp

### Frontend Server
- **URL**: http://localhost:3000
- **Status**: ✅ Running
- **Framework**: Vanilla HTML/CSS/JavaScript

---

## 🚀 Quick Start

### Access the Application

1. **Open your browser** and navigate to:
   ```
   http://localhost:3000/frontend/
   ```

2. **Register a new account** or **login** to start using the system

---

## 📋 Available Features

### 1. **Stock Data Collection**
Collect historical stock prices and news articles:
```bash
cd backend
source .venv/bin/activate
python -m app.main collect-data --symbols AAPL MSFT GOOGL --days 365
```

### 2. **Sentiment Analysis**
Analyze news sentiment for a stock:
```bash
python -m app.main analyze-sentiment --symbol AAPL
```

### 3. **Train ML Model**
Train LSTM prediction model for a stock:
```bash
python -m app.main train-model --symbol AAPL
```

### 4. **Generate Predictions**
Get price predictions:
```bash
python -m app.main predict --symbol AAPL --days 5
```

### 5. **Interactive Agent**
Chat with the AI agent:
```bash
python -m app.main run
```

---

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout

### Stock Data
- `GET /stocks/{symbol}/data?start=YYYY-MM-DD&end=YYYY-MM-DD` - Historical data
- `GET /stocks/{symbol}/price` - Current price
- `GET /stocks/{symbol}/indicators` - Technical indicators
- `POST /stocks/collect` - Collect data for symbols

### Sentiment Analysis
- `GET /sentiment/{symbol}` - Get sentiment data
- `POST /sentiment/{symbol}/analyze` - Analyze sentiment

### Predictions
- `GET /predictions/{symbol}?days=N` - Get predictions
- `POST /predictions/{symbol}/train` - Train model
- `GET /predictions/{symbol}/history` - Prediction history
- `GET /predictions/{symbol}/backtest` - Backtest accuracy

### AI Agent
- `POST /agent/query` - Query the AI agent

### Symbols
- `GET /symbols/search?q=query` - Search stock symbols

---

## 🧪 Testing the System

### Test Backend API
```bash
# Test symbol search
curl http://localhost:8000/symbols/search?q=AAPL

# Register a test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test1234!"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"testuser","password":"Test1234!"}'
```

### Test Frontend
1. Open http://localhost:3000/frontend/
2. Click "Register" and create an account
3. Login with your credentials
4. Navigate through the dashboard

---

## 📊 Example Workflow

### Complete Stock Analysis Workflow

1. **Collect Data**
   ```bash
   cd backend
   source .venv/bin/activate
   python -m app.main collect-data --symbols AAPL --days 365
   ```

2. **Analyze Sentiment**
   ```bash
   python -m app.main analyze-sentiment --symbol AAPL
   ```

3. **Train Model**
   ```bash
   python -m app.main train-model --symbol AAPL
   ```

4. **Generate Predictions**
   ```bash
   python -m app.main predict --symbol AAPL --days 5
   ```

5. **View in Frontend**
   - Open http://localhost:3000/frontend/
   - Navigate to "Predictions" page
   - Select AAPL to view predictions

---

## 🛑 Stopping the System

### Stop Backend Server
```bash
# Press Ctrl+C in the terminal running the backend
# Or find and kill the process:
lsof -ti:8000 | xargs kill -9
```

### Stop Frontend Server
```bash
# Press Ctrl+C in the terminal running the frontend
# Or find and kill the process:
lsof -ti:3000 | xargs kill -9
```

---

## 🔧 Troubleshooting

### Backend Issues

**Database Connection Error**
- Check your Neon PostgreSQL connection string in `backend/.env`
- Ensure SSL mode is enabled

**Missing Dependencies**
```bash
cd backend
uv sync
```

**Migration Issues**
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### Frontend Issues

**CORS Errors**
- Backend already has CORS enabled for all origins
- Make sure backend is running on port 8000

**API Connection Failed**
- Check that backend is running: `curl http://localhost:8000/symbols/search?q=test`
- Verify `frontend/frontend/js/api.js` has correct BASE_URL

---

## 📁 Project Structure

```
stock-market/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI agent coordination
│   │   ├── config/         # Configuration & database
│   │   ├── models/         # Database models
│   │   ├── nodes/          # Processing pipeline nodes
│   │   ├── services/       # Business logic
│   │   ├── tools/          # Utility functions
│   │   ├── utils/          # Logging & helpers
│   │   ├── main.py         # CLI entry point
│   │   └── server.py       # HTTP server
│   ├── alembic/            # Database migrations
│   ├── docs/               # Documentation
│   ├── .env                # Environment variables
│   └── pyproject.toml      # Python dependencies
│
└── frontend/
    └── frontend/
        ├── css/            # Stylesheets
        ├── js/             # JavaScript modules
        ├── pages/          # HTML pages
        └── index.html      # Landing page
```

---

## 🔑 Environment Variables

Key variables in `backend/.env`:

```env
# Database (Neon PostgreSQL)
POSTGRES_SERVER=ep-quiet-grass-ap48qos1-pooler.c-7.us-east-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=npg_Lrose1FZmpX0
POSTGRES_DB=neondb

# Azure OpenAI (GPT-Nano)
AZURE_OPENAI_ENDPOINT=https://comsi-md4b9qgt-eastus2.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=1lpVqQuGLPAobeHfyIuMmX8yQDh8Iq7tPRFxEDIyPPr5fQRJsx1EJQQJ99BGACHYHv6XJ3w3AAAAACOGRB4P
AZURE_OPENAI_DEPLOYMENT=gpt-5.4-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Security
SECRET_KEY=f6d9c342de60743fbda436d8b7ee91c531a51654f3aa44b7e4b2e80f01b75acc
```

---

## 📚 Next Steps

1. **Collect initial data** for stocks you want to track
2. **Train models** for those stocks
3. **Explore the frontend** interface
4. **Try the AI agent** for natural language queries
5. **Review the documentation** in `backend/docs/`

---

## 🎯 Key Technologies

- **Backend**: Python 3.11, aiohttp, SQLModel, TensorFlow
- **Database**: Neon PostgreSQL (cloud-hosted)
- **AI**: Azure OpenAI (GPT-Nano), LSTM models
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Sources**: Yahoo Finance, NewsAPI

---

## 📞 Support

For issues or questions:
1. Check the documentation in `backend/docs/`
2. Review the API reference in `backend/docs/api.md`
3. Check implementation details in `backend/docs/implementation.md`

---

**System is ready! Happy trading! 📈**
