# Changelog

All notable changes to the Stock Market Prediction System.

---

## [2.1.0] - 2026-05-11

### Added
- 🤖 **AI Chat Agent Page** - Interactive chat interface with AI assistant
  - New page: `frontend/pages/agent.html`
  - Endpoint: `POST /agent/query`
  - Quick question buttons for common queries
  - Beautiful chat UI with message history
  - Fallback mechanism for when Azure OpenAI is unavailable

- 👤 **Enhanced User Profile** - Display actual user information
  - New endpoint: `GET /auth/me`
  - Shows real username, email, and account creation date
  - Fetches data from backend API on page load
  - Updated profile page with live data

- 🔄 **AI Agent Fallback Mechanism**
  - Keyword-based intent classification when Azure OpenAI is unavailable
  - Automatic symbol extraction from queries
  - Supports price, prediction, sentiment, and comparison queries
  - 10-second timeout with graceful degradation

### Changed
- Updated navigation menu on all pages to include AI Agent link
- Updated `test_endpoints.sh` to test 14 endpoints (was 13)
- Updated README.md to reflect new features (v2.1.0)
- Enhanced error handling in AI agent

### Fixed
- Profile page now displays actual user data instead of placeholder
- AI agent works even when Azure OpenAI connection fails

### Documentation
- Added `docs/NEW_FEATURES.md` - Comprehensive new features guide
- Added `docs/AI_AGENT_FALLBACK.md` - Fallback mechanism documentation
- Updated README.md with new features and version
- Created CHANGELOG.md

---

## [2.0.0] - 2026-05-11

### Added
- Complete frontend redesign with exact color specifications
- 9 brand new HTML pages from scratch
- Single unified CSS file (`frontend/css/main.css`)
- Responsive design for mobile/tablet/desktop
- Emoji icons throughout the interface
- Comprehensive documentation in `docs/` directory

### Changed
- Implemented exact color scheme: cards (#e1e6e8), buttons (#2baff7)
- All buttons fully rounded (border-radius: 9999px)
- Flattened directory structure (removed nested `frontend/frontend/`)
- Moved all documentation to `docs/` directory

### Removed
- 200+ unnecessary files from previous version
- Old CSS files (components.css, dashboard.css, responsive.css)
- Old JS files (11 files including app.js, auth.js, etc.)
- Node.js dependencies (package.json, node_modules/)
- Old documentation files

### Fixed
- TensorFlow compatibility for macOS x86_64 (downgraded to 2.15.0)
- NumPy version conflict (downgraded to 1.26.x)
- Python version requirement (changed to 3.11)
- Database configuration for Neon PostgreSQL with SSL

---

## [1.0.0] - Initial Release

### Features
- LSTM neural networks for stock price prediction
- Sentiment analysis with TextBlob & VADER
- Real-time stock data from Yahoo Finance
- JWT authentication with bcrypt encryption
- PostgreSQL database with SQLModel ORM
- RESTful API with 12 endpoints
- Basic frontend interface

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 2.1.0 | 2026-05-11 | AI Chat Agent + Enhanced Profile |
| 2.0.0 | 2026-05-11 | Complete Frontend Redesign |
| 1.0.0 | 2026-05-11 | Initial Release |

---

## Upgrade Guide

### From 2.0.0 to 2.1.0

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Restart backend** (new endpoint added)
   ```bash
   cd backend
   source .venv/bin/activate
   python -m app.server
   ```

3. **Access new features**
   - AI Chat Agent: http://localhost:3000/pages/agent.html
   - Enhanced Profile: http://localhost:3000/pages/profile.html

4. **Test new endpoints**
   ```bash
   ./test_endpoints.sh
   ```
   Expected: 14/14 tests passing

---

## Breaking Changes

### 2.1.0
- None (backward compatible)

### 2.0.0
- Complete frontend rewrite (not compatible with v1.0.0 frontend)
- Removed Node.js dependencies
- Changed to pure HTML/CSS/JS

---

## Known Issues

### 2.1.0
- Azure OpenAI connection timeout (fallback mechanism handles this)
- NEWS_API_KEY not configured (optional feature)

### Solutions
- AI Agent: Uses fallback mechanism automatically
- News API: Add NEWS_API_KEY to `.env` file if needed

---

## Future Roadmap

### Version 2.2.0 (Planned)
- [ ] Chat history persistence
- [ ] Export chat conversations
- [ ] Edit profile information
- [ ] Change password functionality
- [ ] Upload profile picture
- [ ] View login history

### Version 3.0.0 (Planned)
- [ ] Real-time WebSocket updates
- [ ] Portfolio tracking
- [ ] Custom watchlists
- [ ] Email notifications
- [ ] Mobile app
- [ ] Multi-language support

---

## Contributors

- Development Team
- AI Assistant (Kiro)

---

## License

This project is for educational and personal use.

---

*Last Updated: May 11, 2026*  
*Current Version: 2.1.0*  
*Status: Production Ready*
