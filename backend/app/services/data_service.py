from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random
from loguru import logger

from ..models.trading_models import MarketData
from ..models.data_models import NewsItem, TechnicalIndicators
from ..core.config import settings
from .multi_source_data import MultiSourceDataService
from ..database import SessionLocal
from ..db.repos.market_repository import MarketRepository

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available, using demo data")


class DataService:
    """Service for fetching and managing market data"""
    
    def __init__(self):
        self.cache = {}
        self.multi_source = MultiSourceDataService(settings)
        logger.info("Data service initialized with multi-source providers")
        
        provider_status = self.multi_source.get_provider_status()
        active_providers = [name for name, active in provider_status.items() if active]
        logger.info(f"Active providers: {', '.join(active_providers) if active_providers else 'None (using demo data)'}")
    
    async def get_market_data(self, symbol: str, timeframe: str = "1D") -> List[MarketData]:
        """Get historical market data"""
        logger.info(f"Fetching market data for {symbol}")
        
        historical_data = await self.multi_source.get_historical_data(symbol, days=100)
        
        if historical_data:
            data = []
            for bar in historical_data:
                data.append(MarketData(
                    symbol=symbol,
                    timestamp=bar['timestamp'],
                    open=bar['open'],
                    high=bar['high'],
                    low=bar['low'],
                    close=bar['close'],
                    volume=bar['volume'],
                    vwap=bar.get('vwap', bar['close'])
                ))
            return data
        
        logger.warning(f"No historical data available for {symbol}, using demo data")
        now = datetime.utcnow()
        data = []
        base_price = random.uniform(100, 500)
        for i in range(100):
            timestamp = now - timedelta(days=100-i)
            change = random.uniform(-0.03, 0.03)
            base_price *= (1 + change)
            
            data.append(MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open=base_price * random.uniform(0.99, 1.01),
                high=base_price * random.uniform(1.00, 1.03),
                low=base_price * random.uniform(0.97, 1.00),
                close=base_price,
                volume=random.uniform(1000000, 10000000),
                vwap=base_price * random.uniform(0.995, 1.005)
            ))
        
        return data
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        price = await self.multi_source.get_price(symbol)
        
        if price:
            logger.debug(f"Real price for {symbol}: ${price:.2f}")
            return price
        
        logger.warning(f"No price available for {symbol}, using demo data")
        return random.uniform(100, 500)
    
    async def get_technical_indicators(self, symbol: str) -> TechnicalIndicators:
        """Calculate technical indicators"""
        logger.debug(f"Calculating technical indicators for {symbol}")
        
        # Demo indicators
        # In production, calculate from real market data
        price = await self.get_current_price(symbol)
        
        return TechnicalIndicators(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            sma_20=price * random.uniform(0.98, 1.02),
            sma_50=price * random.uniform(0.96, 1.04),
            sma_200=price * random.uniform(0.92, 1.08),
            ema_12=price * random.uniform(0.99, 1.01),
            ema_26=price * random.uniform(0.98, 1.02),
            rsi=random.uniform(20, 80),
            macd=random.uniform(-5, 5),
            macd_signal=random.uniform(-5, 5),
            macd_histogram=random.uniform(-2, 2),
            bollinger_upper=price * 1.02,
            bollinger_middle=price,
            bollinger_lower=price * 0.98,
            volume_sma=random.uniform(1000000, 5000000)
        )
    
    async def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Get recent news for symbol"""
        logger.debug(f"Fetching news for {symbol}")
        
        # Demo news
        news_templates = [
            "{symbol} reports strong Q{q} earnings",
            "{symbol} announces new product line",
            "Analysts upgrade {symbol} to buy",
            "{symbol} expands into new markets",
            "CEO discusses {symbol} future growth",
            "{symbol} faces regulatory scrutiny",
            "Market volatility affects {symbol}",
            "{symbol} partnership announcement"
        ]
        
        news = []
        for i in range(min(limit, 5)):
            sentiment = random.uniform(-0.8, 0.8)
            news.append(NewsItem(
                id=f"news_{i}",
                title=random.choice(news_templates).format(symbol=symbol, q=random.randint(1, 4)),
                summary=f"Market analysis and updates for {symbol}",
                source=random.choice(["Bloomberg", "Reuters", "CNBC", "WSJ"]),
                symbols=[symbol],
                sentiment_score=sentiment,
                published_at=datetime.utcnow() - timedelta(hours=i)
            ))
        
        return news
    
    async def get_market_snapshot(self, symbols: List[str]) -> Dict:
        """Get snapshot of multiple symbols"""
        snapshot = await self.multi_source.get_market_snapshot(symbols)
        
        if not snapshot:
            snapshot = {}
        
        real_data_count = len(snapshot)
        
        for symbol in symbols:
            if symbol not in snapshot or not snapshot[symbol].get('price'):
                logger.warning(f"No provider data for {symbol}, using demo fallback")
                snapshot[symbol] = {
                    'price': await self.get_current_price(symbol),
                    'change_pct': random.uniform(-5, 5),
                    'volume': random.uniform(1000000, 10000000),
                    'is_demo': True
                }
        
        logger.info(f"Market snapshot: {real_data_count} real, {len(symbols) - real_data_count} demo")
        
        db = SessionLocal()
        try:
            snapshots_data = []
            for symbol, data in snapshot.items():
                price = data.get('price', 0.0)
                
                if not price or price <= 0:
                    logger.warning(f"Skipping empty snapshot for {symbol}")
                    continue
                
                indicators = data.get('indicators', {})
                if data.get('is_demo'):
                    indicators['data_source'] = 'demo'
                elif indicators:
                    indicators['data_source'] = 'provider'
                else:
                    indicators = {'data_source': 'provider'}
                
                snapshots_data.append({
                    'symbol': symbol,
                    'price': price,
                    'change_pct': data.get('change_pct', 0.0),
                    'volume': data.get('volume', 0.0),
                    'high': data.get('high'),
                    'low': data.get('low'),
                    'open_price': data.get('open'),
                    'indicators': indicators
                })
            
            if snapshots_data:
                MarketRepository.bulk_create_snapshots(db, snapshots_data)
                logger.debug(f"Saved {len(snapshots_data)} market snapshots to database")
        except Exception as e:
            logger.error(f"Error saving market snapshots: {e}")
        finally:
            db.close()
        
        return snapshot
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all data providers"""
        return self.multi_source.get_provider_status()


# Global instance
data_service = DataService()
