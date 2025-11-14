from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from datetime import datetime
from ..database import Base

class AIAnalysis(Base):
    """Store AI agent analysis history"""
    __tablename__ = "ai_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    agent_type = Column(String(50), nullable=False)
    signal = Column(String(20))
    confidence = Column(Float)
    reasoning = Column(Text)
    
    indicators = Column(JSON)
    market_conditions = Column(JSON)
    risk_assessment = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketSnapshot(Base):
    """Store historical market data snapshots"""
    __tablename__ = "market_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    price = Column(Float, nullable=False)
    change_pct = Column(Float)
    volume = Column(Float)
    high = Column(Float)
    low = Column(Float)
    open_price = Column(Float)
    
    indicators = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Trade(Base):
    """Store executed trades"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    
    order_type = Column(String(20))
    status = Column(String(20))
    
    ai_decision = Column(JSON)
    extra_metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    """Store order history"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    side = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    order_type = Column(String(20), nullable=False)
    time_in_force = Column(String(20))
    
    status = Column(String(20), nullable=False)
    filled_qty = Column(Float, default=0.0)
    filled_avg_price = Column(Float)
    
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSettings(Base):
    """Store user preferences and settings"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, default="default")
    
    data_refresh_interval = Column(Integer, default=10)
    active_providers = Column(JSON)
    
    alpaca_api_key = Column(String(500))
    alpaca_secret_key = Column(String(500))
    alpha_vantage_api_key = Column(String(500))
    polygon_api_key = Column(String(500))
    coinbase_api_key = Column(String(500))
    coinbase_api_secret = Column(String(500))
    
    paper_trading = Column(Boolean, default=True)
    enable_auto_trading = Column(Boolean, default=False)
    max_position_size = Column(Float, default=0.1)
    max_daily_loss = Column(Float, default=0.05)
    stop_loss_pct = Column(Float, default=0.02)
    
    agent_weights = Column(JSON)
    analysis_cadence = Column(Integer, default=60)
    
    theme = Column(String(20), default="dark")
    layout_density = Column(String(20), default="comfortable")
    show_news_ticker = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Watchlist(Base):
    """Store user watchlist symbols"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, default="default")
    symbol = Column(String(20), nullable=False)
    
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

class Alert(Base):
    """Store price and indicator alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, default="default")
    symbol = Column(String(20), index=True, nullable=False)
    
    alert_type = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    
    is_active = Column(Boolean, default=True)
    triggered_at = Column(DateTime)
    
    message = Column(Text)
    extra_metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
