# Quick Reference Card

## 🚀 Start/Stop Commands

```bash
# START BACKEND
cd backend && source .venv/bin/activate && python -m app.server

# START FRONTEND
cd frontend && python3 -m http.server 3000 --directory frontend

# STOP (Ctrl+C in each terminal)
```

## 🌐 URLs

- **Frontend**: http://localhost:3000/frontend/
- **Backend API**: http://localhost:8000
- **Database**: Neon PostgreSQL (cloud)

## 📊 Common Operations

### Collect Data
```bash
# Via API
curl -X POST http://localhost:8000/stocks/collect \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"], "days": 365}'

# Via CLI
cd backend && source .venv/bin/activate
python -m app.main collect-data --symbols AAPL --days 365
```

### Train Model
```bash
cd backend && source .venv/bin/activate
python -m app.main train-model --symbol AAPL
```

### Generate Predictions
```bash
# Via API
curl "http://localhost:8000/predictions/AAPL?days=5"

# Via CLI
cd backend && source .venv/bin/activate
python -m app.main predict --symbol AAPL --days 5
```

### Test All Endpoints
```bash
./test_endpoints.sh
```

## 🔑 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login |
| POST | `/auth/logout` | Logout |
| GET | `/stocks/{symbol}/price` | Current price |
| GET | `/stocks/{symbol}/data` | Historical data |
| GET | `/stocks/{symbol}/indicators` | Technical indicators |
| POST | `/stocks/collect` | Collect data |
| GET | `/sentiment/{symbol}` | Sentiment data |
| POST | `/sentiment/{symbol}/analyze` | Analyze sentiment |
| GET | `/predictions/{symbol}` | Get predictions |
| POST | `/predictions/{symbol}/train` | Train model |
| GET | `/predictions/{symbol}/history` | Prediction history |
| POST | `/agent/query` | Query AI agent |
| GET | `/symbols/search?q=` | Search symbols |

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Symbol not found" | Collect data first |
| Prediction slow | First time trains model (30-60s) |
| Port in use | `lsof -ti:8000 \| xargs kill -9` |
| Login fails | Register new user |
| No sentiment | Add NEWS_API_KEY to .env |

## 📁 File Locations

```
stock-market/
├── backend/
│   ├── .env                    # Configuration
│   ├── app/server.py          # HTTP server
│   ├── app/main.py            # CLI commands
│   └── app/models/trained/    # ML models
├── frontend/
│   └── frontend/
│       ├── index.html         # Landing page
│       └── js/api.js          # API client
├── test_endpoints.sh          # Test script
├── RUNNING.md                 # Setup guide
├── TROUBLESHOOTING.md         # Issue solutions
└── SYSTEM_STATUS.md           # Status report
```

## 🔐 Default Credentials

**No defaults** - Register your own account:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"yourname","password":"YourPass123!"}'
```

## 📊 Data Requirements

| Operation | Minimum Data | Recommended |
|-----------|--------------|-------------|
| View price | 1 day | Current |
| Predictions | 60 days | 90+ days |
| Train model | 80 days | 365 days |
| Sentiment | 1 article | 10+ articles |

## 🎯 Workflow

1. **Collect data** for symbols
2. **Train models** (optional, auto-trains on first prediction)
3. **Generate predictions**
4. **View in frontend**
5. **Track accuracy** over time

## 💡 Tips

- ✅ Collect 365 days for best predictions
- ✅ Pre-train models to speed up predictions
- ✅ Use 1-5 day horizons for accuracy
- ✅ Check confidence scores
- ❌ Don't collect data too frequently (rate limits)

## 🆘 Emergency Commands

```bash
# Kill all processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Reset database
cd backend && source .venv/bin/activate
alembic downgrade base
alembic upgrade head

# Delete all models
rm -rf backend/app/models/trained/*

# Fresh start
cd backend && uv sync
alembic upgrade head
python -m app.server
```

## 📞 Get Help

1. Check `TROUBLESHOOTING.md`
2. Run `./test_endpoints.sh`
3. Check terminal logs
4. Review `backend/docs/api.md`

---

**System Status**: ✅ All systems operational  
**Last Updated**: May 11, 2026
