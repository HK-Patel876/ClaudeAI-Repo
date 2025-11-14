from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from loguru import logger

from ...models.database_models import Trade, Order


class TradeRepository:
    
    @staticmethod
    def create_trade(
        db: Session,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        value: float,
        order_type: str = "MARKET",
        status: str = "FILLED",
        ai_decision: dict = None,
        extra_metadata: dict = None
    ) -> Trade:
        trade = Trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            value=value,
            order_type=order_type,
            status=status,
            ai_decision=ai_decision,
            extra_metadata=extra_metadata
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        logger.info(f"Saved trade: {side} {quantity} {symbol} @ ${price}")
        return trade
    
    @staticmethod
    def get_recent_trades(
        db: Session,
        limit: int = 100,
        symbol: Optional[str] = None
    ) -> List[Trade]:
        query = db.query(Trade)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.order_by(desc(Trade.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_trades_by_timeframe(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        symbol: Optional[str] = None
    ) -> List[Trade]:
        query = db.query(Trade).filter(
            Trade.timestamp >= start_time,
            Trade.timestamp <= end_time
        )
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        return query.order_by(Trade.timestamp).all()
    
    @staticmethod
    def get_trade_statistics(
        db: Session,
        start_time: Optional[datetime] = None
    ) -> Dict:
        query = db.query(Trade)
        if start_time:
            query = query.filter(Trade.timestamp >= start_time)
        
        trades = query.all()
        if not trades:
            return {
                'total_trades': 0,
                'total_value': 0.0,
                'buy_trades': 0,
                'sell_trades': 0
            }
        
        return {
            'total_trades': len(trades),
            'total_value': sum(t.value for t in trades),
            'buy_trades': len([t for t in trades if t.side == 'BUY']),
            'sell_trades': len([t for t in trades if t.side == 'SELL'])
        }


class OrderRepository:
    
    @staticmethod
    def create_order(
        db: Session,
        order_id: str,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        status: str,
        price: float = None,
        time_in_force: str = "GTC",
        filled_qty: float = 0.0,
        filled_avg_price: float = None,
        extra_metadata: dict = None
    ) -> Order:
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            status=status,
            price=price,
            time_in_force=time_in_force,
            filled_qty=filled_qty,
            filled_avg_price=filled_avg_price,
            extra_metadata=extra_metadata
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        logger.info(f"Saved order: {order_id} - {side} {quantity} {symbol}")
        return order
    
    @staticmethod
    def update_order_status(
        db: Session,
        order_id: str,
        status: str,
        filled_qty: float = None,
        filled_avg_price: float = None
    ) -> Optional[Order]:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = status
            if filled_qty is not None:
                order.filled_qty = filled_qty
            if filled_avg_price is not None:
                order.filled_avg_price = filled_avg_price
            db.commit()
            db.refresh(order)
        return order
    
    @staticmethod
    def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
        return db.query(Order).filter(Order.order_id == order_id).first()
    
    @staticmethod
    def get_recent_orders(
        db: Session,
        limit: int = 100,
        symbol: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Order]:
        query = db.query(Order)
        if symbol:
            query = query.filter(Order.symbol == symbol)
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(desc(Order.timestamp)).limit(limit).all()
