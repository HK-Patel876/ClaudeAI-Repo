from fastapi import APIRouter, HTTPException
from typing import List
import psutil
from datetime import datetime
from loguru import logger

from ...models.data_models import SystemMetrics, Alert
from ...services.trading_service import trading_service
from ...services.data_service import data_service
from ...core.config import settings
from ...utils import server_error

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health_check():
    """System health check"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow(),
        'version': settings.VERSION,
        'paper_trading': settings.PAPER_TRADING
    }


@router.get("/providers")
async def get_provider_status():
    """Get data provider status and health information"""
    try:
        provider_status = data_service.get_provider_status()

        # Calculate overall system health
        available_count = sum(1 for p in provider_status.values() if p.get('available'))
        active_count = sum(1 for p in provider_status.values() if p.get('active'))
        working_count = sum(1 for p in provider_status.values() if p.get('can_attempt'))

        overall_health = "healthy" if active_count > 0 else "degraded" if available_count > 0 else "critical"

        return {
            'status': 'success',
            'timestamp': datetime.utcnow(),
            'overall_health': overall_health,
            'summary': {
                'total_providers': len(provider_status),
                'available': available_count,
                'active': active_count,
                'working': working_count
            },
            'providers': provider_status
        }
    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        return server_error(f"Failed to get provider status: {str(e)}")


@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get system metrics"""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        positions = await trading_service.get_positions()
        orders = await trading_service.get_orders()
        open_orders = [o for o in orders if o.status.value in ['pending', 'open']]
        
        # Calculate today's trades
        today = datetime.utcnow().date()
        today_trades = [h for h in trading_service.trade_history 
                       if h['timestamp'].date() == today]
        
        # Calculate win rate (simplified)
        win_rate = 0.5  # Demo value
        
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            active_positions=len(positions),
            open_orders=len(open_orders),
            daily_trades=len(today_trades),
            win_rate=win_rate,
            sharpe_ratio=None,
            max_drawdown=0.0,
            total_pnl=sum(p.unrealized_pnl + p.realized_pnl for p in positions),
            daily_pnl=sum(p.unrealized_pnl for p in positions),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            api_latency_ms=5.0
        )
    except Exception as e:
        raise server_error(e, "fetching system metrics")


@router.get("/alerts", response_model=List[Alert])
async def get_alerts():
    """Get system alerts"""
    # Demo alerts
    alerts = [
        Alert(
            level="info",
            title="System Started",
            message="AI Trading System initialized successfully",
            category="system",
            timestamp=datetime.utcnow()
        )
    ]
    return alerts


@router.get("/config")
async def get_config():
    """Get system configuration"""
    return {
        'paper_trading': settings.PAPER_TRADING,
        'auto_trading': settings.ENABLE_AUTO_TRADING,
        'max_position_size': settings.MAX_POSITION_SIZE,
        'max_daily_loss': settings.MAX_DAILY_LOSS,
        'stop_loss_pct': settings.STOP_LOSS_PERCENTAGE
    }


@router.post("/config")
async def update_config(config: dict):
    """Update system configuration"""
    try:
        if 'auto_trading' in config:
            settings.ENABLE_AUTO_TRADING = config['auto_trading']
        if 'max_position_size' in config:
            settings.MAX_POSITION_SIZE = config['max_position_size']
        
        logger.info(f"Configuration updated: {config}")
        return {'status': 'success', 'config': await get_config()}
    except Exception as e:
        raise server_error(e, "updating config")


@router.get("/providers")
async def get_provider_status():
    """Get status of all data providers"""
    try:
        status = data_service.get_provider_status()
        active_providers = [name for name, info in status.items() if info['active']]
        
        return {
            'providers': status,
            'active_count': len(active_providers),
            'active_providers': active_providers,
            'timestamp': datetime.utcnow()
        }
    except Exception as e:
        raise server_error(e, "fetching provider status")
