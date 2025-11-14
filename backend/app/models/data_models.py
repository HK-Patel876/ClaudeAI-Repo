from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class NewsItem(BaseModel):
    id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    source: str
    url: Optional[str] = None
    symbols: List[str] = []
    sentiment_score: Optional[float] = None
    published_at: datetime
    created_at: datetime = datetime.utcnow()


class TechnicalIndicators(BaseModel):
    symbol: str
    timestamp: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    volume_sma: Optional[float] = None


class SystemMetrics(BaseModel):
    timestamp: datetime
    active_positions: int
    open_orders: int
    daily_trades: int
    win_rate: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: float
    total_pnl: float
    daily_pnl: float
    cpu_usage: float
    memory_usage: float
    api_latency_ms: float


class Alert(BaseModel):
    id: Optional[str] = None
    level: str  # info, warning, error, critical
    title: str
    message: str
    category: str  # risk, execution, data, system
    timestamp: datetime = datetime.utcnow()
    acknowledged: bool = False
