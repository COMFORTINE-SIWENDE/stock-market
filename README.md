# 📈 Stock Market Prediction System

AI-powered stock market prediction system with sentiment analysis, LSTM neural networks, and real-time data collection.

![Status](https://img.shields.io/badge/status-operational-brightgreen)
![Tests](https://img.shields.io/badge/tests-12%2F12%20passing-brightgreen)

---

## 🚀 Quick Start

### 1. Start Backend
```bash
cd backend
source .venv/bin/activate
python -m app.server
```

### 2. Start Frontend
```bash
cd frontend
python3 -m http.server 3000
```

### 3. Access Application
```
http://localhost:3000/
```

---

## ✨ Features

- 🤖 **AI Predictions** - LSTM neural networks for price forecasting
- 📰 **Sentiment Analysis** - News analysis with TextBlob & VADER
- 📊 **Real-Time Data** - Live stock data from Yahoo Finance
- 🧠 **AI Chat Agent** - Interactive chat with AI assistant for market insights
- 🔐 **Secure Auth** - JWT tokens with bcrypt encryption
- 📱 **Responsive UI** - Modern design that works on all devices
- 👤 **User Profiles** - Personalized account information and statistics

---

## 📊 System Status

| Component | Status |
|-----------|--------|
| Backend API | ✅ Running (http://localhost:8000) |
| Frontend UI | ✅ Running (http://localhost:3000) |
| Database | ✅ Connected (Neon PostgreSQL) |
| All Endpoints | ✅ 14/14 Working |
| AI Chat Agent | ✅ Available |

---

## 🎨 Design

- **Cards**: Light gray (#e1e6e8)
- **Buttons**: Bright blue (#2baff7)
- **Style**: Fully rounded buttons, emoji icons
- **Layout**: Card-based, responsive design

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [RUNNING.md](docs/RUNNING.md) | Complete setup guide |
| [FRONTEND_GUIDE.md](docs/FRONTEND_GUIDE.md) | User guide |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues |
| [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | Command reference |
| [API Reference](backend/docs/api.md) | Complete API docs |

---

## 🧪 Testing

```bash
./test_endpoints.sh
```

Expected: 14/14 tests passing ✓

**New Features:**
- 🤖 AI Chat Agent page at `/pages/agent.html`
- 👤 Enhanced profile with real user data from `/auth/me`

See [NEW_FEATURES.md](docs/NEW_FEATURES.md) for details.

---

## 📁 Project Structure

```
stock-market/
├── backend/              # Python backend (aiohttp + SQLModel)
│   ├── app/             # Application code
│   ├── alembic/         # Database migrations
│   └── docs/            # Backend documentation
├── frontend/            # HTML/CSS/JS frontend
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript modules
│   ├── pages/          # HTML pages
│   └── index.html      # Landing page
├── docs/               # Project documentation
└── test_endpoints.sh   # Automated tests
```

---

## 🔧 Tech Stack

**Backend**
- Python 3.11
- aiohttp (HTTP server)
- SQLModel (ORM)
- TensorFlow 2.15 (ML)
- Azure OpenAI (AI agent)
- PostgreSQL (Neon)

**Frontend**
- HTML5 + CSS3
- Vanilla JavaScript (ES6)
- No frameworks or dependencies

---

## 📊 Example Usage

### Collect Data
```bash
cd backend && source .venv/bin/activate
python -m app.main collect-data --symbols AAPL MSFT --days 365
```

### Generate Predictions
```bash
python -m app.main predict --symbol AAPL --days 5
```

### Train Model
```bash
python -m app.main train-model --symbol AAPL
```

---

## 🎯 Key Endpoints

- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user info (NEW)
- `GET /stocks/{symbol}/price` - Current price
- `GET /predictions/{symbol}?days=N` - Generate predictions
- `POST /sentiment/{symbol}/analyze` - Analyze sentiment
- `POST /agent/query` - Chat with AI agent (NEW)
- `POST /stocks/collect` - Collect data

See [API Reference](backend/docs/api.md) for complete documentation.

---

## 🔐 Security

- ✅ Password hashing (bcrypt)
- ✅ JWT authentication
- ✅ Database SSL/TLS
- ✅ Input validation
- ✅ Protected routes

---

## 📈 Performance

| Operation | Time |
|-----------|------|
| Stock Price | < 100ms |
| Predictions (cached) | < 500ms |
| Predictions (first time) | 30-60s |
| Sentiment Analysis | < 1s |

---

## 🎉 Getting Started

1. **Register** an account at http://localhost:3000/
2. **Collect data** for stocks you want to track
3. **Generate predictions** with AI models
4. **Analyze sentiment** from news articles
5. **Track accuracy** over time

---

## 📞 Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Testing**: Run `./test_endpoints.sh`

---

## 📄 License

This project is for educational and personal use.

---

**🚀 Ready to predict the market? Start now at http://localhost:3000/**

**New in v2.1.0:**
- 🤖 AI Chat Agent for interactive market insights
- 👤 Enhanced user profiles with real account data

*Last Updated: May 11, 2026 • Version 2.1.0*
