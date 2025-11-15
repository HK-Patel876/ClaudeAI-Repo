"""
Backtesting API Endpoints
Run historical performance analysis on AI trading strategies
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from loguru import logger

from ...services.backtesting_engine import backtesting_engine

router = APIRouter()


class BacktestRequest(BaseModel):
    """Request model for running a backtest"""
    symbol: str
    start_date: str  # ISO format: "2024-01-01"
    end_date: str  # ISO format: "2024-12-31"
    initial_capital: Optional[float] = 100000.0
    position_size_pct: Optional[float] = 0.1  # 10% of capital per trade
    use_stop_loss: Optional[bool] = True
    use_take_profit: Optional[bool] = True
    min_confidence: Optional[float] = 0.6


class QuickBacktestRequest(BaseModel):
    """Quick backtest with preset timeframes"""
    symbol: str
    timeframe: str  # "1M", "3M", "6M", "1Y", "2Y", "5Y"
    initial_capital: Optional[float] = 100000.0
    min_confidence: Optional[float] = 0.6


@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a comprehensive backtest on a symbol

    Tests AI trading signals against historical data to evaluate performance.
    Returns detailed metrics including win rate, Sharpe ratio, drawdown, etc.

    Example:
    ```json
    {
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
        "min_confidence": 0.6
    }
    ```
    """
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)

        # Validate date range
        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="End date must be after start date"
            )

        days_diff = (end_date - start_date).days
        if days_diff < 30:
            raise HTTPException(
                status_code=400,
                detail="Backtest period must be at least 30 days"
            )

        if days_diff > 1825:  # 5 years
            raise HTTPException(
                status_code=400,
                detail="Backtest period cannot exceed 5 years"
            )

        logger.info(f"Starting backtest for {request.symbol} from {start_date} to {end_date}")

        # Run backtest
        result = await backtesting_engine.run_backtest(
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            position_size_pct=request.position_size_pct,
            use_stop_loss=request.use_stop_loss,
            use_take_profit=request.use_take_profit,
            min_confidence=request.min_confidence
        )

        return {
            "success": True,
            "backtest_result": {
                "symbol": result.symbol,
                "period": {
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                    "days": days_diff
                },
                "capital": {
                    "initial": result.initial_capital,
                    "final": result.final_capital,
                    "total_return_pct": result.total_return_pct
                },
                "trades": {
                    "total": result.total_trades,
                    "winning": result.winning_trades,
                    "losing": result.losing_trades,
                    "win_rate": result.win_rate
                },
                "performance": {
                    "avg_win": result.avg_win,
                    "avg_loss": result.avg_loss,
                    "largest_win": result.largest_win,
                    "largest_loss": result.largest_loss,
                    "profit_factor": result.profit_factor
                },
                "risk_metrics": {
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "max_drawdown_pct": result.max_drawdown_pct
                },
                "trading_metrics": {
                    "avg_hold_time_hours": result.avg_hold_time_hours,
                    "trades_per_day": result.trades_per_day,
                    "best_signal_type": result.best_signal_type
                },
                "signal_performance": result.signal_performance,
                "equity_curve": result.equity_curve,
                "trades": result.trades
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/quick")
async def quick_backtest(request: QuickBacktestRequest):
    """
    Run a quick backtest with preset timeframes

    Timeframes:
    - "1M": Last 1 month
    - "3M": Last 3 months
    - "6M": Last 6 months
    - "1Y": Last 1 year
    - "2Y": Last 2 years
    - "5Y": Last 5 years

    Example:
    ```json
    {
        "symbol": "AAPL",
        "timeframe": "1Y",
        "min_confidence": 0.7
    }
    ```
    """
    try:
        # Calculate date range based on timeframe
        end_date = datetime.now()

        timeframe_map = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365,
            "2Y": 730,
            "5Y": 1825
        }

        if request.timeframe not in timeframe_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(timeframe_map.keys())}"
            )

        days = timeframe_map[request.timeframe]
        start_date = end_date - timedelta(days=days)

        logger.info(f"Quick backtest for {request.symbol} - {request.timeframe}")

        # Run backtest
        result = await backtesting_engine.run_backtest(
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            min_confidence=request.min_confidence
        )

        return {
            "success": True,
            "timeframe": request.timeframe,
            "backtest_result": {
                "symbol": result.symbol,
                "period": {
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                    "days": days
                },
                "capital": {
                    "initial": result.initial_capital,
                    "final": result.final_capital,
                    "total_return_pct": result.total_return_pct
                },
                "trades": {
                    "total": result.total_trades,
                    "winning": result.winning_trades,
                    "losing": result.losing_trades,
                    "win_rate": result.win_rate
                },
                "performance": {
                    "avg_win": result.avg_win,
                    "avg_loss": result.avg_loss,
                    "profit_factor": result.profit_factor,
                    "sharpe_ratio": result.sharpe_ratio
                },
                "risk_metrics": {
                    "max_drawdown": result.max_drawdown,
                    "max_drawdown_pct": result.max_drawdown_pct
                },
                "signal_performance": result.signal_performance,
                "equity_curve": result.equity_curve
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running quick backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/multi-symbol")
async def backtest_multiple_symbols(
    symbols: List[str],
    timeframe: str = "1Y",
    min_confidence: float = 0.6
):
    """
    Run backtests on multiple symbols in parallel

    Useful for comparing strategy performance across different assets.

    Example:
    ```json
    {
        "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA"],
        "timeframe": "1Y",
        "min_confidence": 0.6
    }
    ```
    """
    try:
        import asyncio

        if len(symbols) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 symbols allowed per batch"
            )

        # Calculate date range
        end_date = datetime.now()
        timeframe_map = {
            "1M": 30, "3M": 90, "6M": 180,
            "1Y": 365, "2Y": 730, "5Y": 1825
        }

        if timeframe not in timeframe_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(timeframe_map.keys())}"
            )

        days = timeframe_map[timeframe]
        start_date = end_date - timedelta(days=days)

        logger.info(f"Multi-symbol backtest for {len(symbols)} symbols - {timeframe}")

        async def backtest_one(symbol: str):
            try:
                result = await backtesting_engine.run_backtest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    min_confidence=min_confidence
                )

                return {
                    "symbol": symbol,
                    "success": True,
                    "total_return_pct": result.total_return_pct,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "profit_factor": result.profit_factor
                }
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {e}")
                return {
                    "symbol": symbol,
                    "success": False,
                    "error": str(e)
                }

        # Run all backtests in parallel
        results = await asyncio.gather(*[backtest_one(s) for s in symbols])

        # Calculate summary statistics
        successful = [r for r in results if r.get("success")]

        summary = {
            "total_symbols": len(symbols),
            "successful": len(successful),
            "failed": len(symbols) - len(successful)
        }

        if successful:
            summary["avg_return_pct"] = sum(r["total_return_pct"] for r in successful) / len(successful)
            summary["avg_win_rate"] = sum(r["win_rate"] for r in successful) / len(successful)
            summary["avg_sharpe_ratio"] = sum(r["sharpe_ratio"] for r in successful) / len(successful)
            summary["best_performer"] = max(successful, key=lambda x: x["total_return_pct"])
            summary["worst_performer"] = min(successful, key=lambda x: x["total_return_pct"])

        return {
            "success": True,
            "timeframe": timeframe,
            "summary": summary,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-symbol backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/presets")
async def get_backtest_presets():
    """
    Get preset backtest configurations

    Returns common backtest setups for quick analysis.
    """
    return {
        "success": True,
        "presets": {
            "conservative": {
                "name": "Conservative Strategy",
                "description": "High confidence signals only, strict risk management",
                "min_confidence": 0.8,
                "position_size_pct": 0.05,
                "use_stop_loss": True,
                "use_take_profit": True
            },
            "moderate": {
                "name": "Moderate Strategy",
                "description": "Balanced approach with moderate risk",
                "min_confidence": 0.6,
                "position_size_pct": 0.1,
                "use_stop_loss": True,
                "use_take_profit": True
            },
            "aggressive": {
                "name": "Aggressive Strategy",
                "description": "Lower confidence threshold, larger positions",
                "min_confidence": 0.5,
                "position_size_pct": 0.2,
                "use_stop_loss": True,
                "use_take_profit": False
            },
            "high_frequency": {
                "name": "High Frequency",
                "description": "Maximum trading activity",
                "min_confidence": 0.55,
                "position_size_pct": 0.08,
                "use_stop_loss": True,
                "use_take_profit": True
            }
        },
        "timeframes": {
            "1M": "Last 1 Month",
            "3M": "Last 3 Months",
            "6M": "Last 6 Months",
            "1Y": "Last 1 Year",
            "2Y": "Last 2 Years",
            "5Y": "Last 5 Years"
        },
        "popular_symbols": {
            "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"],
            "crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
            "indices": ["SPY", "QQQ", "DIA"]
        }
    }


@router.get("/backtest/compare")
async def compare_strategies(
    symbol: str = Query(..., description="Symbol to backtest"),
    timeframe: str = Query(default="1Y", description="Timeframe (1M, 3M, 6M, 1Y, 2Y, 5Y)")
):
    """
    Compare different strategy configurations on the same symbol

    Runs multiple backtests with different parameters to find optimal settings.
    """
    try:
        import asyncio

        # Calculate date range
        end_date = datetime.now()
        timeframe_map = {
            "1M": 30, "3M": 90, "6M": 180,
            "1Y": 365, "2Y": 730, "5Y": 1825
        }

        if timeframe not in timeframe_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(timeframe_map.keys())}"
            )

        days = timeframe_map[timeframe]
        start_date = end_date - timedelta(days=days)

        logger.info(f"Strategy comparison for {symbol} - {timeframe}")

        # Define strategies to compare
        strategies = {
            "conservative": {"min_confidence": 0.8, "position_size_pct": 0.05},
            "moderate": {"min_confidence": 0.6, "position_size_pct": 0.1},
            "aggressive": {"min_confidence": 0.5, "position_size_pct": 0.2}
        }

        async def test_strategy(name: str, params: dict):
            try:
                result = await backtesting_engine.run_backtest(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    **params
                )

                return {
                    "strategy": name,
                    "params": params,
                    "success": True,
                    "results": {
                        "total_return_pct": result.total_return_pct,
                        "win_rate": result.win_rate,
                        "total_trades": result.total_trades,
                        "sharpe_ratio": result.sharpe_ratio,
                        "max_drawdown_pct": result.max_drawdown_pct,
                        "profit_factor": result.profit_factor,
                        "avg_hold_time_hours": result.avg_hold_time_hours
                    }
                }
            except Exception as e:
                logger.error(f"Error testing {name} strategy: {e}")
                return {
                    "strategy": name,
                    "params": params,
                    "success": False,
                    "error": str(e)
                }

        # Run all strategies in parallel
        comparisons = await asyncio.gather(*[
            test_strategy(name, params)
            for name, params in strategies.items()
        ])

        # Find best strategy
        successful = [c for c in comparisons if c.get("success")]
        best_strategy = None
        if successful:
            best_strategy = max(
                successful,
                key=lambda x: x["results"]["sharpe_ratio"]  # Use Sharpe ratio as primary metric
            )

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "comparisons": comparisons,
            "best_strategy": best_strategy["strategy"] if best_strategy else None,
            "recommendation": f"Based on Sharpe ratio, the {best_strategy['strategy']} strategy performed best" if best_strategy else "No successful backtests"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
