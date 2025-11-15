from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from loguru import logger
import asyncio
import json
import random
from datetime import datetime, timedelta

from .core.config import settings
from .core.events import startup_event, shutdown_event
from .api.endpoints import trading, data, system, settings as settings_api, watchlist, analyses, ai_signals, backtesting
from .api.endpoints.signals_stream import websocket_signals_stream
from .services.data_service import data_service
from .services.ai_scheduler import ai_scheduler
from .services.ai_engine_core import ai_core
from .database import init_db
from .models import database_models

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Autonomous AI Trading System with Multi-Agent Architecture"
)

# CORS middleware - restrict origins in production
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# In debug mode, allow all origins for development
if settings.DEBUG:
    origins.append("*")
    logger.warning("DEBUG mode: CORS allows all origins")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trading.router, prefix=settings.API_PREFIX)
app.include_router(data.router, prefix=settings.API_PREFIX)
app.include_router(system.router, prefix=settings.API_PREFIX)
app.include_router(settings_api.router, prefix=settings.API_PREFIX)
app.include_router(watchlist.router, prefix=settings.API_PREFIX)
app.include_router(analyses.router, prefix=settings.API_PREFIX)
app.include_router(ai_signals.router, prefix=settings.API_PREFIX, tags=["AI Signals"])
app.include_router(backtesting.router, prefix=settings.API_PREFIX, tags=["Backtesting"])

# Startup and shutdown events
@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database...")
    init_db()
    await startup_event(app)

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_event(app)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                dead_connections.append(connection)

        # Remove dead connections
        for connection in dead_connections:
            try:
                self.active_connections.remove(connection)
                logger.info(f"Removed dead connection. Active: {len(self.active_connections)}")
            except ValueError:
                pass  # Already removed


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            
            # Echo back (can be used for heartbeat)
            await websocket.send_json({
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/chart/{symbol}/{timeframe}")
async def chart_stream_endpoint(websocket: WebSocket, symbol: str, timeframe: str):
    """WebSocket endpoint for chart real-time updates"""
    await websocket.accept()
    logger.info(f"Chart stream connected for {symbol} on {timeframe}")
    
    timeframe_seconds = {
        '1s': 1,
        '5s': 5,
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '1h': 3600,
        '4h': 14400,
        '1D': 86400,
        '1W': 604800
    }
    
    interval = timeframe_seconds.get(timeframe, 60)
    current_candle = None
    candle_start_time = None
    
    try:
        while True:
            current_price = await data_service.get_current_price(symbol)
            current_time = datetime.utcnow()
            
            if timeframe.endswith('s'):
                timestamp_seconds = int(current_time.timestamp())
                candle_start_seconds = (timestamp_seconds // interval) * interval
                candle_start = datetime.utcfromtimestamp(candle_start_seconds)
            elif timeframe.endswith('m'):
                minutes = int(timeframe[:-1])
                timestamp_minutes = int(current_time.timestamp() // 60)
                candle_start_minutes = (timestamp_minutes // minutes) * minutes
                candle_start = datetime.utcfromtimestamp(candle_start_minutes * 60)
            elif timeframe.endswith('h'):
                hours = int(timeframe[:-1])
                timestamp_hours = int(current_time.timestamp() // 3600)
                candle_start_hours = (timestamp_hours // hours) * hours
                candle_start = datetime.utcfromtimestamp(candle_start_hours * 3600)
            elif timeframe == '1D':
                candle_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == '1W':
                days_since_monday = current_time.weekday()
                candle_start = (current_time - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                candle_start = current_time
            
            if current_candle is None or candle_start_time is None or candle_start > candle_start_time:
                current_candle = {
                    'time': int(candle_start.timestamp()),
                    'open': current_price,
                    'high': current_price,
                    'low': current_price,
                    'close': current_price,
                    'volume': random.uniform(100000, 1000000)
                }
                candle_start_time = candle_start
            else:
                current_candle['high'] = max(current_candle['high'], current_price)
                current_candle['low'] = min(current_candle['low'], current_price)
                current_candle['close'] = current_price
                current_candle['volume'] += random.uniform(10000, 100000)
            
            await websocket.send_json({
                'type': 'candle',
                **current_candle
            })
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"Chart stream disconnected for {symbol} on {timeframe}")
    except Exception as e:
        logger.error(f"Chart stream error for {symbol} on {timeframe}: {e}")


@app.websocket("/ws/market-stream/{symbol}/{timeframe}")
async def market_stream_endpoint(websocket: WebSocket, symbol: str, timeframe: str):
    """WebSocket endpoint for streaming incremental market data with timeframe support"""
    await websocket.accept()
    logger.info(f"Market stream connected for {symbol} on {timeframe}")

    timeframe_seconds = {
        '1s': 1,
        '5s': 5,
        '15s': 15,
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '1H': 3600,
        '1D': 86400,
        '1W': 604800
    }

    interval = timeframe_seconds.get(timeframe, 1)

    current_candle = None
    candle_start_time = None

    try:
        while True:
            current_price = await data_service.get_current_price(symbol)
            current_time = datetime.utcnow()

            if timeframe.endswith('s'):
                timestamp_seconds = int(current_time.timestamp())
                candle_start_seconds = (timestamp_seconds // interval) * interval
                candle_start = datetime.utcfromtimestamp(candle_start_seconds)
            elif timeframe.endswith('m'):
                minutes = int(timeframe[:-1])
                timestamp_minutes = int(current_time.timestamp() // 60)
                candle_start_minutes = (timestamp_minutes // minutes) * minutes
                candle_start = datetime.utcfromtimestamp(candle_start_minutes * 60)
            elif timeframe == '1H':
                candle_start = current_time.replace(minute=0, second=0, microsecond=0)
            elif timeframe == '1D':
                candle_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == '1W':
                days_since_monday = current_time.weekday()
                candle_start = (current_time - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                candle_start = current_time

            if current_candle is None or candle_start_time is None or candle_start > candle_start_time:
                current_candle = {
                    'timestamp': candle_start.isoformat(),
                    'open': current_price,
                    'high': current_price,
                    'low': current_price,
                    'close': current_price,
                    'volume': random.uniform(100000, 1000000)
                }
                candle_start_time = candle_start
            else:
                current_candle['high'] = max(current_candle['high'], current_price)
                current_candle['low'] = min(current_candle['low'], current_price)
                current_candle['close'] = current_price
                current_candle['volume'] += random.uniform(10000, 100000)

            await websocket.send_json({
                'type': 'candle_update',
                'symbol': symbol,
                'timeframe': timeframe,
                'candle': current_candle
            })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"Market stream disconnected for {symbol} on {timeframe}")
    except Exception as e:
        logger.error(f"Market stream error for {symbol} on {timeframe}: {e}")


@app.websocket("/api/v1/ws/signals-stream")
async def signals_stream_endpoint(websocket: WebSocket):
    """
    Real-Time AI Signals WebSocket Stream

    Continuously streams AI-powered trading signals for multiple assets.
    Updates every second with analysis from 75+ technical indicators.

    Example client code:
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/signals-stream');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('New signals:', data.signals);
        };
    """
    await websocket_signals_stream(websocket)


async def stream_market_updates():
    """Background task to stream market updates"""
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'BTC-USD', 'ETH-USD', 'SOL-USD']
    
    # Wait for server to be fully ready
    await asyncio.sleep(2)
    
    while True:
        try:
            if len(manager.active_connections) > 0:
                snapshot = await data_service.get_market_snapshot(symbols)
                await manager.broadcast({
                    'type': 'market_update',
                    'data': snapshot,
                    'timestamp': datetime.utcnow().isoformat()
                })
                logger.debug(f"Broadcast market update to {len(manager.active_connections)} clients")
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Error in market updates stream: {e}")
            await asyncio.sleep(5)


# Background task handle
market_task = None

@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks"""
    global market_task
    market_task = asyncio.create_task(stream_market_updates())
    logger.info("Background market streaming task started")
    
    ai_scheduler.set_broadcast_callback(manager.broadcast)
    await ai_scheduler.start()
    logger.info("AI Scheduler started")


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Trading System</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 10px;
            }
            h1 { margin: 0 0 10px 0; }
            .status { color: #4ade80; font-weight: bold; }
            .link { color: #60a5fa; text-decoration: none; }
            .link:hover { text-decoration: underline; }
            ul { list-style: none; padding: 0; }
            li { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Trading System</h1>
            <p class="status">✅ System Online</p>
            <p>Autonomous multi-agent trading platform with real-time analytics</p>
            
            <h2>API Endpoints</h2>
            <ul>
                <li>📊 <a class="link" href="/docs">API Documentation</a></li>
                <li>🔄 <a class="link" href="/api/v1/system/health">Health Check</a></li>
                <li>📈 <a class="link" href="/api/v1/trading/portfolio">Portfolio</a></li>
                <li>📰 <a class="link" href="/api/v1/data/snapshot">Market Snapshot</a></li>
                <li>⚙️ <a class="link" href="/api/v1/system/metrics">System Metrics</a></li>
            </ul>
            
            <p style="margin-top: 30px; opacity: 0.8; font-size: 14px;">
                Version """ + settings.VERSION + """ | Paper Trading Mode: """ + str(settings.PAPER_TRADING) + """
            </p>
        </div>
    </body>
    </html>
    """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
