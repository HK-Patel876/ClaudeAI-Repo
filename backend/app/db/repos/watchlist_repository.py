from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from ...models.database_models import Watchlist, Alert


class WatchlistRepository:
    
    @staticmethod
    def add_symbol(
        db: Session,
        symbol: str,
        user_id: str = "default",
        notes: str = None
    ) -> Watchlist:
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == user_id,
            Watchlist.symbol == symbol
        ).first()
        
        if existing:
            return existing
        
        watchlist_item = Watchlist(
            user_id=user_id,
            symbol=symbol,
            notes=notes
        )
        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)
        logger.info(f"Added {symbol} to watchlist")
        return watchlist_item
    
    @staticmethod
    def remove_symbol(
        db: Session,
        symbol: str,
        user_id: str = "default"
    ) -> bool:
        deleted = db.query(Watchlist).filter(
            Watchlist.user_id == user_id,
            Watchlist.symbol == symbol
        ).delete()
        db.commit()
        if deleted:
            logger.info(f"Removed {symbol} from watchlist")
        return deleted > 0
    
    @staticmethod
    def get_watchlist(db: Session, user_id: str = "default") -> List[Watchlist]:
        return db.query(Watchlist).filter(
            Watchlist.user_id == user_id
        ).order_by(desc(Watchlist.added_at)).all()
    
    @staticmethod
    def is_symbol_in_watchlist(
        db: Session,
        symbol: str,
        user_id: str = "default"
    ) -> bool:
        return db.query(Watchlist).filter(
            Watchlist.user_id == user_id,
            Watchlist.symbol == symbol
        ).first() is not None


class AlertRepository:
    
    @staticmethod
    def create_alert(
        db: Session,
        symbol: str,
        alert_type: str,
        condition: str,
        threshold: float,
        user_id: str = "default",
        message: str = None,
        extra_metadata: dict = None
    ) -> Alert:
        alert = Alert(
            user_id=user_id,
            symbol=symbol,
            alert_type=alert_type,
            condition=condition,
            threshold=threshold,
            message=message,
            extra_metadata=extra_metadata
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.info(f"Created alert for {symbol}: {condition} {threshold}")
        return alert
    
    @staticmethod
    def get_active_alerts(
        db: Session,
        user_id: str = "default",
        symbol: Optional[str] = None
    ) -> List[Alert]:
        query = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_active == True
        )
        if symbol:
            query = query.filter(Alert.symbol == symbol)
        return query.order_by(desc(Alert.created_at)).all()
    
    @staticmethod
    def get_triggered_alerts(
        db: Session,
        user_id: str = "default"
    ) -> List[Alert]:
        return db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.triggered_at.isnot(None)
        ).order_by(desc(Alert.triggered_at)).all()
    
    @staticmethod
    def trigger_alert(db: Session, alert_id: int) -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.triggered_at = datetime.utcnow()
            alert.is_active = False
            db.commit()
            db.refresh(alert)
            logger.info(f"Alert {alert_id} triggered for {alert.symbol}")
        return alert
    
    @staticmethod
    def delete_alert(db: Session, alert_id: int) -> bool:
        deleted = db.query(Alert).filter(Alert.id == alert_id).delete()
        db.commit()
        return deleted > 0
    
    @staticmethod
    def check_alerts(
        db: Session,
        symbol: str,
        current_price: float,
        user_id: str = "default"
    ) -> List[Alert]:
        active_alerts = AlertRepository.get_active_alerts(db, user_id, symbol)
        triggered = []
        
        for alert in active_alerts:
            should_trigger = False
            
            if alert.condition == 'ABOVE' and current_price > alert.threshold:
                should_trigger = True
            elif alert.condition == 'BELOW' and current_price < alert.threshold:
                should_trigger = True
            elif alert.condition == 'EQUALS' and abs(current_price - alert.threshold) < 0.01:
                should_trigger = True
            
            if should_trigger:
                AlertRepository.trigger_alert(db, alert.id)
                triggered.append(alert)
        
        return triggered
