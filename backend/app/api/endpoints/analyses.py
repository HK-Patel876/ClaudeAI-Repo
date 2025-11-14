from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from ...database import get_db
from ...db.repos.analysis_repository import AnalysisRepository
from ...db.repos.trade_repository import TradeRepository
from ...utils import server_error, validation_error

router = APIRouter(tags=["analyses"])


@router.get("/analyses")
async def get_analyses(
    limit: int = Query(50, ge=1, le=200),
    symbol: Optional[str] = None,
    agent_type: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        if agent_type:
            analyses = AnalysisRepository.get_analyses_by_agent(db, agent_type, limit)
        else:
            analyses = AnalysisRepository.get_recent_analyses(db, limit, symbol)
        
        return {
            'success': True,
            'data': [
                {
                    'id': analysis.id,
                    'symbol': analysis.symbol,
                    'timestamp': analysis.timestamp.isoformat(),
                    'agent_type': analysis.agent_type,
                    'signal': analysis.signal,
                    'confidence': analysis.confidence,
                    'reasoning': analysis.reasoning,
                    'indicators': analysis.indicators,
                    'market_conditions': analysis.market_conditions,
                    'risk_assessment': analysis.risk_assessment
                }
                for analysis in analyses
            ]
        }
    except Exception as e:
        raise server_error(e, "fetching analyses")


@router.get("/performance")
async def get_performance_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict:
    try:
        start_time = datetime.utcnow() - timedelta(days=days)
        trades = TradeRepository.get_trades_by_timeframe(db, start_time, datetime.utcnow())
        
        if not trades:
            return {
                'success': True,
                'data': {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'cumulative_returns': []
                }
            }
        
        cumulative_pnl = 0.0
        cumulative_returns = []
        winning_trades = 0
        losing_trades = 0
        
        positions = {}
        
        for trade in trades:
            trade_pnl = 0.0
            symbol = trade.symbol
            
            if trade.side == 'BUY':
                if symbol not in positions:
                    positions[symbol] = []
                positions[symbol].append({
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp
                })
            
            elif trade.side == 'SELL':
                if trade.extra_metadata and 'entry_price' in trade.extra_metadata:
                    entry_price = trade.extra_metadata['entry_price']
                    trade_pnl = (trade.price - entry_price) * trade.quantity
                elif symbol in positions and positions[symbol]:
                    remaining_qty = trade.quantity
                    total_cost = 0.0
                    
                    while remaining_qty > 0 and positions[symbol]:
                        pos = positions[symbol][0]
                        qty_to_close = min(remaining_qty, pos['quantity'])
                        
                        total_cost += qty_to_close * pos['price']
                        remaining_qty -= qty_to_close
                        pos['quantity'] -= qty_to_close
                        
                        if pos['quantity'] <= 0:
                            positions[symbol].pop(0)
                    
                    closed_qty = trade.quantity - remaining_qty
                    if closed_qty > 0:
                        avg_entry = total_cost / closed_qty
                        trade_pnl = (trade.price - avg_entry) * closed_qty
                else:
                    avg_price = trade.value / trade.quantity if trade.quantity > 0 else trade.price
                    estimated_entry = avg_price * 0.98
                    trade_pnl = (trade.price - estimated_entry) * trade.quantity
                
                if trade_pnl > 0:
                    winning_trades += 1
                elif trade_pnl < 0:
                    losing_trades += 1
            
            cumulative_pnl += trade_pnl
            cumulative_returns.append({
                'timestamp': trade.timestamp.isoformat(),
                'value': cumulative_pnl
            })
        
        total_closed_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0.0
        
        max_drawdown = 0.0
        peak = 0.0
        for point in cumulative_returns:
            if point['value'] > peak:
                peak = point['value']
            drawdown = (peak - point['value']) / peak if peak > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        returns = [point['value'] for point in cumulative_returns]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = (mean_return / std_dev) if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        return {
            'success': True,
            'data': {
                'total_trades': len(trades),
                'win_rate': round(win_rate, 2),
                'total_pnl': round(cumulative_pnl, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown * 100, 2),
                'cumulative_returns': cumulative_returns
            }
        }
    except Exception as e:
        raise server_error(e, "calculating performance metrics")
