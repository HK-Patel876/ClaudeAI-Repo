from fastapi import APIRouter, HTTPException
from typing import List
from loguru import logger

from ...models.trading_models import Order, Position, PortfolioSummary, TradingDecision
from ...services.trading_service import trading_service, risk_service
from ...services.data_service import data_service
from ...services.ai_service import orchestrator
from ...utils import server_error, not_found_error

router = APIRouter(prefix="/trading", tags=["trading"])


@router.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio():
    """Get current portfolio summary"""
    try:
        # Get current prices for all positions
        symbols = list(trading_service.positions.keys())
        current_prices = {}
        for symbol in symbols:
            current_prices[symbol] = await data_service.get_current_price(symbol)
        
        portfolio = await trading_service.get_portfolio_summary(current_prices)
        return portfolio
    except Exception as e:
        raise server_error(e, "fetching portfolio")


@router.get("/positions", response_model=List[Position])
async def get_positions():
    """Get all current positions"""
    try:
        return await trading_service.get_positions()
    except Exception as e:
        raise server_error(e, "fetching positions")


@router.get("/orders", response_model=List[Order])
async def get_orders(limit: int = 50):
    """Get recent orders"""
    try:
        return await trading_service.get_orders(limit)
    except Exception as e:
        raise server_error(e, "fetching orders")


@router.post("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    """Analyze symbol and get trading decision"""
    try:
        logger.info(f"Analyzing {symbol}")
        
        # Gather market data
        current_price = await data_service.get_current_price(symbol)
        indicators = await data_service.get_technical_indicators(symbol)
        news = await data_service.get_news(symbol, limit=10)
        
        # Get current portfolio
        current_prices = {symbol: current_price}
        portfolio = await trading_service.get_portfolio_summary(current_prices)
        
        # Prepare data for AI agents
        market_data = {
            'current_price': current_price,
            'indicators': indicators,
            'news': news,
            'fundamentals': {},
            'portfolio_value': portfolio.total_value,
            'daily_pnl': portfolio.daily_pnl,
            'current_positions': [p.dict() for p in portfolio.positions],
            'proposed_quantity': 0
        }
        
        # Get AI trading decision
        decision = await orchestrator.get_trading_decision(symbol, market_data)
        
        if not decision:
            return {
                'symbol': symbol,
                'decision': 'HOLD',
                'reason': 'No consensus from AI agents',
                'agents': []
            }
        
        # Check risk
        risk_check = await risk_service.check_trade_risk(decision, portfolio)
        
        return {
            'symbol': symbol,
            'decision': decision.action.value,
            'quantity': decision.quantity,
            'price': decision.price,
            'confidence': decision.confidence,
            'risk_check': risk_check,
            'agent_votes': [
                {
                    'agent': a.agent_type.value,
                    'signal': a.signal.value,
                    'confidence': a.confidence,
                    'reasoning': a.reasoning
                } for a in decision.agent_votes
            ]
        }
    except Exception as e:
        raise server_error(e, f"analyzing {symbol}")


@router.post("/execute/{symbol}")
async def execute_trade(symbol: str):
    """Execute trade based on AI decision"""
    try:
        logger.info(f"Executing trade for {symbol}")
        
        # Get analysis first
        analysis = await analyze_symbol(symbol)
        
        if analysis['decision'] == 'HOLD':
            return {'status': 'skipped', 'reason': analysis['reason']}
        
        # Check risk approval
        if not analysis['risk_check']['approved']:
            return {
                'status': 'rejected',
                'reason': 'Risk check failed',
                'risks': analysis['risk_check']['risks']
            }
        
        # Create decision object
        decision = TradingDecision(
            symbol=symbol,
            action=analysis['decision'],
            quantity=analysis['quantity'],
            price=analysis['price'],
            confidence=analysis['confidence'],
            agent_votes=[],
            risk_assessment=analysis['risk_check']
        )
        
        # Place order
        order = await trading_service.place_order(decision)
        
        return {
            'status': 'success',
            'order': order.dict()
        }
    except Exception as e:
        raise server_error(e, f"executing trade for {symbol}")


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order"""
    try:
        success = await trading_service.cancel_order(order_id)
        if success:
            return {'status': 'success', 'message': 'Order cancelled'}
        else:
            raise not_found_error('Order', order_id)
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, f"cancelling order {order_id}")
