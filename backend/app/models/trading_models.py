from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class AgentType(str, Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"
    SENTIMENT = "sentiment"
    RISK = "risk"


class Signal(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class MarketData(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None


class Order(BaseModel):
    id: Optional[str] = None
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_avg_price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Position(BaseModel):
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    market_value: float
    cost_basis: float


class AgentAnalysis(BaseModel):
    agent_type: AgentType
    symbol: str
    signal: Signal
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class TradingDecision(BaseModel):
    symbol: str
    action: OrderSide
    quantity: float
    price: Optional[float] = None
    confidence: float
    agent_votes: List[AgentAnalysis]
    risk_assessment: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    positions_value: float
    total_pnl: float
    daily_pnl: float
    positions: List[Position]
    buying_power: float
