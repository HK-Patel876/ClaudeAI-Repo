from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from loguru import logger

from ...database import get_db
from ...db.repos.watchlist_repository import WatchlistRepository, AlertRepository
from ...utils import server_error, not_found_error, database_error

router = APIRouter(tags=["watchlist"])


class WatchlistAdd(BaseModel):
    symbol: str
    notes: Optional[str] = None


class AlertCreate(BaseModel):
    symbol: str
    alert_type: str = "PRICE"
    condition: str
    threshold: float
    message: Optional[str] = None


@router.get("/watchlist")
async def get_watchlist(db: Session = Depends(get_db)) -> Dict:
    try:
        watchlist = WatchlistRepository.get_watchlist(db)
        return {
            'success': True,
            'data': [
                {
                    'id': item.id,
                    'symbol': item.symbol,
                    'notes': item.notes,
                    'added_at': item.added_at.isoformat()
                }
                for item in watchlist
            ]
        }
    except Exception as e:
        raise server_error(e, "fetching watchlist")


@router.post("/watchlist")
async def add_to_watchlist(
    item: WatchlistAdd,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        watchlist_item = WatchlistRepository.add_symbol(
            db,
            symbol=item.symbol.upper(),
            notes=item.notes
        )
        return {
            'success': True,
            'message': f'{item.symbol} added to watchlist',
            'data': {
                'id': watchlist_item.id,
                'symbol': watchlist_item.symbol,
                'notes': watchlist_item.notes,
                'added_at': watchlist_item.added_at.isoformat()
            }
        }
    except Exception as e:
        raise database_error(e, "adding to watchlist")


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        removed = WatchlistRepository.remove_symbol(db, symbol.upper())
        if removed:
            return {
                'success': True,
                'message': f'{symbol} removed from watchlist'
            }
        else:
            raise not_found_error('Symbol in watchlist', symbol)
    except HTTPException:
        raise
    except Exception as e:
        raise database_error(e, "removing from watchlist")


@router.get("/alerts")
async def get_alerts(
    active_only: bool = False,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        if active_only:
            alerts = AlertRepository.get_active_alerts(db)
        else:
            all_alerts = AlertRepository.get_active_alerts(db)
            triggered = AlertRepository.get_triggered_alerts(db)
            alerts = all_alerts + triggered
        
        return {
            'success': True,
            'data': [
                {
                    'id': alert.id,
                    'symbol': alert.symbol,
                    'alert_type': alert.alert_type,
                    'condition': alert.condition,
                    'threshold': alert.threshold,
                    'is_active': alert.is_active,
                    'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None,
                    'message': alert.message,
                    'created_at': alert.created_at.isoformat()
                }
                for alert in alerts
            ]
        }
    except Exception as e:
        raise server_error(e, "fetching alerts")


@router.post("/alerts")
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        new_alert = AlertRepository.create_alert(
            db,
            symbol=alert.symbol.upper(),
            alert_type=alert.alert_type,
            condition=alert.condition,
            threshold=alert.threshold,
            message=alert.message
        )
        return {
            'success': True,
            'message': 'Alert created successfully',
            'data': {
                'id': new_alert.id,
                'symbol': new_alert.symbol,
                'condition': new_alert.condition,
                'threshold': new_alert.threshold,
                'created_at': new_alert.created_at.isoformat()
            }
        }
    except Exception as e:
        raise database_error(e, "creating alert")


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    try:
        deleted = AlertRepository.delete_alert(db, alert_id)
        if deleted:
            return {
                'success': True,
                'message': 'Alert deleted successfully'
            }
        else:
            raise not_found_error('Alert', str(alert_id))
    except HTTPException:
        raise
    except Exception as e:
        raise database_error(e, "deleting alert")
