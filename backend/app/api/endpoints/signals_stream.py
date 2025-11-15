"""
Real-Time AI Signals WebSocket Stream
Continuous signal updates every second for multiple tickers
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Set
from loguru import logger
import asyncio
import json
from datetime import datetime
import pandas as pd

from ...services.ai_engine_core import ai_core
from ...services.data_service import data_service


class SignalsConnectionManager:
    """Manages WebSocket connections for real-time signals"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.watched_symbols: Set[str] = set()
        self.streaming_task = None

    async def connect(self, websocket: WebSocket):
        """Add new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New signals stream connection. Total: {len(self.active_connections)}")

        # Start streaming if this is first connection
        if len(self.active_connections) == 1:
            await self.start_streaming()

    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Signals stream disconnected. Remaining: {len(self.active_connections)}")

        # Stop streaming if no connections
        if len(self.active_connections) == 0:
            self.stop_streaming()

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def start_streaming(self):
        """Start continuous signal generation"""
        if self.streaming_task is None or self.streaming_task.done():
            self.streaming_task = asyncio.create_task(self._stream_signals())
            logger.info("Started real-time signals streaming")

    def stop_streaming(self):
        """Stop streaming task"""
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
            logger.info("Stopped real-time signals streaming")

    async def _stream_signals(self):
        """Continuously generate and broadcast signals"""
        # Default watchlist - can be customized per connection later
        symbols = [
            # Top Stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'AMD',
            # Crypto
            'BTC-USD', 'ETH-USD', 'SOL-USD',
            # Indices
            'SPY', 'QQQ'
        ]

        logger.info(f"Streaming signals for {len(symbols)} symbols")

        while True:
            try:
                # Analyze all symbols in parallel
                signals = await self._analyze_all_symbols(symbols)

                # Broadcast to all connected clients
                message = {
                    "type": "signals_update",
                    "timestamp": datetime.now().isoformat(),
                    "count": len(signals),
                    "signals": signals,
                    "next_update_in_ms": 1000  # 1 second
                }

                await self.broadcast(message)

                # Update every 1 second
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Signals streaming cancelled")
                break
            except Exception as e:
                logger.error(f"Error in signals stream: {e}")
                # Continue streaming even on errors
                await asyncio.sleep(1)

    async def _analyze_all_symbols(self, symbols: List[str]) -> List[dict]:
        """Analyze multiple symbols in parallel"""
        async def analyze_one(symbol: str):
            try:
                # Get market data
                market_data = await data_service.get_market_data(
                    symbol=symbol,
                    timeframe="1m"
                )

                if not market_data or len(market_data) < 50:
                    return None

                # Convert to DataFrame
                df = pd.DataFrame(market_data)
                current_price = df['close'].iloc[-1]

                # Determine asset type
                if '-USD' in symbol or 'USDT' in symbol:
                    asset_type = 'crypto'
                elif '=X' in symbol:
                    asset_type = 'forex'
                elif symbol in ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']:
                    asset_type = 'indices'
                else:
                    asset_type = 'stocks'

                # Get AI analysis
                signal = await ai_core.analyze_symbol(
                    symbol=symbol,
                    df=df,
                    current_price=current_price,
                    asset_type=asset_type
                )

                return signal.to_dict()

            except Exception as e:
                logger.debug(f"Error analyzing {symbol}: {e}")
                return None

        # Analyze all symbols concurrently
        results = await asyncio.gather(*[analyze_one(s) for s in symbols])

        # Filter out None results and return
        return [r for r in results if r is not None]


# Global connection manager
signals_manager = SignalsConnectionManager()


async def websocket_signals_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time AI signals

    Continuously streams AI-powered trading signals for multiple assets
    Updates every second with fresh analysis from 75+ indicators

    Usage:
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/signals-stream');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('New signals:', data.signals);
        };
    """
    await signals_manager.connect(websocket)

    try:
        # Keep connection alive and handle client messages
        while True:
            # Wait for client messages (optional - can be used for commands)
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client commands
                if message.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong', 'timestamp': datetime.now().isoformat()})
                elif message.get('type') == 'subscribe':
                    # Future: Allow clients to customize watched symbols
                    symbols = message.get('symbols', [])
                    await websocket.send_json({
                        'type': 'subscribed',
                        'symbols': symbols,
                        'message': 'Symbol subscription will be supported in future update'
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.debug(f"Error handling client message: {e}")
                continue

    except WebSocketDisconnect:
        logger.info("Client disconnected from signals stream")
    except Exception as e:
        logger.error(f"Error in signals WebSocket: {e}")
    finally:
        signals_manager.disconnect(websocket)
