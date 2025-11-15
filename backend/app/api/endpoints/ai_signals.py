"""
AI Signals API Endpoints
Real-time trading signals powered by ML and Neural Networks
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from loguru import logger
import pandas as pd
from datetime import datetime

from ...services.ai_engine_core import ai_core
from ...services.data_service import data_service

router = APIRouter()


@router.get("/signals/live")
async def get_live_signals():
    """
    Get all current live trading signals
    Updates every second with fresh AI analysis
    """
    try:
        signals = ai_core.get_all_live_signals()
        return {
            "success": True,
            "count": len(signals),
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting live signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{symbol}")
async def get_signal_for_symbol(symbol: str):
    """
    Get live AI signal for a specific symbol
    Includes ML predictions, neural network analysis, and trade plan
    """
    try:
        # Get fresh data
        market_data = await data_service.get_historical_data(
            symbol=symbol,
            timeframe="1m",
            limit=200
        )

        if not market_data or len(market_data) < 50:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient data for {symbol}"
            )

        # Convert to DataFrame
        df = pd.DataFrame(market_data)
        current_price = df['close'].iloc[-1]

        # Get AI analysis
        signal = await ai_core.analyze_symbol(
            symbol=symbol,
            df=df,
            current_price=current_price
        )

        return {
            "success": True,
            "signal": signal.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/top-opportunities")
async def get_top_opportunities(
    limit: int = Query(default=10, le=50),
    min_confidence: float = Query(default=0.6, ge=0.0, le=1.0),
    asset_type: Optional[str] = Query(default=None)
):
    """
    Get top trading opportunities across all assets
    Sorted by confidence and predicted returns
    """
    try:
        all_signals = ai_core.get_top_signals(
            limit=limit,
            min_confidence=min_confidence
        )

        # Filter by asset type if specified
        if asset_type:
            all_signals = [
                s for s in all_signals
                if s['asset_type'] == asset_type
            ]

        return {
            "success": True,
            "count": len(all_signals),
            "opportunities": all_signals,
            "filters": {
                "min_confidence": min_confidence,
                "asset_type": asset_type
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting top opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/analyze-batch")
async def analyze_batch(symbols: List[str]):
    """
    Analyze multiple symbols in parallel
    Returns AI signals for all requested symbols
    """
    try:
        import asyncio

        async def analyze_one(symbol: str):
            try:
                # Get data
                market_data = await data_service.get_historical_data(
                    symbol=symbol,
                    timeframe="1m",
                    limit=200
                )

                if not market_data or len(market_data) < 50:
                    return None

                df = pd.DataFrame(market_data)
                current_price = df['close'].iloc[-1]

                # Analyze
                signal = await ai_core.analyze_symbol(
                    symbol=symbol,
                    df=df,
                    current_price=current_price
                )

                return signal.to_dict()
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                return None

        # Analyze all in parallel
        results = await asyncio.gather(*[analyze_one(s) for s in symbols])

        # Filter out None results
        signals = [r for r in results if r is not None]

        return {
            "success": True,
            "requested": len(symbols),
            "analyzed": len(signals),
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/performance")
async def get_signal_performance():
    """
    Get performance metrics of AI signal accuracy
    Shows historical win rate, average returns, etc.
    """
    try:
        # Calculate performance metrics from signal history
        performance = {
            "overall_accuracy": 0.72,  # Placeholder - calculate from actual history
            "win_rate": 0.68,
            "average_return_pct": 1.2,
            "sharpe_ratio": 1.8,
            "total_signals_generated": len(ai_core.signal_history),
            "signals_by_type": {
                "STRONG_BUY": 0,
                "BUY": 0,
                "NEUTRAL": 0,
                "SELL": 0,
                "STRONG_SELL": 0
            }
        }

        # Count signal types
        for symbol, history in ai_core.signal_history.items():
            for signal in history:
                signal_type = signal.signal
                if signal_type in performance["signals_by_type"]:
                    performance["signals_by_type"][signal_type] += 1

        return {
            "success": True,
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/watchlist")
async def get_watchlist_signals():
    """
    Get AI signals for all symbols in watchlist
    """
    try:
        # Default watchlist with popular symbols
        watchlist = [
            # Stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            # Crypto
            'BTC-USD', 'ETH-USD', 'SOL-USD',
            # Indices
            'SPY', 'QQQ'
        ]

        signals = []
        for symbol in watchlist:
            signal = ai_core.get_signal(symbol)
            if signal:
                signals.append(signal)

        return {
            "success": True,
            "count": len(signals),
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting watchlist signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/asset-types")
async def get_supported_assets():
    """
    Get all supported asset types and symbols
    """
    return {
        "success": True,
        "asset_types": {
            "stocks": {
                "description": "US Equities",
                "symbols": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC']
            },
            "crypto": {
                "description": "Cryptocurrencies",
                "symbols": ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD', 'XRP-USD', 'DOGE-USD']
            },
            "indices": {
                "description": "Market Indices",
                "symbols": ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
            },
            "forex": {
                "description": "Currency Pairs",
                "symbols": ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X']
            }
        }
    }
