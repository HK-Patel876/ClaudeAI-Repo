from typing import List, Optional, Dict
from datetime import datetime
import uuid
from loguru import logger

from ..models.trading_models import (
    Order, Position, OrderSide, OrderType, OrderStatus, 
    PortfolioSummary, TradingDecision
)
from ..core.config import settings
from ..database import SessionLocal
from ..db.repos.trade_repository import TradeRepository, OrderRepository


class TradingService:
    """Service for managing trades and positions"""
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.cash = 100000.0  # Starting capital
        self.initial_capital = 100000.0
        self.trade_history = []
        logger.info(f"Trading service initialized with ${self.cash:,.2f}")
    
    async def place_order(self, decision: TradingDecision) -> Order:
        """Place a trading order"""
        order_id = str(uuid.uuid4())
        
        order = Order(
            id=order_id,
            symbol=decision.symbol,
            side=decision.action,
            order_type=OrderType.MARKET,
            quantity=decision.quantity,
            price=decision.price
        )
        
        # Paper trading simulation
        if settings.PAPER_TRADING:
            # Simulate immediate fill for market orders
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.filled_avg_price = decision.price
            
            # Update positions
            await self._update_position(order)
            
            logger.info(f"✅ Order filled: {order.side.value} {order.quantity} {order.symbol} @ ${decision.price:.2f}")
        else:
            order.status = OrderStatus.PENDING
            logger.warning("Live trading not yet implemented")
        
        self.orders[order_id] = order
        self.trade_history.append({
            'timestamp': datetime.utcnow(),
            'order': order,
            'decision': decision
        })
        
        db = SessionLocal()
        try:
            OrderRepository.create_order(
                db,
                order_id=order_id,
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                order_type=order.order_type.value,
                status=order.status.value,
                price=order.price,
                filled_qty=order.filled_quantity,
                filled_avg_price=order.filled_avg_price
            )
            
            if order.status == OrderStatus.FILLED:
                TradeRepository.create_trade(
                    db,
                    symbol=order.symbol,
                    side=order.side.value,
                    quantity=order.filled_quantity,
                    price=order.filled_avg_price,
                    value=order.filled_quantity * order.filled_avg_price,
                    order_type=order.order_type.value,
                    status="FILLED",
                    ai_decision={'confidence': decision.confidence, 'agent_votes': len(decision.agent_votes)}
                )
        except Exception as e:
            logger.error(f"Error saving order/trade to database: {e}")
        finally:
            db.close()
        
        return order
    
    async def _update_position(self, order: Order):
        """Update position after order fill"""
        symbol = order.symbol
        
        if symbol in self.positions:
            position = self.positions[symbol]
            
            if order.side == OrderSide.BUY:
                # Add to position
                new_quantity = position.quantity + order.filled_quantity
                new_cost = (position.cost_basis + order.filled_quantity * order.filled_avg_price)
                position.quantity = new_quantity
                position.avg_entry_price = new_cost / new_quantity if new_quantity > 0 else 0
                position.cost_basis = new_cost
                self.cash -= order.filled_quantity * order.filled_avg_price
            else:
                # Reduce position
                if order.filled_quantity >= position.quantity:
                    # Close entire position
                    realized_pnl = (order.filled_avg_price - position.avg_entry_price) * position.quantity
                    position.realized_pnl += realized_pnl
                    self.cash += order.filled_quantity * order.filled_avg_price
                    del self.positions[symbol]
                    logger.info(f"Position closed for {symbol}, PnL: ${realized_pnl:,.2f}")
                else:
                    # Partial close
                    realized_pnl = (order.filled_avg_price - position.avg_entry_price) * order.filled_quantity
                    position.quantity -= order.filled_quantity
                    position.realized_pnl += realized_pnl
                    position.cost_basis -= order.filled_quantity * position.avg_entry_price
                    self.cash += order.filled_quantity * order.filled_avg_price
        else:
            # New position
            if order.side == OrderSide.BUY:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    avg_entry_price=order.filled_avg_price,
                    current_price=order.filled_avg_price,
                    unrealized_pnl=0.0,
                    market_value=order.filled_quantity * order.filled_avg_price,
                    cost_basis=order.filled_quantity * order.filled_avg_price
                )
                self.cash -= order.filled_quantity * order.filled_avg_price
                logger.info(f"New position opened for {symbol}")
    
    async def get_portfolio_summary(self, current_prices: Dict[str, float]) -> PortfolioSummary:
        """Get current portfolio summary"""
        positions = []
        total_unrealized_pnl = 0.0
        total_realized_pnl = sum(p.realized_pnl for p in self.positions.values())
        positions_value = 0.0
        
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.current_price)
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = (current_price - position.avg_entry_price) * position.quantity
            
            positions.append(position)
            total_unrealized_pnl += position.unrealized_pnl
            positions_value += position.market_value
        
        total_value = self.cash + positions_value
        total_pnl = total_realized_pnl + total_unrealized_pnl
        daily_pnl = total_pnl  # Simplified
        
        return PortfolioSummary(
            total_value=total_value,
            cash=self.cash,
            positions_value=positions_value,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            positions=positions,
            buying_power=self.cash
        )
    
    async def get_orders(self, limit: int = 50) -> List[Order]:
        """Get recent orders"""
        orders = list(self.orders.values())
        orders.sort(key=lambda x: x.created_at, reverse=True)
        return orders[:limit]
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        return list(self.positions.values())
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.OPEN]:
                order.status = OrderStatus.CANCELLED
                logger.info(f"Order {order_id} cancelled")
                return True
        return False


class RiskService:
    """Service for risk management and compliance"""
    
    def __init__(self):
        self.max_position_size = settings.MAX_POSITION_SIZE
        self.max_daily_loss = settings.MAX_DAILY_LOSS
        self.stop_loss_pct = settings.STOP_LOSS_PERCENTAGE
        logger.info("Risk service initialized")
    
    async def check_trade_risk(self, decision: TradingDecision, portfolio: PortfolioSummary) -> Dict:
        """Check if trade passes risk requirements"""
        risks = []
        approved = True
        
        # Position size check
        trade_value = decision.quantity * decision.price
        position_pct = trade_value / portfolio.total_value if portfolio.total_value > 0 else 0
        
        if position_pct > self.max_position_size:
            risks.append(f"Position size {position_pct*100:.1f}% exceeds limit {self.max_position_size*100:.1f}%")
            approved = False
        
        # Daily loss check
        daily_loss_pct = abs(portfolio.daily_pnl) / portfolio.total_value if portfolio.total_value > 0 else 0
        if daily_loss_pct > self.max_daily_loss:
            risks.append(f"Daily loss {daily_loss_pct*100:.1f}% exceeds limit {self.max_daily_loss*100:.1f}%")
            approved = False
        
        # Buying power check
        if decision.action == OrderSide.BUY:
            if trade_value > portfolio.buying_power:
                risks.append(f"Insufficient buying power: need ${trade_value:,.2f}, have ${portfolio.buying_power:,.2f}")
                approved = False
        
        return {
            'approved': approved,
            'risks': risks,
            'position_pct': position_pct,
            'daily_loss_pct': daily_loss_pct
        }
    
    async def calculate_stop_loss(self, entry_price: float) -> float:
        """Calculate stop loss price"""
        return entry_price * (1 - self.stop_loss_pct)
    
    async def calculate_take_profit(self, entry_price: float, risk_reward_ratio: float = 2.0) -> float:
        """Calculate take profit price"""
        return entry_price * (1 + self.stop_loss_pct * risk_reward_ratio)


# Global instances
trading_service = TradingService()
risk_service = RiskService()
