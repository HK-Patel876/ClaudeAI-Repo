# CLAUDE.md - AI Assistant Guide for AI Trading System

## Project Overview

**Project Name:** AI Trading System
**Version:** 1.0.0
**Type:** Autonomous AI Trading Platform
**Tech Stack:** FastAPI (Backend) + React (Frontend)
**Purpose:** Educational/Demo trading platform with multi-agent AI architecture

This is an autonomous AI trading system that uses multiple specialized AI agents (Technical Analyst, News Analyst, Fundamental Analyst, Risk Manager) to make collaborative trading decisions. The system includes real-time market data streaming, comprehensive risk management, and a modern dashboard interface.

### Key Features
- Multi-agent AI decision-making system
- Real-time WebSocket market data streaming
- Paper trading mode (default)
- Comprehensive risk management
- Interactive dashboard with live charts
- Technical analysis with 7+ indicators
- News sentiment analysis
- Portfolio tracking and performance visualization

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│  (Port 5000: Dashboard, Charts, Real-time Updates)          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                   (Port 8000: API Server)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ API Endpoints│  │   Services   │  │  WebSocket   │     │
│  │   (Router)   │  │   (Business) │  │  (Streaming) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Multi-Agent  │  │ Data Service │  │  Database    │     │
│  │ AI System    │  │  (Market)    │  │ (SQLAlchemy) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   External APIs       │
         │ - Alpaca (Stocks)     │
         │ - Alpha Vantage       │
         │ - Polygon.io          │
         │ - yfinance (Fallback) │
         └───────────────────────┘
```

### Multi-Agent AI System

The core intelligence consists of 4 specialized agents that collaborate on trading decisions:

1. **Technical Analyst Agent**: Analyzes price patterns and technical indicators (RSI, MACD, Moving Averages, Bollinger Bands, Stochastic, ATR, Volume)
2. **News Analyst Agent**: Processes news sentiment and market events
3. **Fundamental Analyst Agent**: Evaluates company fundamentals (demo mode)
4. **Risk Manager Agent**: Enforces position limits, stop-losses, and has veto power

**Decision Flow:**
```
Market Data → Each Agent Analyzes → Weighted Voting → Consensus Decision
                                         ↓
                          Risk Manager Veto Check
                                         ↓
                            Final Trading Decision
```

---

## Directory Structure

```
Excellent-Project-Pycharm/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   │   ├── endpoints/
│   │   │   │   ├── trading.py      # Trading operations
│   │   │   │   ├── data.py         # Market data endpoints
│   │   │   │   ├── system.py       # System health/metrics
│   │   │   │   ├── settings.py     # User settings
│   │   │   │   ├── watchlist.py    # Watchlist management
│   │   │   │   └── analyses.py     # AI analysis history
│   │   │   └── __init__.py
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py           # Settings and environment
│   │   │   └── events.py           # Startup/shutdown events
│   │   ├── db/                # Database layer
│   │   │   └── repos/              # Repository pattern
│   │   │       ├── analysis_repository.py
│   │   │       ├── market_repository.py
│   │   │       ├── settings_repository.py
│   │   │       ├── trade_repository.py
│   │   │       └── watchlist_repository.py
│   │   ├── models/            # Data models
│   │   │   ├── database_models.py  # SQLAlchemy ORM models
│   │   │   ├── data_models.py      # Pydantic models for data
│   │   │   └── trading_models.py   # Pydantic models for trading
│   │   ├── services/          # Business logic
│   │   │   ├── ai_service.py       # Multi-agent AI orchestration
│   │   │   ├── data_service.py     # Market data fetching
│   │   │   ├── multi_source_data.py # Multi-provider data aggregation
│   │   │   ├── trading_service.py  # Trading execution
│   │   │   └── ai_scheduler.py     # Scheduled AI analysis
│   │   ├── utils/             # Utilities
│   │   │   └── error_responses.py
│   │   ├── database.py        # Database initialization
│   │   └── main.py            # Application entry point
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React frontend application
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── AgentInsights.js     # AI agent analysis display
│   │   │   ├── AgentLog.js          # Agent activity log
│   │   │   ├── Dashboard.js         # Main dashboard layout
│   │   │   ├── MainChart/           # Trading chart component
│   │   │   │   ├── MainChart.js
│   │   │   │   ├── SymbolSearch.js
│   │   │   │   └── index.js
│   │   │   ├── MarketBlotter.js     # Live market prices
│   │   │   ├── NewsTicker.js        # News headlines
│   │   │   ├── OrdersGrid.js        # Orders table
│   │   │   ├── PortfolioChart.js    # Portfolio performance
│   │   │   ├── PositionsGrid.js     # Positions table
│   │   │   ├── StockChartModal.js   # Chart modal
│   │   │   ├── SystemMetrics.js     # System stats
│   │   │   ├── TradingPanel.js      # Quick trade panel
│   │   │   └── WatchlistPanel.js    # Watchlist management
│   │   ├── services/         # API and WebSocket services
│   │   │   ├── api.js               # HTTP API client
│   │   │   └── websocket.js         # WebSocket client
│   │   ├── hooks/            # Custom React hooks
│   │   ├── store/            # State management
│   │   ├── styles/           # CSS styles
│   │   ├── utils/            # Utility functions
│   │   ├── App.js            # Root component
│   │   └── index.js          # Entry point
│   └── package.json          # Node dependencies
│
├── config/                   # Configuration files
├── attached_assets/          # Documentation and design docs
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── .replit                 # Replit configuration
├── main.py                 # Alternative entry point
├── start.sh                # Startup script
├── README.md               # User-facing documentation
├── CLAUDE.md               # This file - AI assistant guide
└── replit.md               # Replit-specific documentation
```

---

## Development Workflows

### Starting the Application

**Method 1: Using the startup script (Recommended)**
```bash
chmod +x start.sh
./start.sh
```

**Method 2: Manual start (separate terminals)**
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm start
```

**Access Points:**
- Frontend Dashboard: http://localhost:5000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/system/health

### Initial Setup

1. **Install Backend Dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install Frontend Dependencies:**
```bash
cd frontend
npm install
```

3. **Configure Environment (Optional):**
```bash
cp .env.example .env
# Edit .env with your API keys
# NOTE: System works without API keys using yfinance as fallback
```

### Database Setup

The application uses SQLite by default (file-based, no setup needed). For PostgreSQL:

```bash
# Set in .env
DATABASE_URL=postgresql://user:password@localhost:5432/trading_db

# Database tables are auto-created on startup via SQLAlchemy
```

---

## Key Conventions and Patterns

### Backend Patterns

#### 1. Repository Pattern
All database operations use the repository pattern for clean separation:

```python
# Example: backend/app/db/repos/trade_repository.py
class TradeRepository:
    @staticmethod
    def create_trade(db: Session, symbol: str, side: str, ...):
        trade = Trade(symbol=symbol, side=side, ...)
        db.add(trade)
        db.commit()
        return trade
```

#### 2. Dependency Injection
FastAPI's dependency injection is used for database sessions:

```python
from ..database import get_db

@router.get("/portfolio")
async def get_portfolio(db: Session = Depends(get_db)):
    # db session automatically managed
    pass
```

#### 3. Pydantic Models
- **Database Models**: SQLAlchemy ORM in `models/database_models.py`
- **API Models**: Pydantic in `models/data_models.py` and `models/trading_models.py`
- Always use Pydantic for request/response validation

#### 4. Service Layer Pattern
Business logic lives in services, not endpoints:

```python
# Good: backend/app/services/trading_service.py
class TradingService:
    async def execute_trade(self, symbol: str, ...):
        # Complex business logic here
        pass

# API endpoint just calls service
@router.post("/execute/{symbol}")
async def execute_trade(symbol: str):
    result = await trading_service.execute_trade(symbol)
    return result
```

#### 5. Async/Await Convention
- All service methods are `async`
- All API endpoints are `async`
- Use `await` for I/O operations (database, external APIs)

#### 6. Error Handling
```python
from fastapi import HTTPException
from loguru import logger

try:
    result = await service_method()
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

#### 7. Logging Convention
Use `loguru` for all logging:

```python
from loguru import logger

logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")  # Only in DEBUG mode
```

### Frontend Patterns

#### 1. Component Structure
- Functional components with hooks (no class components)
- Each component in its own file
- Complex components get a folder (e.g., MainChart/)

#### 2. State Management
- Local state: `useState` hook
- WebSocket updates: Subscriptions via `wsService`
- API calls: Direct axios calls in components

#### 3. WebSocket Usage
```javascript
import wsService from '../services/websocket';

useEffect(() => {
  const unsubscribe = wsService.subscribe('market_update', (data) => {
    // Handle update
  });
  return () => unsubscribe();
}, []);
```

#### 4. API Service Pattern
```javascript
import api from '../services/api';

const data = await api.get('/trading/portfolio');
const result = await api.post('/trading/execute/AAPL');
```

#### 5. Styling Convention
- CSS modules or inline styles
- Consistent color scheme (gradients, dark theme)
- Responsive design with flexbox/grid

---

## Backend Architecture Details

### API Structure

All endpoints are prefixed with `/api/v1` and organized by domain:

#### Trading Endpoints (`api/endpoints/trading.py`)
```python
GET    /api/v1/trading/portfolio         # Portfolio summary
GET    /api/v1/trading/positions         # List positions
GET    /api/v1/trading/orders            # List orders
POST   /api/v1/trading/analyze/{symbol}  # Run AI analysis
POST   /api/v1/trading/execute/{symbol}  # Execute AI trade
DELETE /api/v1/trading/orders/{id}       # Cancel order
```

#### Data Endpoints (`api/endpoints/data.py`)
```python
GET /api/v1/data/market/{symbol}         # Historical OHLCV data
GET /api/v1/data/price/{symbol}          # Current price
GET /api/v1/data/indicators/{symbol}     # Technical indicators
GET /api/v1/data/news/{symbol}           # News feed
GET /api/v1/data/snapshot                # Multi-symbol snapshot
```

#### System Endpoints (`api/endpoints/system.py`)
```python
GET  /api/v1/system/health               # Health check
GET  /api/v1/system/metrics              # System metrics (CPU, memory)
GET  /api/v1/system/alerts               # Active alerts
GET  /api/v1/system/config               # Get configuration
POST /api/v1/system/config               # Update configuration
```

#### Settings Endpoints (`api/endpoints/settings.py`)
```python
GET  /api/v1/settings                    # Get user settings
POST /api/v1/settings                    # Update settings
```

#### Watchlist Endpoints (`api/endpoints/watchlist.py`)
```python
GET    /api/v1/watchlist                 # Get watchlist
POST   /api/v1/watchlist                 # Add symbol
DELETE /api/v1/watchlist/{symbol}        # Remove symbol
```

#### Analyses Endpoints (`api/endpoints/analyses.py`)
```python
GET /api/v1/analyses/{symbol}            # Get analysis history
GET /api/v1/analyses/recent              # Recent analyses
```

### WebSocket Endpoints

#### Main WebSocket (`/ws`)
- Broadcasts market updates every 3 seconds
- Client heartbeat with ping/pong
- Multi-symbol snapshot updates

```javascript
// Client usage
ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'market_update') {
    // Handle market data
  }
};
```

#### Chart Stream (`/ws/chart/{symbol}/{timeframe}`)
- Real-time candlestick updates
- Timeframes: 1s, 5s, 1m, 5m, 15m, 1h, 4h, 1D, 1W
- Sends OHLCV data

#### Market Stream (`/ws/market-stream/{symbol}/{timeframe}`)
- Similar to chart stream but different format
- Incremental candle updates

### Data Service Architecture

**Multi-source fallback strategy:**
```
1. Try Alpaca API (if configured)
   ↓ (if fails or not configured)
2. Try Polygon API (if configured)
   ↓ (if fails or not configured)
3. Try Alpha Vantage (if configured)
   ↓ (if fails or not configured)
4. Use yfinance (always available, no API key)
```

File: `backend/app/services/multi_source_data.py`

### Database Models

File: `backend/app/models/database_models.py`

**Tables:**
- `ai_analyses`: AI agent analysis history
- `market_snapshots`: Historical market data points
- `trades`: Executed trades
- `orders`: Order history and status
- `user_settings`: User preferences and API keys
- `watchlist`: User's watched symbols
- `alerts`: Price and indicator alerts

**ORM Usage:**
```python
from ..models.database_models import Trade, Order, AIAnalysis
from ..database import SessionLocal

db = SessionLocal()
try:
    trade = Trade(symbol="AAPL", side="buy", quantity=10, price=150.0)
    db.add(trade)
    db.commit()
finally:
    db.close()
```

### Configuration

File: `backend/app/core/config.py`

**Key Settings:**
```python
settings = Settings()

# App
settings.APP_NAME          # "AI Trading System"
settings.VERSION           # "1.0.0"
settings.API_PREFIX        # "/api/v1"

# Server
settings.HOST              # "0.0.0.0"
settings.PORT              # 5000

# Trading APIs (all optional)
settings.ALPACA_API_KEY
settings.ALPHA_VANTAGE_API_KEY
settings.POLYGON_API_KEY

# Risk Management
settings.MAX_POSITION_SIZE      # 0.1 (10% max)
settings.MAX_DAILY_LOSS         # 0.05 (5% max)
settings.STOP_LOSS_PERCENTAGE   # 0.02 (2%)

# System
settings.PAPER_TRADING          # True (default)
settings.ENABLE_AUTO_TRADING    # False (default)
```

---

## Frontend Architecture Details

### Component Hierarchy

```
App.js (WebSocket connection)
  └── Dashboard.js (main layout)
      ├── MarketBlotter.js (live prices)
      ├── MainChart/MainChart.js (trading chart)
      ├── AgentInsights.js (AI analysis)
      ├── TradingPanel.js (quick trade)
      ├── PortfolioChart.js (performance)
      ├── PositionsGrid.js (positions table)
      ├── OrdersGrid.js (orders table)
      ├── NewsTicker.js (news headlines)
      ├── SystemMetrics.js (system stats)
      ├── WatchlistPanel.js (watchlist)
      └── AgentLog.js (agent activity)
```

### Service Modules

#### API Service (`frontend/src/services/api.js`)
```javascript
import api from './services/api';

// GET request
const portfolio = await api.get('/trading/portfolio');

// POST request
const result = await api.post('/trading/execute/AAPL', { quantity: 10 });

// DELETE request
await api.delete('/trading/orders/123');
```

Base URL: `http://localhost:8000/api/v1` (via proxy in package.json)

#### WebSocket Service (`frontend/src/services/websocket.js`)
```javascript
import wsService from './services/websocket';

// Subscribe to events
const unsubscribe = wsService.subscribe('market_update', (data) => {
  console.log('Market update:', data);
});

// Cleanup
unsubscribe();
```

Event Types:
- `market_update`: Multi-symbol market snapshot
- `pong`: Heartbeat response
- `candle`: Chart candle update
- `candle_update`: Market stream update

### Key Dependencies

```json
{
  "react": "^18.2.0",
  "axios": "^1.6.0",
  "lightweight-charts": "^5.0.9",  // TradingView-like charts
  "recharts": "^2.10.0",           // Portfolio charts
  "lucide-react": "^0.300.0",      // Icons
  "@headlessui/react": "^1.7.17"   // UI components
}
```

---

## AI Agent System

### Agent Architecture

File: `backend/app/services/ai_service.py`

#### Base Agent Class
```python
class AIAgent:
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.confidence_threshold = 0.6

    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        raise NotImplementedError
```

#### Agent Types (Enum)
```python
class AgentType(str, Enum):
    TECHNICAL = "technical"
    NEWS = "news"
    FUNDAMENTAL = "fundamental"
    RISK = "risk"
```

#### Signal Types (Enum)
```python
class Signal(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
```

### Technical Analyst Agent

**Indicators Calculated:**
1. **RSI** (Relative Strength Index): Oversold (<30) = Buy, Overbought (>70) = Sell
2. **MACD** (Moving Average Convergence Divergence): Line crossovers
3. **Moving Averages**: SMA 20/50 crossover strategy
4. **Bollinger Bands**: Price touching bands
5. **Stochastic Oscillator**: <20 oversold, >80 overbought
6. **ATR** (Average True Range): Volatility measurement
7. **Volume Analysis**: Volume spikes with price movement

**Signal Aggregation:**
- Counts buy vs. sell signals across all indicators
- 2+ buy signals = BUY, 4+ = STRONG_BUY
- 2+ sell signals = SELL, 4+ = STRONG_SELL
- Calculates average confidence from supporting indicators

### Multi-Agent Orchestrator

**Weighted Voting System:**
```python
signal_weights = {
    Signal.STRONG_BUY: +2,
    Signal.BUY: +1,
    Signal.HOLD: 0,
    Signal.SELL: -1,
    Signal.STRONG_SELL: -2
}

# Risk manager veto: STRONG_SELL weight × 3
```

**Decision Threshold:**
- Total score > 1.5: Execute BUY
- Total score < -1.5: Execute SELL
- Otherwise: No trade (HOLD)

**Usage:**
```python
from ..services.ai_service import orchestrator

decision = await orchestrator.get_trading_decision(
    symbol="AAPL",
    market_data={
        'current_price': 150.0,
        'portfolio_value': 100000,
        'daily_pnl': -500,
        ...
    }
)

if decision:
    # decision.action: BUY or SELL
    # decision.quantity: Calculated position size
    # decision.confidence: 0.0 - 1.0
    # decision.agent_votes: List of all agent analyses
    # decision.risk_assessment: Risk manager output
```

---

## Environment Configuration

File: `.env.example` (copy to `.env`)

### Required Settings
```bash
# None - system works without any API keys!
```

### Optional Data Provider APIs

All API keys are optional. The system intelligently falls back to free sources:

```bash
# Alpaca (Recommended for US stocks)
ALPACA_API_KEY=
ALPACA_SECRET_KEY=

# Alpha Vantage (Technical indicators)
ALPHA_VANTAGE_API_KEY=

# Polygon.io (High-quality data)
POLYGON_API_KEY=

# Coinbase (Crypto data)
COINBASE_API_KEY=
COINBASE_API_SECRET=
```

### System Configuration
```bash
# Trading Mode
PAPER_TRADING=true              # Use paper trading (recommended)
ENABLE_AUTO_TRADING=false       # Require manual approval

# Security
SECRET_KEY=change-this-secret-key-in-production

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./trading.db
```

---

## Testing Guidelines

### Backend Testing

**Manual Testing:**
```bash
# Health check
curl http://localhost:8000/api/v1/system/health

# Get market data
curl http://localhost:8000/api/v1/data/price/AAPL

# Run AI analysis
curl -X POST http://localhost:8000/api/v1/trading/analyze/AAPL
```

**API Documentation:**
Visit http://localhost:8000/docs for interactive API testing (Swagger UI)

### Frontend Testing

**Component Testing:**
```bash
cd frontend
npm test
```

**Manual Testing:**
1. Start the application
2. Open http://localhost:5000
3. Check WebSocket connection (green indicator)
4. Test features:
   - Market data updates every 3 seconds
   - AI analysis for any symbol
   - Quick trade execution
   - Chart timeframe switching
   - Watchlist add/remove

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Create endpoint in appropriate router:**
```python
# backend/app/api/endpoints/trading.py
@router.get("/my-new-endpoint")
async def my_new_endpoint(db: Session = Depends(get_db)):
    # Implementation
    return {"status": "success"}
```

2. **Add business logic to service if complex:**
```python
# backend/app/services/trading_service.py
class TradingService:
    async def my_new_feature(self):
        # Complex logic here
        pass
```

3. **Test the endpoint:**
```bash
curl http://localhost:8000/api/v1/trading/my-new-endpoint
```

### Adding a New Database Model

1. **Define model:**
```python
# backend/app/models/database_models.py
class MyNewModel(Base):
    __tablename__ = "my_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Create repository:**
```python
# backend/app/db/repos/my_repository.py
class MyRepository:
    @staticmethod
    def create(db: Session, name: str):
        obj = MyNewModel(name=name)
        db.add(obj)
        db.commit()
        return obj
```

3. **Tables auto-create on startup** (SQLAlchemy handles migrations)

### Adding a New React Component

1. **Create component file:**
```javascript
// frontend/src/components/MyComponent.js
import React, { useState, useEffect } from 'react';

function MyComponent() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Fetch data or subscribe to WebSocket
  }, []);

  return (
    <div className="my-component">
      {/* Component JSX */}
    </div>
  );
}

export default MyComponent;
```

2. **Import and use in Dashboard:**
```javascript
// frontend/src/components/Dashboard.js
import MyComponent from './MyComponent';

// In render:
<MyComponent />
```

### Adding a New Technical Indicator

1. **Add calculation method to TechnicalAnalystAgent:**
```python
# backend/app/services/ai_service.py
class TechnicalAnalystAgent:
    def calculate_my_indicator(self, prices: pd.Series) -> Dict:
        # Calculate indicator
        value = ...
        signal = "BUY" | "SELL" | "NEUTRAL"
        confidence = 0.0 to 1.0

        return {
            'value': value,
            'signal': signal,
            'confidence': confidence
        }
```

2. **Add to analyze method:**
```python
indicators = {
    'rsi': self.calculate_rsi(closes),
    'my_indicator': self.calculate_my_indicator(closes),
    # ... other indicators
}
```

3. **Indicator automatically participates in voting**

### Adding a New AI Agent

1. **Create agent class:**
```python
# backend/app/services/ai_service.py
class MyNewAgent(AIAgent):
    def __init__(self):
        super().__init__(AgentType.MY_TYPE)

    async def analyze(self, symbol: str, data: Dict) -> AgentAnalysis:
        # Analysis logic
        return AgentAnalysis(
            agent_type=self.agent_type,
            symbol=symbol,
            signal=Signal.BUY,  # or SELL, HOLD, etc.
            confidence=0.75,
            reasoning="My reasoning"
        )
```

2. **Add to orchestrator:**
```python
class MultiAgentOrchestrator:
    def __init__(self):
        self.agents = [
            TechnicalAnalystAgent(),
            NewsAnalystAgent(),
            MyNewAgent(),  # Add here
            RiskManagerAgent()
        ]
```

3. **Agent automatically participates in consensus voting**

---

## Code Style and Conventions

### Python (Backend)

**Style Guide:** PEP 8

**Key Points:**
- Use type hints for function parameters and returns
```python
async def my_function(symbol: str, price: float) -> Dict[str, Any]:
    pass
```

- Docstrings for classes and complex functions
```python
def complex_function(param: str) -> int:
    """
    Brief description of what this function does.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
    pass
```

- Async/await for I/O operations
```python
# Good
result = await api_call()

# Bad (blocking)
result = api_call()
```

- Use Pydantic models for validation
```python
class MyRequest(BaseModel):
    symbol: str
    quantity: float

@router.post("/endpoint")
async def endpoint(request: MyRequest):
    # request.symbol and request.quantity are validated
    pass
```

### JavaScript (Frontend)

**Style Guide:** Airbnb JavaScript Style Guide (loosely)

**Key Points:**
- Use const/let, never var
```javascript
const data = await fetchData();
let counter = 0;
```

- Arrow functions for callbacks
```javascript
const filtered = items.filter(item => item.active);
```

- Destructuring for props
```javascript
function MyComponent({ title, onClose }) {
  return <div>{title}</div>;
}
```

- Async/await over promises
```javascript
// Good
const data = await api.get('/data');

// Avoid
api.get('/data').then(data => { ... });
```

### File Naming

**Backend:**
- snake_case for Python files: `trading_service.py`
- PascalCase for classes: `TradingService`
- snake_case for functions: `execute_trade()`

**Frontend:**
- PascalCase for component files: `TradingPanel.js`
- PascalCase for component names: `TradingPanel`
- camelCase for utilities: `wsService.js`
- camelCase for functions: `fetchMarketData()`

---

## Troubleshooting

### Backend Issues

**Issue: "ModuleNotFoundError" when starting backend**
```bash
# Solution: Install dependencies
cd backend
pip install -r requirements.txt
```

**Issue: "Address already in use" error**
```bash
# Solution: Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

**Issue: Database errors**
```bash
# Solution: Delete and recreate database
rm trading.db
# Restart backend - tables auto-create
```

**Issue: "No module named 'app'"**
```bash
# Solution: Run from backend directory with module syntax
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend Issues

**Issue: "Cannot find module" errors**
```bash
# Solution: Install dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue: WebSocket connection failed**
- Check backend is running on port 8000
- Check browser console for errors
- Verify WebSocket URL in `frontend/src/services/websocket.js`

**Issue: API calls fail with CORS error**
- Check CORS middleware in `backend/app/main.py`
- Verify proxy setting in `frontend/package.json`

**Issue: Chart not displaying**
- Check browser console for errors
- Verify lightweight-charts is installed
- Check that symbol data is being received

### Data Provider Issues

**Issue: "No data available" for symbols**
- System falls back to yfinance automatically
- Check symbol format (use Yahoo Finance format)
- Try different symbol (e.g., AAPL, MSFT)

**Issue: Real-time data not updating**
- Check API key configuration in .env
- Verify API provider is active (check provider status)
- System will fallback to yfinance if APIs fail

---

## Performance Considerations

### Backend Optimization

1. **Database Queries:**
   - Use indexes on frequently queried columns (already set on symbol, timestamp)
   - Repository pattern allows easy query optimization

2. **WebSocket Broadcasts:**
   - Update interval: 3 seconds (configurable in main.py)
   - Only broadcasts when clients connected

3. **AI Analysis:**
   - Technical analysis requires 50+ data points
   - Cache market data where appropriate
   - Consider async task queue for heavy analysis

### Frontend Optimization

1. **React Rendering:**
   - Use React.memo for expensive components
   - Avoid unnecessary re-renders
   - Use keys properly in lists

2. **WebSocket Data:**
   - Throttle updates if needed
   - Unsubscribe when components unmount
   - Batch state updates

3. **Chart Performance:**
   - Limit candles shown (default: last 200)
   - Use lightweight-charts for best performance
   - Lazy load historical data

---

## Security Considerations

### Current Security Measures

1. **Paper Trading Default:** System starts in paper trading mode
2. **API Key Storage:** API keys stored in environment variables, not committed
3. **CORS:** Configured for localhost development
4. **Input Validation:** Pydantic validates all API inputs

### Production Checklist

Before deploying to production:

- [ ] Change SECRET_KEY in .env
- [ ] Set up proper database (PostgreSQL)
- [ ] Configure CORS for production domain
- [ ] Use HTTPS for all connections
- [ ] Implement proper authentication
- [ ] Rate limit API endpoints
- [ ] Encrypt sensitive data at rest
- [ ] Set up monitoring and alerting
- [ ] Use environment-specific configs
- [ ] Review and test risk limits

---

## AI Assistant Guidelines

### When Analyzing This Codebase

1. **Start with README.md** for user perspective
2. **Reference this CLAUDE.md** for implementation details
3. **Check backend/app/main.py** for entry point and routing
4. **Review models/** for data structures
5. **Examine services/** for business logic

### When Making Changes

1. **Follow established patterns** (repository, service layer)
2. **Maintain async/await** conventions
3. **Update both backend and frontend** if adding features
4. **Test with paper trading** before any live trading
5. **Preserve risk management** logic
6. **Document new patterns** in this file

### When Adding Features

1. **Database:** Add model → repository → service → endpoint
2. **AI Agent:** Create agent class → add to orchestrator
3. **Frontend:** Create component → integrate with Dashboard
4. **API:** Add endpoint → update frontend API calls

### Common Pitfalls to Avoid

1. **Don't bypass risk management** checks
2. **Don't block async operations** with synchronous code
3. **Don't hardcode configuration** - use settings
4. **Don't skip error handling** - always log and handle
5. **Don't commit API keys** - use .env

---

## Additional Resources

### External Documentation

- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pydantic:** https://docs.pydantic.dev/
- **Lightweight Charts:** https://tradingview.github.io/lightweight-charts/

### API Provider Documentation

- **Alpaca:** https://alpaca.markets/docs/
- **Alpha Vantage:** https://www.alphavantage.co/documentation/
- **Polygon.io:** https://polygon.io/docs/
- **yfinance:** https://pypi.org/project/yfinance/

### Project Files for Reference

- **Architecture Design:** `attached_assets/Structure_*.txt`
- **Project Roadmap:** `attached_assets/Pasted-Building-*.txt`
- **Replit Guide:** `replit.md`

---

## Version History

- **v1.0.0** (Current): Initial release with multi-agent AI system, paper trading, and comprehensive dashboard

---

## Contact and Support

For questions about this codebase:
1. Review this CLAUDE.md file
2. Check the README.md for user documentation
3. Examine relevant source files
4. Consult external documentation links above

**Remember:** This is an educational project for learning about AI trading systems. Always use paper trading mode and never trade with real money without thorough testing and understanding of risks.

---

*Last Updated: 2024-11-14*
*This guide is maintained for AI assistants working on the AI Trading System codebase.*
