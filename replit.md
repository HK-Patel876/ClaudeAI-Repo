# 🤖 AI Trading System

## Overview
An advanced autonomous AI trading platform with multi-agent architecture, real-time analytics, and comprehensive risk management. This system combines a FastAPI backend with a React frontend dashboard featuring 8+ specialized components for comprehensive market analysis and trading.

## Recent Changes
- **2025-11-14 (Latest)**: Simplified Chart System - Clean Modal Design ✅
  - **Complete Chart Redesign**:
    - Replaced complex TradingView implementation with simple, functional chart modal
    - **Click any stock symbol** in Market Blotter to view interactive chart
    - Professional area charts using Recharts library
    - 5 timeframe options: 1D, 1W, 1M, 3M, 1Y
    - Clean dark theme with smooth animations
    - Fast loading with proper error handling
    
  - **Dashboard Improvements**:
    - Simplified layout - removed complex grid system
    - Cleaner component organization
    - Better visual hierarchy and spacing
    - Professional design with gradient accents
    - Removed over-engineered state management
    
  - **Technical Improvements**:
    - Charts load data via REST API (reliable, no WebSocket issues)
    - Eliminated memory leaks from drawing tools
    - Faster page load times
    - More maintainable codebase
    - Better error handling and loading states
    
  - **Expanded Technical Analysis (7 Indicators)**:
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Moving Averages (SMA-20, SMA-50)
    - Bollinger Bands (upper, middle, lower)
    - Stochastic Oscillator (K/D crossover)
    - ATR (Average True Range - volatility)
    - Volume Analysis (trend detection)
    - Each indicator returns individual buy/sell/hold signal
    - Aggregated recommendation with confidence scores
    
  - **Intelligent Provider Status Tracking**:
    - Tracks REAL data usage (not just API key presence)
    - Providers show green only when actively used in last 5 minutes
    - Monitors: last_success, last_error, request_count, success_count
    - Accurate display of which providers are actually fetching data
    
  - **Per-Stock Analysis Modal**:
    - Click stocks to view detailed analysis
    - Interactive chart with all technical indicators
    - AI multi-agent consensus breakdown
    - Color-coded buy/sell/hold signals
    - Individual agent votes with confidence

- **2025-11-14**: Database persistence, settings system, and enhanced dashboard ✅
  - **PostgreSQL Database Integration**:
    - 7 database tables: ai_analyses, market_snapshots, trades, orders, user_settings, watchlist, alerts
    - Complete repository layer for data persistence
    - AI analysis and market data automatically saved
    
  - **Settings System**:
    - Settings modal with 4 categories (Data & API, Trading Controls, AI Config, Display)
    - User preferences stored in database with Fernet encryption for API keys
    - Settings icon in dashboard header
    
  - **New Dashboard Features**:
    - Watchlist & Alerts panel - track symbols and set price alerts
    - Performance Analytics - cumulative returns, Sharpe ratio, drawdown charts
    - Live Agent Log - real-time AI analysis timeline
    - Improved UI with CSS design tokens and better spacing
    
  - **Bug Fixes**:
    - Fixed performance metrics calculations (PnL, win rate, returns)
    - Preserved real provider data in market snapshots
    - Structured API error handling

- **2025-11-13**: Complete system implementation with multi-source data integration ✅
  - Built FastAPI backend with multi-agent AI system
  - Created React dashboard with 8+ advanced components
  - **Integrated 5 professional data providers**:
    - Alpaca API (stocks + crypto trading)
    - Alpha Vantage (market data + technical indicators)
    - Polygon.io (real-time quotes + historical data)
    - Coinbase Advanced Trade (cryptocurrency data)
    - yfinance (free fallback, no API key required)
  - **Smart fallback system**: Alpaca → Polygon → Alpha Vantage → yfinance
  - **Crypto support**: BTC-USD, ETH-USD, SOL-USD with real-time data
  - Fixed MarketBlotter to display live market data with color-coded changes
  - Added DataSourceIndicator showing active/inactive providers
  - Implemented WebSocket for real-time data streaming
  - Added paper trading mode with risk management
  - Configured deployment for autoscale production hosting
  - **System Status**: Fully operational - works perfectly with OR without API keys!

## Project Architecture

### Backend (FastAPI on localhost:8000)
- **API Layer**: RESTful endpoints + WebSocket streaming
- **Multi-Agent AI System**: 
  - Technical Analyst (RSI, MACD, Moving Averages)
  - News Analyst (Sentiment analysis)
  - Fundamental Analyst (Financial metrics)
  - Risk Manager (Position limits, stop-losses)
- **Services**: Data ingestion, trading execution, risk management
- **Real-time Updates**: WebSocket broadcasts for live market data

### Frontend (React on 0.0.0.0:5000)
- **Dashboard Components** (12 total):
  1. Market Blotter - Live prices and trends
  2. Agent Insights - Multi-agent analysis panel
  3. Portfolio Chart - Performance charts + asset allocation
  4. Positions Grid - Active positions with P&L
  5. Orders Grid - Order history and management
  6. News Ticker - Rotating news with sentiment
  7. System Metrics - Resource usage and stats
  8. Trading Panel - One-click AI-powered trades
  9. **Watchlist Panel** - Symbol tracking with alerts ✨
  10. **Performance Analytics** - Returns, Sharpe, drawdown ✨
  11. **Agent Log** - Real-time AI analysis timeline ✨
  12. **Settings Modal** - User preferences management ✨
- **Real-time Charts**: Recharts for visualization
- **WebSocket Client**: Live data streaming
- **Responsive Design**: Modern CSS with design tokens
- **Settings System**: Persistent user preferences

## Key Features

### 🧠 Multi-Agent AI
- Collaborative decision-making by specialized agents
- Weighted voting system with consensus building
- Risk manager with veto power
- Confidence scoring for all decisions

### 📊 Advanced Dashboard
- Real-time market data via WebSocket
- Interactive performance charts
- Live news ticker with sentiment analysis
- Comprehensive system monitoring

### ⚡ Trading Capabilities
- Paper trading mode (safe testing)
- Multi-asset support (stocks, crypto extensible)
- Automated risk management
- One-click AI-powered execution

### 🔒 Safety Features
- Position size limits (10% max)
- Daily loss limits (5% max)
- Automated stop-losses (2%)
- Risk manager oversight
- Paper trading by default

## Dependencies

### Backend
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- WebSockets: Real-time communication
- Loguru: Logging
- Psutil: System metrics
- **Data Providers** (all optional):
  - alpaca-py: Alpaca trading API
  - alpha-vantage: Alpha Vantage market data
  - polygon-api-client: Polygon.io real-time data
  - coinbase-advanced-py: Coinbase crypto API
  - yfinance: Free stock/crypto data (always available)

### Frontend
- React 18: UI framework
- Recharts: Data visualization
- Axios: HTTP client
- Lucide React: Icons

## Configuration

### Environment Variables (.env)
- `PAPER_TRADING`: Enable paper trading (default: true)
- `ENABLE_AUTO_TRADING`: Allow automated trades (default: false)
- `MAX_POSITION_SIZE`: Max position as % of portfolio (default: 0.1)
- `MAX_DAILY_LOSS`: Daily loss limit as % (default: 0.05)
- `STOP_LOSS_PERCENTAGE`: Stop loss % (default: 0.02)

### API Keys (All Optional - System Works Without Them!)
The system uses yfinance by default and works perfectly without any API keys. Add API keys for enhanced features:

- **Alpaca** (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`): 
  - Sign up: https://alpaca.markets/
  - Free paper trading, real-time stock quotes
  
- **Alpha Vantage** (`ALPHA_VANTAGE_API_KEY`):
  - Sign up: https://www.alphavantage.co/support/#api-key
  - Free tier: 25 requests/day, historical data
  
- **Polygon.io** (`POLYGON_API_KEY`):
  - Sign up: https://polygon.io/
  - Real-time quotes, <20ms latency
  
- **Coinbase** (`COINBASE_API_KEY`, `COINBASE_API_SECRET`):
  - Sign up: https://portal.cdp.coinbase.com/
  - Advanced crypto trading and real-time data

**Priority**: Add Alpaca first for best stock data, then Polygon for real-time updates

## How It Works

1. **Data Ingestion**: System collects market data, news, and technical indicators
2. **AI Analysis**: Multiple specialized agents analyze the data independently
3. **Consensus Building**: Agents vote on trading decisions with confidence scores
4. **Risk Check**: Risk manager validates trade against limits and rules
5. **Execution**: If approved, order is executed (paper or live trading)
6. **Monitoring**: Real-time dashboard shows positions, P&L, and system metrics

## API Endpoints

### Trading
- `GET /api/v1/trading/portfolio` - Portfolio summary
- `GET /api/v1/trading/positions` - Active positions
- `GET /api/v1/trading/orders` - Order history
- `POST /api/v1/trading/analyze/{symbol}` - AI analysis
- `POST /api/v1/trading/execute/{symbol}` - Execute trade

### Data
- `GET /api/v1/data/market/{symbol}` - Historical data
- `GET /api/v1/data/price/{symbol}` - Current price
- `GET /api/v1/data/indicators/{symbol}` - Technical indicators
- `GET /api/v1/data/news/{symbol}` - News feed
- `GET /api/v1/data/snapshot` - Multi-symbol snapshot

### System
- `GET /api/v1/system/health` - Health check
- `GET /api/v1/system/metrics` - System metrics
- `GET /api/v1/system/config` - Configuration

### WebSocket
- `WS /ws` - Real-time market updates

## User Preferences
- Modern, gradient-based UI design
- Multi-feature comprehensive dashboard
- Real-time updates and live data
- AI-driven decision making
- Safety-first approach with paper trading

## Future Enhancements
- Live trading integration (Alpaca, Binance)
- Machine learning model training
- Backtesting framework
- More technical indicators
- Alternative data sources
- Advanced charting
- Mobile app
