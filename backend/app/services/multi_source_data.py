from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import asyncio

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

try:
    from alpha_vantage.timeseries import TimeSeries
    from alpha_vantage.techindicators import TechIndicators
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False

try:
    from polygon import RESTClient as PolygonClient
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False

try:
    from coinbase.wallet.client import Client as CoinbaseClient
    COINBASE_AVAILABLE = True
except ImportError:
    COINBASE_AVAILABLE = False


class MultiSourceDataService:
    """Multi-source data provider with smart fallback logic"""
    
    def __init__(self, config):
        self.config = config
        self.providers = {}
        self.provider_stats = {
            'alpaca': {'last_success': None, 'last_error': None, 'request_count': 0, 'success_count': 0},
            'alpha_vantage': {'last_success': None, 'last_error': None, 'request_count': 0, 'success_count': 0},
            'polygon': {'last_success': None, 'last_error': None, 'request_count': 0, 'success_count': 0},
            'coinbase': {'last_success': None, 'last_error': None, 'request_count': 0, 'success_count': 0},
            'yfinance': {'last_success': None, 'last_error': None, 'request_count': 0, 'success_count': 0}
        }
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all available data providers"""
        
        if ALPACA_AVAILABLE and self.config.ALPACA_API_KEY:
            try:
                self.providers['alpaca_stock'] = StockHistoricalDataClient(
                    api_key=self.config.ALPACA_API_KEY,
                    secret_key=self.config.ALPACA_SECRET_KEY
                )
                self.providers['alpaca_crypto'] = CryptoHistoricalDataClient(
                    api_key=self.config.ALPACA_API_KEY,
                    secret_key=self.config.ALPACA_SECRET_KEY
                )
                logger.info("✅ Alpaca API initialized (stocks & crypto)")
            except Exception as e:
                logger.warning(f"Failed to initialize Alpaca: {e}")
        
        if ALPHA_VANTAGE_AVAILABLE and self.config.ALPHA_VANTAGE_API_KEY:
            try:
                self.providers['alpha_vantage'] = TimeSeries(
                    key=self.config.ALPHA_VANTAGE_API_KEY,
                    output_format='pandas'
                )
                self.providers['alpha_vantage_tech'] = TechIndicators(
                    key=self.config.ALPHA_VANTAGE_API_KEY,
                    output_format='pandas'
                )
                logger.info("✅ Alpha Vantage API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Alpha Vantage: {e}")
        
        if POLYGON_AVAILABLE and self.config.POLYGON_API_KEY:
            try:
                self.providers['polygon'] = PolygonClient(self.config.POLYGON_API_KEY)
                logger.info("✅ Polygon.io API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Polygon: {e}")
        
        if COINBASE_AVAILABLE and self.config.COINBASE_API_KEY:
            try:
                self.providers['coinbase'] = CoinbaseClient(
                    self.config.COINBASE_API_KEY,
                    self.config.COINBASE_API_SECRET
                )
                logger.info("✅ Coinbase API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Coinbase: {e}")
        
        if YFINANCE_AVAILABLE:
            self.providers['yfinance'] = True
            logger.info("✅ yfinance available as fallback")
        
        if not self.providers:
            logger.warning("⚠️ No data providers available - system will use demo data")
    
    def get_provider_status(self) -> Dict[str, dict]:
        """Get status of all providers with actual usage data"""
        status = {}
        now = datetime.utcnow()
        active_threshold = timedelta(minutes=5)
        
        for provider, stats in self.provider_stats.items():
            initialized = self._is_provider_initialized(provider)
            last_success = stats.get('last_success')
            active = initialized and last_success and (now - last_success) < active_threshold
            
            status[provider] = {
                'available': initialized,
                'active': active,
                'last_success': last_success.isoformat() if last_success else None,
                'success_count': stats.get('success_count', 0),
                'request_count': stats.get('request_count', 0)
            }
        
        return status
    
    def _is_provider_initialized(self, provider: str) -> bool:
        """Check if a provider is initialized"""
        if provider == 'alpaca':
            return 'alpaca_stock' in self.providers or 'alpaca_crypto' in self.providers
        elif provider == 'alpha_vantage':
            return 'alpha_vantage' in self.providers
        elif provider == 'polygon':
            return 'polygon' in self.providers
        elif provider == 'coinbase':
            return 'coinbase' in self.providers
        elif provider == 'yfinance':
            return 'yfinance' in self.providers
        return False
    
    def _is_crypto(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency"""
        crypto_suffixes = ['-USD', '/USD', 'USDT', 'BUSD']
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'DOGE', 'MATIC']
        
        for suffix in crypto_suffixes:
            if suffix in symbol:
                return True
        
        for crypto in crypto_symbols:
            if symbol.startswith(crypto):
                return True
                
        return False
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price with smart fallback"""
        
        is_crypto = self._is_crypto(symbol)
        
        if is_crypto:
            return await self._get_crypto_price(symbol)
        else:
            return await self._get_stock_price(symbol)
    
    async def _get_stock_price(self, symbol: str) -> Optional[float]:
        """Get stock price with provider fallback"""
        
        if 'alpaca_stock' in self.providers:
            try:
                self.provider_stats['alpaca']['request_count'] += 1
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self.providers['alpaca_stock'].get_stock_latest_quote(request)
                if quote and symbol in quote:
                    price = float(quote[symbol].ask_price or quote[symbol].bid_price)
                    self.provider_stats['alpaca']['last_success'] = datetime.utcnow()
                    self.provider_stats['alpaca']['success_count'] += 1
                    logger.debug(f"Alpaca: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['alpaca']['last_error'] = datetime.utcnow()
                logger.debug(f"Alpaca failed for {symbol}: {e}")
        
        if 'polygon' in self.providers:
            try:
                self.provider_stats['polygon']['request_count'] += 1
                ticker = self.providers['polygon'].get_last_trade(symbol)
                if ticker:
                    price = float(ticker.price)
                    self.provider_stats['polygon']['last_success'] = datetime.utcnow()
                    self.provider_stats['polygon']['success_count'] += 1
                    logger.debug(f"Polygon: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['polygon']['last_error'] = datetime.utcnow()
                logger.debug(f"Polygon failed for {symbol}: {e}")
        
        if 'alpha_vantage' in self.providers:
            try:
                self.provider_stats['alpha_vantage']['request_count'] += 1
                data, _ = self.providers['alpha_vantage'].get_quote_endpoint(symbol)
                if not data.empty:
                    price = float(data['05. price'].iloc[0])
                    self.provider_stats['alpha_vantage']['last_success'] = datetime.utcnow()
                    self.provider_stats['alpha_vantage']['success_count'] += 1
                    logger.debug(f"Alpha Vantage: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['alpha_vantage']['last_error'] = datetime.utcnow()
                logger.debug(f"Alpha Vantage failed for {symbol}: {e}")
        
        if 'yfinance' in self.providers:
            try:
                self.provider_stats['yfinance']['request_count'] += 1
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d")
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    self.provider_stats['yfinance']['last_success'] = datetime.utcnow()
                    self.provider_stats['yfinance']['success_count'] += 1
                    logger.debug(f"yfinance: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['yfinance']['last_error'] = datetime.utcnow()
                logger.debug(f"yfinance failed for {symbol}: {e}")
        
        logger.warning(f"All providers failed for {symbol}")
        return None
    
    async def _get_crypto_price(self, symbol: str) -> Optional[float]:
        """Get crypto price with provider fallback"""
        
        crypto_symbol = symbol.replace('-', '').replace('/', '')
        
        if 'alpaca_crypto' in self.providers:
            try:
                self.provider_stats['alpaca']['request_count'] += 1
                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Minute,
                    limit=1
                )
                bars = self.providers['alpaca_crypto'].get_crypto_bars(request)
                if bars and symbol in bars:
                    price = float(bars[symbol][-1].close)
                    self.provider_stats['alpaca']['last_success'] = datetime.utcnow()
                    self.provider_stats['alpaca']['success_count'] += 1
                    logger.debug(f"Alpaca Crypto: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['alpaca']['last_error'] = datetime.utcnow()
                logger.debug(f"Alpaca crypto failed for {symbol}: {e}")
        
        if 'coinbase' in self.providers:
            try:
                self.provider_stats['coinbase']['request_count'] += 1
                price_data = self.providers['coinbase'].get_spot_price(currency_pair=symbol)
                if price_data:
                    price = float(price_data.amount)
                    self.provider_stats['coinbase']['last_success'] = datetime.utcnow()
                    self.provider_stats['coinbase']['success_count'] += 1
                    logger.debug(f"Coinbase: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['coinbase']['last_error'] = datetime.utcnow()
                logger.debug(f"Coinbase failed for {symbol}: {e}")
        
        if 'yfinance' in self.providers:
            try:
                self.provider_stats['yfinance']['request_count'] += 1
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d")
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    self.provider_stats['yfinance']['last_success'] = datetime.utcnow()
                    self.provider_stats['yfinance']['success_count'] += 1
                    logger.debug(f"yfinance: {symbol} = ${price:.2f}")
                    return price
            except Exception as e:
                self.provider_stats['yfinance']['last_error'] = datetime.utcnow()
                logger.debug(f"yfinance failed for {symbol}: {e}")
        
        logger.warning(f"All providers failed for crypto {symbol}")
        return None
    
    async def get_historical_data(
        self, 
        symbol: str, 
        days: int = 100
    ) -> List[Dict]:
        """Get historical price data"""
        
        is_crypto = self._is_crypto(symbol)
        
        if is_crypto:
            return await self._get_crypto_historical(symbol, days)
        else:
            return await self._get_stock_historical(symbol, days)
    
    async def _get_stock_historical(self, symbol: str, days: int) -> List[Dict]:
        """Get stock historical data"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        if 'alpaca_stock' in self.providers:
            try:
                self.provider_stats['alpaca']['request_count'] += 1
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
                    start=start_date
                )
                bars = self.providers['alpaca_stock'].get_stock_bars(request)
                if bars and symbol in bars:
                    data = []
                    for bar in bars[symbol]:
                        data.append({
                            'timestamp': bar.timestamp,
                            'open': float(bar.open),
                            'high': float(bar.high),
                            'low': float(bar.low),
                            'close': float(bar.close),
                            'volume': float(bar.volume)
                        })
                    self.provider_stats['alpaca']['last_success'] = datetime.utcnow()
                    self.provider_stats['alpaca']['success_count'] += 1
                    logger.debug(f"Alpaca: Got {len(data)} bars for {symbol}")
                    return data
            except Exception as e:
                self.provider_stats['alpaca']['last_error'] = datetime.utcnow()
                logger.debug(f"Alpaca historical failed for {symbol}: {e}")
        
        if 'yfinance' in self.providers:
            try:
                self.provider_stats['yfinance']['request_count'] += 1
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                if not hist.empty:
                    data = []
                    for idx, row in hist.iterrows():
                        data.append({
                            'timestamp': idx,
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': float(row['Volume'])
                        })
                    self.provider_stats['yfinance']['last_success'] = datetime.utcnow()
                    self.provider_stats['yfinance']['success_count'] += 1
                    logger.debug(f"yfinance: Got {len(data)} bars for {symbol}")
                    return data
            except Exception as e:
                self.provider_stats['yfinance']['last_error'] = datetime.utcnow()
                logger.debug(f"yfinance historical failed for {symbol}: {e}")
        
        return []
    
    async def _get_crypto_historical(self, symbol: str, days: int) -> List[Dict]:
        """Get crypto historical data"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        if 'alpaca_crypto' in self.providers:
            try:
                self.provider_stats['alpaca']['request_count'] += 1
                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=TimeFrame.Day,
                    start=start_date
                )
                bars = self.providers['alpaca_crypto'].get_crypto_bars(request)
                if bars and symbol in bars:
                    data = []
                    for bar in bars[symbol]:
                        data.append({
                            'timestamp': bar.timestamp,
                            'open': float(bar.open),
                            'high': float(bar.high),
                            'low': float(bar.low),
                            'close': float(bar.close),
                            'volume': float(bar.volume)
                        })
                    self.provider_stats['alpaca']['last_success'] = datetime.utcnow()
                    self.provider_stats['alpaca']['success_count'] += 1
                    logger.debug(f"Alpaca Crypto: Got {len(data)} bars for {symbol}")
                    return data
            except Exception as e:
                self.provider_stats['alpaca']['last_error'] = datetime.utcnow()
                logger.debug(f"Alpaca crypto historical failed for {symbol}: {e}")
        
        if 'yfinance' in self.providers:
            try:
                self.provider_stats['yfinance']['request_count'] += 1
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{days}d")
                if not hist.empty:
                    data = []
                    for idx, row in hist.iterrows():
                        data.append({
                            'timestamp': idx,
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': float(row['Volume'])
                        })
                    self.provider_stats['yfinance']['last_success'] = datetime.utcnow()
                    self.provider_stats['yfinance']['success_count'] += 1
                    logger.debug(f"yfinance: Got {len(data)} bars for {symbol}")
                    return data
            except Exception as e:
                self.provider_stats['yfinance']['last_error'] = datetime.utcnow()
                logger.debug(f"yfinance crypto historical failed for {symbol}: {e}")
        
        return []
    
    async def get_market_snapshot(self, symbols: List[str]) -> Dict:
        """Get snapshot for multiple symbols"""
        
        snapshot = {}
        
        for symbol in symbols:
            try:
                price = await self.get_price(symbol)
                if price:
                    hist = await self.get_historical_data(symbol, days=2)
                    
                    if len(hist) >= 2:
                        prev_price = hist[-2]['close']
                        change_pct = ((price - prev_price) / prev_price) * 100
                    else:
                        change_pct = 0.0
                    
                    volume = hist[-1]['volume'] if hist else 0
                    
                    snapshot[symbol] = {
                        'price': price,
                        'change_pct': change_pct,
                        'volume': volume
                    }
                    
            except Exception as e:
                logger.debug(f"Error getting snapshot for {symbol}: {e}")
        
        return snapshot
