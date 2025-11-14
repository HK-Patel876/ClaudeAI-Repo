from fastapi import APIRouter, HTTPException
from typing import List
from loguru import logger

from ...models.data_models import NewsItem, TechnicalIndicators
from ...models.trading_models import MarketData
from ...services.data_service import data_service
from ...utils import server_error, validation_error

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/market/{symbol}", response_model=List[MarketData])
async def get_market_data(symbol: str, timeframe: str = "1D", limit: int = 100):
    """Get historical market data"""
    try:
        data = await data_service.get_market_data(symbol, timeframe)
        return data[-limit:]
    except Exception as e:
        raise server_error(e, f"fetching market data for {symbol}")


@router.get("/price/{symbol}")
async def get_current_price(symbol: str):
    """Get current price for symbol"""
    try:
        price = await data_service.get_current_price(symbol)
        return {'symbol': symbol, 'price': price}
    except Exception as e:
        raise server_error(e, f"fetching price for {symbol}")


@router.get("/indicators/{symbol}", response_model=TechnicalIndicators)
async def get_indicators(symbol: str):
    """Get technical indicators for symbol"""
    try:
        indicators = await data_service.get_technical_indicators(symbol)
        return indicators
    except Exception as e:
        raise server_error(e, f"fetching indicators for {symbol}")


@router.get("/news/{symbol}", response_model=List[NewsItem])
async def get_news(symbol: str, limit: int = 10):
    """Get recent news for symbol"""
    try:
        news = await data_service.get_news(symbol, limit)
        return news
    except Exception as e:
        raise server_error(e, f"fetching news for {symbol}")


@router.get("/snapshot")
async def get_market_snapshot(symbols: str = "AAPL,MSFT,GOOGL,TSLA,AMZN"):
    """Get market snapshot for multiple symbols"""
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        snapshot = await data_service.get_market_snapshot(symbol_list)
        return snapshot
    except Exception as e:
        raise server_error(e, "fetching market snapshot")


@router.get("/chart/{symbol}")
async def get_chart_data(symbol: str, timeframe: str = "1D", limit: int = 500):
    """Get chart data in lightweight-charts format"""
    try:
        data = await data_service.get_market_data(symbol, timeframe)
        
        if not data:
            return {"candles": [], "volume": []}
        
        candles = []
        volumes = []
        
        for item in data[-limit:]:
            candles.append({
                "time": int(item.timestamp.timestamp()),
                "open": float(item.open),
                "high": float(item.high),
                "low": float(item.low),
                "close": float(item.close)
            })
            volumes.append(float(item.volume))
        
        return {
            "candles": candles,
            "volume": volumes,
            "symbol": symbol,
            "timeframe": timeframe
        }
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        raise server_error(e, f"fetching chart data for {symbol}")


@router.get("/symbols/search")
async def search_symbols(q: str = ""):
    """Search for stock symbols"""
    try:
        common_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'AMD',
            'NFLX', 'DIS', 'ORCL', 'INTC', 'CSCO', 'ADBE', 'CRM', 'PYPL',
            'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO',
            'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD'
        ]
        
        if not q:
            return common_symbols[:12]
        
        query = q.upper()
        filtered = [s for s in common_symbols if query in s]
        
        return filtered[:20]
    except Exception as e:
        raise server_error(e, "searching symbols")
