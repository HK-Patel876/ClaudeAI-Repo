from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Trading System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # Backend runs on port 8000, frontend on port 3000
    
    # Database
    DATABASE_URL: Optional[str] = None
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENCRYPTION_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Trading APIs - Stocks
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"
    
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    POLYGON_API_KEY: Optional[str] = None
    
    # Trading APIs - Crypto
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    
    COINBASE_API_KEY: Optional[str] = None
    COINBASE_API_SECRET: Optional[str] = None
    
    # AI Models
    OPENAI_API_KEY: Optional[str] = None
    
    def get_available_providers(self) -> dict:
        """Check which data providers are configured"""
        return {
            'alpaca': bool(self.ALPACA_API_KEY and self.ALPACA_SECRET_KEY),
            'alpha_vantage': bool(self.ALPHA_VANTAGE_API_KEY),
            'polygon': bool(self.POLYGON_API_KEY),
            'binance': bool(self.BINANCE_API_KEY and self.BINANCE_SECRET_KEY),
            'coinbase': bool(self.COINBASE_API_KEY and self.COINBASE_API_SECRET),
        }
    
    # Risk Management
    MAX_POSITION_SIZE: float = 0.1  # 10% of portfolio
    MAX_DAILY_LOSS: float = 0.05  # 5% daily loss limit
    STOP_LOSS_PERCENTAGE: float = 0.02  # 2% stop loss
    
    # System
    PAPER_TRADING: bool = True  # Start with paper trading
    ENABLE_AUTO_TRADING: bool = False  # Require manual approval initially
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
