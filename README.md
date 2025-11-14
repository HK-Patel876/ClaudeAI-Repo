# 🤖 AI Trading System

An advanced autonomous AI trading platform with multi-agent architecture, real-time analytics, and comprehensive risk management.

## ✨ Features

### 🧠 Multi-Agent AI System
- **Technical Analyst**: Analyzes price patterns, indicators (RSI, MACD, Moving Averages)
- **News Analyst**: Processes news sentiment and market events
- **Fundamental Analyst**: Evaluates company fundamentals and growth metrics  
- **Risk Manager**: Enforces position limits, stop-losses, and risk controls

### 📊 Advanced Dashboard
- **Live Market Blotter**: Real-time price updates via WebSocket
- **Agent Insights Panel**: See AI agent analysis and consensus voting
- **Portfolio Performance Charts**: Historical P&L and asset allocation
- **Positions & Orders Grids**: Track all trades and positions
- **Live News Ticker**: Rotating news with sentiment analysis
- **System Metrics**: CPU, memory, latency, and trading stats

### ⚡ Trading Capabilities
- **Paper Trading Mode**: Test strategies risk-free
- **Multi-Asset Support**: Stocks, crypto, forex (extensible)
- **Risk Management**: Automated position sizing and stop-losses
- **Quick Trade Execution**: One-click AI-powered trading

### 🔒 Safety Features
- Position size limits (default: 10% max)
- Daily loss limits (default: 5% max)
- Risk manager with veto power
- Paper trading by default

## 🏗️ Architecture

### Backend (FastAPI)
- **API Layer**: RESTful endpoints + WebSocket streaming
- **Services**: Data ingestion, AI orchestration, trading execution, risk management
- **Multi-Agent System**: Collaborative AI decision-making
- **Real-time Updates**: WebSocket broadcasts for live data

### Frontend (React)
- **Dashboard Components**: 8+ specialized components
- **Real-time Charts**: Recharts for performance visualization
- **WebSocket Client**: Live market data streaming
- **Responsive Design**: Modern, gradient-based UI

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Installation

1. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

3. **Configure Environment** (Optional)
```bash
cp .env.example .env
# Edit .env with your API keys (or leave empty for demo mode)
```

### Running the System

**Option 1: Use the startup script**
```bash
chmod +x start.sh
./start.sh
```

**Option 2: Manual start**
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --host localhost --port 8000 --reload

# Terminal 2: Start frontend
cd frontend
npm start
```

The dashboard will be available at: `http://localhost:5000`

## 📖 Usage

### Analyzing a Symbol
1. Go to the "AI Agent Insights" panel
2. Enter a stock symbol (e.g., AAPL, TSLA)
3. Click "Analyze" to see multi-agent analysis
4. Review agent votes, confidence scores, and risk assessment

### Executing a Trade
1. Use the "Quick Trade" panel
2. Enter symbol and click "Execute AI Trade"
3. System will:
   - Gather market data and news
   - Run all AI agents
   - Check risk limits
   - Execute if approved

### Monitoring Portfolio
- View positions, orders, and P&L in real-time
- Track performance with interactive charts
- Monitor system metrics and alerts

## 🎨 Dashboard Components

| Component | Features |
|-----------|----------|
| **Market Blotter** | Live prices, volume, trends for top symbols |
| **Agent Insights** | Multi-agent analysis with vote breakdowns |
| **Portfolio Chart** | 30-day performance + asset allocation pie chart |
| **Positions Grid** | Active positions with P&L tracking |
| **Orders Grid** | Order history with cancel functionality |
| **News Ticker** | Rotating news headlines with sentiment scores |
| **System Metrics** | Resource usage and trading statistics |
| **Trading Panel** | One-click AI-powered trade execution |

## 🔧 Configuration

Edit `backend/app/core/config.py`:

```python
# Risk Management
MAX_POSITION_SIZE = 0.1  # 10% max position size
MAX_DAILY_LOSS = 0.05    # 5% daily loss limit
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss

# Trading Mode
PAPER_TRADING = True  # Use paper trading
ENABLE_AUTO_TRADING = False  # Require manual approval
```

## 🏦 API Endpoints

### Trading
- `GET /api/v1/trading/portfolio` - Get portfolio summary
- `GET /api/v1/trading/positions` - List positions
- `GET /api/v1/trading/orders` - List orders
- `POST /api/v1/trading/analyze/{symbol}` - Analyze symbol
- `POST /api/v1/trading/execute/{symbol}` - Execute trade
- `DELETE /api/v1/trading/orders/{id}` - Cancel order

### Data
- `GET /api/v1/data/market/{symbol}` - Historical data
- `GET /api/v1/data/price/{symbol}` - Current price
- `GET /api/v1/data/indicators/{symbol}` - Technical indicators
- `GET /api/v1/data/news/{symbol}` - News feed
- `GET /api/v1/data/snapshot` - Multi-symbol snapshot

### System
- `GET /api/v1/system/health` - Health check
- `GET /api/v1/system/metrics` - System metrics
- `GET /api/v1/system/alerts` - Active alerts
- `GET /api/v1/system/config` - Get/update config

### WebSocket
- `WS /ws` - Real-time market updates

## 📊 Trading Strategies Supported

1. **Technical Analysis**: RSI, MACD, Moving Averages, Bollinger Bands
2. **Sentiment Analysis**: News and social media sentiment
3. **Fundamental Analysis**: Financial metrics and growth indicators
4. **Risk Management**: Automated position sizing and stop-losses

## 🛡️ Risk Management

The system includes multiple layers of protection:

1. **Position Limits**: Maximum position size as % of portfolio
2. **Daily Loss Limits**: Trading halts if daily loss exceeds threshold
3. **Stop Losses**: Automatic exit at predefined loss levels
4. **Risk Manager Agent**: Veto power over risky trades
5. **Paper Trading**: Test strategies without real money

## 🔮 Future Enhancements

- [ ] Live trading integration (Alpaca, Interactive Brokers, Binance)
- [ ] Machine learning model training
- [ ] Backtesting framework
- [ ] More technical indicators
- [ ] Alternative data sources
- [ ] Mobile app
- [ ] Advanced charting
- [ ] Portfolio optimization

## 📝 License

This project is for educational purposes. Use at your own risk.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves risk of loss. Past performance does not guarantee future results. Always do your own research and consult with financial professionals before trading.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

## 📧 Support

For questions or issues, please open a GitHub issue.

---

**Built with ❤️ using FastAPI, React, and AI**
