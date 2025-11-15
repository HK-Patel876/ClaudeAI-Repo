from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


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
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., AAPL)")
    side: OrderSide
    order_type: OrderType
    quantity: float = Field(..., gt=0, description="Quantity must be positive")
    price: Optional[float] = Field(None, gt=0, description="Price must be positive if specified")
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = Field(0.0, ge=0)
    filled_avg_price: Optional[float] = Field(None, gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        """Validate symbol format"""
        if not re.match(r'^[A-Z]{1,5}(-[A-Z]{3})?$', v.upper()):
            raise ValueError('Symbol must be 1-5 uppercase letters, optionally followed by -XXX for crypto')
        return v.upper()

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validate quantity is reasonable"""
        if v > 1_000_000:
            raise ValueError('Quantity cannot exceed 1,000,000 shares')
        return v


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


# Request/Response Models for API endpoints
class TradeRequest(BaseModel):
    """Request model for executing a trade"""
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: Optional[float] = Field(None, gt=0, le=1_000_000)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        """Validate and uppercase symbol"""
        return v.upper().strip()


class AnalysisRequest(BaseModel):
    """Request model for running AI analysis"""
    symbol: str = Field(..., min_length=1, max_length=10)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        """Validate and uppercase symbol"""
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.upper().strip()


class OrderCancelRequest(BaseModel):
    """Request model for canceling an order"""
    order_id: str = Field(..., min_length=1)


class WatchlistAddRequest(BaseModel):
    """Request model for adding to watchlist"""
    symbol: str = Field(..., min_length=1, max_length=10)
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        """Validate and uppercase symbol"""
        return v.upper().strip()
