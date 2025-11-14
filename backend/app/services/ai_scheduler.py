import asyncio
from datetime import datetime
from loguru import logger
from typing import Dict, List

from ..database import SessionLocal
from ..db.repos.settings_repository import SettingsRepository
from ..db.repos.watchlist_repository import WatchlistRepository
from ..services.ai_service import orchestrator
from ..services.trading_service import trading_service, risk_service
from ..services.data_service import data_service


class AIScheduler:
    def __init__(self):
        self.is_running = False
        self.task = None
        self.broadcast_callback = None
        logger.info("AI Scheduler initialized")
    
    def set_broadcast_callback(self, callback):
        self.broadcast_callback = callback
        logger.info("WebSocket broadcast callback registered")
    
    async def start(self):
        if self.is_running:
            logger.warning("AI Scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting AI Scheduler background task")
        self.task = asyncio.create_task(self._run_analysis_loop())
    
    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("AI Scheduler stopped")
    
    async def _run_analysis_loop(self):
        await asyncio.sleep(5)
        
        while self.is_running:
            try:
                db = SessionLocal()
                try:
                    settings = SettingsRepository.get_or_create_settings(db)
                    interval = settings.analysis_cadence or 60
                    enable_auto_trading = settings.enable_auto_trading or False
                    
                    watchlist_items = WatchlistRepository.get_watchlist(db)
                    symbols = [item.symbol for item in watchlist_items]
                    
                    if not symbols:
                        logger.debug("No symbols in watchlist, skipping analysis")
                        await asyncio.sleep(interval)
                        continue
                    
                    logger.info(f"Starting AI analysis cycle for {len(symbols)} symbols")
                    
                    for symbol in symbols[:5]:
                        try:
                            await self._analyze_symbol(symbol, enable_auto_trading, settings)
                        except Exception as e:
                            logger.error(f"Error analyzing {symbol}: {e}")
                    
                    logger.info(f"AI analysis cycle completed. Next run in {interval}s")
                    
                finally:
                    db.close()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in AI scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_symbol(self, symbol: str, enable_auto_trading: bool, settings):
        try:
            market_data = await data_service.get_market_snapshot([symbol])
            
            if not market_data or symbol not in market_data:
                logger.warning(f"No market data for {symbol}")
                return
            
            symbol_data = market_data[symbol]
            current_price = symbol_data.get('price', 0)
            
            if current_price <= 0:
                logger.warning(f"Invalid price for {symbol}: {current_price}")
                return
            
            analysis_data = {
                'current_price': current_price,
                'indicators': symbol_data.get('indicators'),
                'news': [],
                'fundamentals': {},
                'portfolio_value': 100000,
                'daily_pnl': 0,
                'current_positions': [],
                'proposed_quantity': 10
            }
            
            decision = await orchestrator.get_trading_decision(symbol, analysis_data)
            
            if decision:
                analysis_result = {
                    'symbol': symbol,
                    'decision': decision.action.value,
                    'confidence': decision.confidence,
                    'quantity': decision.quantity,
                    'price': decision.price,
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent_votes': [
                        {
                            'agent': vote.agent_type.value,
                            'signal': vote.signal.value,
                            'confidence': vote.confidence,
                            'reasoning': vote.reasoning
                        }
                        for vote in decision.agent_votes
                    ],
                    'risk_assessment': decision.risk_assessment
                }
                
                if self.broadcast_callback:
                    await self.broadcast_callback({
                        'type': 'ai_analysis',
                        'data': analysis_result,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                logger.info(f"AI Analysis: {symbol} - {decision.action.value} (confidence: {decision.confidence:.2f})")
                
                if enable_auto_trading:
                    await self._execute_auto_trade(decision, settings)
            else:
                logger.debug(f"No clear trading decision for {symbol}")
                
                if self.broadcast_callback:
                    await self.broadcast_callback({
                        'type': 'ai_analysis',
                        'data': {
                            'symbol': symbol,
                            'decision': 'HOLD',
                            'confidence': 0.0,
                            'reasoning': 'No clear consensus from agents',
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
        except Exception as e:
            logger.error(f"Error in _analyze_symbol for {symbol}: {e}")
    
    async def _execute_auto_trade(self, decision, settings):
        try:
            if not settings.paper_trading:
                logger.warning("Auto-trading attempted but paper trading is disabled. Skipping for safety.")
                return
            
            current_prices = {decision.symbol: decision.price}
            portfolio = await trading_service.get_portfolio_summary(current_prices)
            
            risk_check = await risk_service.check_trade_risk(decision, portfolio)
            
            if not risk_check['approved']:
                logger.warning(f"Auto-trade rejected for {decision.symbol}: {risk_check['risks']}")
                return
            
            order = await trading_service.place_order(decision)
            
            logger.warning(f"🤖 AUTO-TRADE EXECUTED: {order.side.value} {order.quantity:.2f} {order.symbol} @ ${order.price:.2f}")
            
            if self.broadcast_callback:
                await self.broadcast_callback({
                    'type': 'auto_trade',
                    'data': {
                        'symbol': order.symbol,
                        'side': order.side.value,
                        'quantity': order.quantity,
                        'price': order.price,
                        'status': order.status.value,
                        'confidence': decision.confidence,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error executing auto-trade: {e}")


ai_scheduler = AIScheduler()
