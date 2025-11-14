from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from ...models.database_models import MarketSnapshot


class MarketRepository:
    
    @staticmethod
    def create_snapshot(
        db: Session,
        symbol: str,
        price: float,
        change_pct: float = None,
        volume: float = None,
        high: float = None,
        low: float = None,
        open_price: float = None,
        indicators: dict = None
    ) -> MarketSnapshot:
        snapshot = MarketSnapshot(
            symbol=symbol,
            price=price,
            change_pct=change_pct,
            volume=volume,
            high=high,
            low=low,
            open_price=open_price,
            indicators=indicators
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot
    
    @staticmethod
    def bulk_create_snapshots(
        db: Session,
        snapshots_data: List[Dict]
    ) -> int:
        snapshots = []
        for data in snapshots_data:
            snapshots.append(MarketSnapshot(**data))
        db.bulk_save_objects(snapshots)
        db.commit()
        logger.debug(f"Saved {len(snapshots)} market snapshots")
        return len(snapshots)
    
    @staticmethod
    def get_latest_snapshot(
        db: Session,
        symbol: str
    ) -> Optional[MarketSnapshot]:
        return db.query(MarketSnapshot).filter(
            MarketSnapshot.symbol == symbol
        ).order_by(desc(MarketSnapshot.timestamp)).first()
    
    @staticmethod
    def get_snapshots_by_timeframe(
        db: Session,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MarketSnapshot]:
        return db.query(MarketSnapshot).filter(
            MarketSnapshot.symbol == symbol,
            MarketSnapshot.timestamp >= start_time,
            MarketSnapshot.timestamp <= end_time
        ).order_by(MarketSnapshot.timestamp).all()
    
    @staticmethod
    def get_recent_snapshots(
        db: Session,
        symbol: str,
        limit: int = 100
    ) -> List[MarketSnapshot]:
        return db.query(MarketSnapshot).filter(
            MarketSnapshot.symbol == symbol
        ).order_by(desc(MarketSnapshot.timestamp)).limit(limit).all()
    
    @staticmethod
    def delete_old_snapshots(db: Session, days: int = 90) -> int:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(MarketSnapshot).filter(
            MarketSnapshot.timestamp < cutoff_date
        ).delete()
        db.commit()
        logger.info(f"Deleted {deleted} old market snapshots")
        return deleted
