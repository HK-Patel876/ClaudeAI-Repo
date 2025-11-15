from typing import List, Dict, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
from loguru import logger
from functools import wraps
import asyncio
import time

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

from ..utils.data_exceptions import (
    DataProviderError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
    InvalidSymbolError,
    EmptyDataError,
    DataValidationError,
    ProviderUnavailableError
)


# Configuration constants
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 10.0  # seconds
REQUEST_TIMEOUT = 30.0  # seconds
CIRCUIT_BREAKER_THRESHOLD = 5  # failures before opening circuit
CIRCUIT_BREAKER_TIMEOUT = 300  # seconds (5 minutes)


class CircuitBreaker:
    """Circuit breaker to prevent repeated calls to failing providers"""

    def __init__(self, threshold: int = CIRCUIT_BREAKER_THRESHOLD, timeout: int = CIRCUIT_BREAKER_TIMEOUT):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call_failed(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def call_succeeded(self):
        """Record a successful call"""
        self.failure_count = 0
        self.state = "closed"

    def can_attempt(self) -> bool:
        """Check if we can attempt a call"""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed > self.timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False

        # half-open state - allow one attempt
        return True


def validate_price_data(data: Dict, symbol: str) -> bool:
    """Validate price data quality"""
    if not data:
        raise DataValidationError("validation", f"Empty data for {symbol}")

    price = data.get('price') or data.get('close')
    if price is None:
        raise DataValidationError("validation", f"No price field in data for {symbol}")

    if not isinstance(price, (int, float)):
        raise DataValidationError("validation", f"Invalid price type for {symbol}: {type(price)}")

    if price <= 0:
        raise DataValidationError("validation", f"Invalid price value for {symbol}: {price}")

    if price > 1000000:  # Sanity check for extremely high prices
        logger.warning(f"Unusually high price for {symbol}: ${price:,.2f}")

    return True


def validate_historical_data(data: List[Dict], symbol: str, min_bars: int = 1) -> bool:
    """Validate historical data quality"""
    if not data:
        raise EmptyDataError("validation", f"No historical data for {symbol}")

    if len(data) < min_bars:
        raise EmptyDataError("validation", f"Insufficient data for {symbol}: got {len(data)}, need {min_bars}")

    for i, bar in enumerate(data):
        required_fields = ['open', 'high', 'low', 'close', 'volume']
        missing_fields = [f for f in required_fields if f not in bar or bar[f] is None]

        if missing_fields:
            raise DataValidationError(
                "validation",
                f"Missing fields in bar {i} for {symbol}: {missing_fields}"
            )

        # Validate OHLC relationship
        if not (bar['low'] <= bar['open'] <= bar['high'] and
                bar['low'] <= bar['close'] <= bar['high']):
            raise DataValidationError(
                "validation",
                f"Invalid OHLC relationship in bar {i} for {symbol}"
            )

        # Validate positive values
        if any(bar[f] <= 0 for f in ['open', 'high', 'low', 'close']):
            raise DataValidationError(
                "validation",
                f"Non-positive price in bar {i} for {symbol}"
            )

    return True


def retry_with_backoff(max_retries: int = MAX_RETRIES, initial_delay: float = INITIAL_RETRY_DELAY):
    """Decorator for retrying functions with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (NetworkError, RateLimitError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.info(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, MAX_RETRY_DELAY)  # Exponential backoff with cap
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
                except (AuthenticationError, InvalidSymbolError, DataValidationError, EmptyDataError) as e:
                    # Don't retry these errors
                    logger.debug(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                except Exception as e:
                    # Unexpected errors - log and don't retry
                    logger.error(f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}")
                    raise

            # If we get here, all retries failed
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


async def with_timeout(coro, timeout: float = REQUEST_TIMEOUT, provider: str = "unknown"):
    """Execute coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise NetworkError(provider, f"Request timed out after {timeout}s")


class MultiSourceDataService:
    """Multi-source data provider with smart fallback logic"""
    
    def __init__(self, config):
        self.config = config
        self.providers = {}
        self.provider_stats = {
            'alpaca': {
                'last_success': None,
                'last_error': None,
                'last_error_msg': None,
                'request_count': 0,
                'success_count': 0,
                'error_count': 0
            },
            'alpha_vantage': {
                'last_success': None,
                'last_error': None,
                'last_error_msg': None,
                'request_count': 0,
                'success_count': 0,
                'error_count': 0
            },
            'polygon': {
                'last_success': None,
                'last_error': None,
                'last_error_msg': None,
                'request_count': 0,
                'success_count': 0,
                'error_count': 0
            },
            'coinbase': {
                'last_success': None,
                'last_error': None,
                'last_error_msg': None,
                'request_count': 0,
                'success_count': 0,
                'error_count': 0
            },
            'yfinance': {
                'last_success': None,
                'last_error': None,
                'last_error_msg': None,
                'request_count': 0,
                'success_count': 0,
                'error_count': 0
            }
        }
        # Circuit breakers for each provider
        self.circuit_breakers = {
            'alpaca': CircuitBreaker(),
            'alpha_vantage': CircuitBreaker(),
            'polygon': CircuitBreaker(),
            'coinbase': CircuitBreaker(),
            'yfinance': CircuitBreaker()
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
            last_error = stats.get('last_error')
            active = initialized and last_success and (now - last_success) < active_threshold

            circuit_breaker = self.circuit_breakers.get(provider)
            circuit_state = circuit_breaker.state if circuit_breaker else "unknown"
            can_attempt = circuit_breaker.can_attempt() if circuit_breaker else True

            status[provider] = {
                'available': initialized,
                'active': active,
                'circuit_breaker_state': circuit_state,
                'can_attempt': can_attempt,
                'last_success': last_success.isoformat() if last_success else None,
                'last_error': last_error.isoformat() if last_error else None,
                'last_error_msg': stats.get('last_error_msg'),
                'success_count': stats.get('success_count', 0),
                'error_count': stats.get('error_count', 0),
                'request_count': stats.get('request_count', 0),
                'success_rate': (
                    stats.get('success_count', 0) / stats.get('request_count', 1)
                    if stats.get('request_count', 0) > 0 else 0.0
                )
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

    def _record_success(self, provider: str):
        """Record a successful API call"""
        self.provider_stats[provider]['last_success'] = datetime.utcnow()
        self.provider_stats[provider]['success_count'] += 1
        self.circuit_breakers[provider].call_succeeded()

    def _record_failure(self, provider: str, error: Exception):
        """Record a failed API call"""
        self.provider_stats[provider]['last_error'] = datetime.utcnow()
        self.provider_stats[provider]['last_error_msg'] = str(error)
        self.provider_stats[provider]['error_count'] += 1
        self.circuit_breakers[provider].call_failed()

    def _categorize_error(self, error: Exception, provider: str) -> DataProviderError:
        """Categorize generic exceptions into specific error types"""
        error_msg = str(error).lower()

        # Network errors
        if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network', 'unreachable']):
            return NetworkError(provider, f"Network error: {error}", error)

        # Authentication errors
        if any(keyword in error_msg for keyword in ['auth', 'unauthorized', 'forbidden', 'api key', 'invalid key']):
            return AuthenticationError(provider, f"Authentication failed: {error}", error)

        # Rate limit errors
        if any(keyword in error_msg for keyword in ['rate limit', 'too many requests', '429']):
            return RateLimitError(provider, f"Rate limit exceeded: {error}", error)

        # Invalid symbol errors
        if any(keyword in error_msg for keyword in ['invalid symbol', 'not found', 'unknown symbol', '404']):
            return InvalidSymbolError(provider, f"Invalid symbol: {error}", error)

        # Empty data errors
        if any(keyword in error_msg for keyword in ['no data', 'empty', 'not available']):
            return EmptyDataError(provider, f"No data available: {error}", error)

        # Default to generic DataProviderError
        return DataProviderError(provider, f"Provider error: {error}", error)
    
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
        """Get stock price with provider fallback, retry logic, and comprehensive error handling"""

        errors = []  # Track all errors for detailed reporting

        # Try Alpaca
        if 'alpaca_stock' in self.providers and self.circuit_breakers['alpaca'].can_attempt():
            try:
                self.provider_stats['alpaca']['request_count'] += 1
                price = await self._get_alpaca_stock_price(symbol)
                if price:
                    validate_price_data({'price': price}, symbol)
                    self._record_success('alpaca')
                    logger.info(f"✅ Alpaca: {symbol} = ${price:.2f}")
                    return price
            except DataProviderError as e:
                self._record_failure('alpaca', e)
                errors.append(f"Alpaca: {e.message}")
                logger.warning(f"Alpaca failed for {symbol}: {e.message}")
            except Exception as e:
                categorized_error = self._categorize_error(e, 'alpaca')
                self._record_failure('alpaca', categorized_error)
                errors.append(f"Alpaca: {categorized_error.message}")
                logger.warning(f"Alpaca unexpected error for {symbol}: {type(e).__name__}: {e}")

        # Try Polygon
        if 'polygon' in self.providers and self.circuit_breakers['polygon'].can_attempt():
            try:
                self.provider_stats['polygon']['request_count'] += 1
                price = await self._get_polygon_price(symbol)
                if price:
                    validate_price_data({'price': price}, symbol)
                    self._record_success('polygon')
                    logger.info(f"✅ Polygon: {symbol} = ${price:.2f}")
                    return price
            except DataProviderError as e:
                self._record_failure('polygon', e)
                errors.append(f"Polygon: {e.message}")
                logger.warning(f"Polygon failed for {symbol}: {e.message}")
            except Exception as e:
                categorized_error = self._categorize_error(e, 'polygon')
                self._record_failure('polygon', categorized_error)
                errors.append(f"Polygon: {categorized_error.message}")
                logger.warning(f"Polygon unexpected error for {symbol}: {type(e).__name__}: {e}")

        # Try Alpha Vantage
        if 'alpha_vantage' in self.providers and self.circuit_breakers['alpha_vantage'].can_attempt():
            try:
                self.provider_stats['alpha_vantage']['request_count'] += 1
                price = await self._get_alpha_vantage_price(symbol)
                if price:
                    validate_price_data({'price': price}, symbol)
                    self._record_success('alpha_vantage')
                    logger.info(f"✅ Alpha Vantage: {symbol} = ${price:.2f}")
                    return price
            except DataProviderError as e:
                self._record_failure('alpha_vantage', e)
                errors.append(f"Alpha Vantage: {e.message}")
                logger.warning(f"Alpha Vantage failed for {symbol}: {e.message}")
            except Exception as e:
                categorized_error = self._categorize_error(e, 'alpha_vantage')
                self._record_failure('alpha_vantage', categorized_error)
                errors.append(f"Alpha Vantage: {categorized_error.message}")
                logger.warning(f"Alpha Vantage unexpected error for {symbol}: {type(e).__name__}: {e}")

        # Try yfinance (most reliable fallback)
        if 'yfinance' in self.providers and self.circuit_breakers['yfinance'].can_attempt():
            try:
                self.provider_stats['yfinance']['request_count'] += 1
                price = await self._get_yfinance_price(symbol)
                if price:
                    validate_price_data({'price': price}, symbol)
                    self._record_success('yfinance')
                    logger.info(f"✅ yfinance: {symbol} = ${price:.2f}")
                    return price
            except DataProviderError as e:
                self._record_failure('yfinance', e)
                errors.append(f"yfinance: {e.message}")
                logger.warning(f"yfinance failed for {symbol}: {e.message}")
            except Exception as e:
                categorized_error = self._categorize_error(e, 'yfinance')
                self._record_failure('yfinance', categorized_error)
                errors.append(f"yfinance: {categorized_error.message}")
                logger.warning(f"yfinance unexpected error for {symbol}: {type(e).__name__}: {e}")

        # All providers failed - log comprehensive error
        logger.error(
            f"❌ All providers failed for {symbol}. Errors:\n" +
            "\n".join(f"  - {err}" for err in errors)
        )
        return None

    @retry_with_backoff(max_retries=2)
    async def _get_alpaca_stock_price(self, symbol: str) -> Optional[float]:
        """Get stock price from Alpaca with retry logic"""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = await with_timeout(
                asyncio.to_thread(self.providers['alpaca_stock'].get_stock_latest_quote, request),
                timeout=REQUEST_TIMEOUT,
                provider='alpaca'
            )

            if not quote or symbol not in quote:
                raise EmptyDataError('alpaca', f"No quote data returned for {symbol}")

            quote_data = quote[symbol]
            price = float(quote_data.ask_price or quote_data.bid_price)

            if not price or price <= 0:
                raise EmptyDataError('alpaca', f"Invalid price in quote for {symbol}")

            return price
        except DataProviderError:
            raise
        except Exception as e:
            raise self._categorize_error(e, 'alpaca')

    @retry_with_backoff(max_retries=2)
    async def _get_polygon_price(self, symbol: str) -> Optional[float]:
        """Get stock price from Polygon with retry logic"""
        try:
            ticker = await with_timeout(
                asyncio.to_thread(self.providers['polygon'].get_last_trade, symbol),
                timeout=REQUEST_TIMEOUT,
                provider='polygon'
            )

            if not ticker:
                raise EmptyDataError('polygon', f"No trade data returned for {symbol}")

            price = float(ticker.price)

            if not price or price <= 0:
                raise EmptyDataError('polygon', f"Invalid price in trade for {symbol}")

            return price
        except DataProviderError:
            raise
        except Exception as e:
            raise self._categorize_error(e, 'polygon')

    @retry_with_backoff(max_retries=2)
    async def _get_alpha_vantage_price(self, symbol: str) -> Optional[float]:
        """Get stock price from Alpha Vantage with retry logic"""
        try:
            data, _ = await with_timeout(
                asyncio.to_thread(self.providers['alpha_vantage'].get_quote_endpoint, symbol),
                timeout=REQUEST_TIMEOUT,
                provider='alpha_vantage'
            )

            if data.empty:
                raise EmptyDataError('alpha_vantage', f"No quote data returned for {symbol}")

            price = float(data['05. price'].iloc[0])

            if not price or price <= 0:
                raise EmptyDataError('alpha_vantage', f"Invalid price in quote for {symbol}")

            return price
        except DataProviderError:
            raise
        except Exception as e:
            raise self._categorize_error(e, 'alpha_vantage')

    @retry_with_backoff(max_retries=2)
    async def _get_yfinance_price(self, symbol: str) -> Optional[float]:
        """Get stock price from yfinance with retry logic"""
        try:
            ticker = yf.Ticker(symbol)
            data = await with_timeout(
                asyncio.to_thread(ticker.history, period="1d"),
                timeout=REQUEST_TIMEOUT,
                provider='yfinance'
            )

            if data.empty:
                raise EmptyDataError('yfinance', f"No price data returned for {symbol}")

            if 'Close' not in data.columns:
                raise DataValidationError('yfinance', f"Missing 'Close' column in data for {symbol}")

            price = float(data['Close'].iloc[-1])

            if not price or price <= 0:
                raise EmptyDataError('yfinance', f"Invalid price value for {symbol}: {price}")

            return price
        except DataProviderError:
            raise
        except Exception as e:
            raise self._categorize_error(e, 'yfinance')
    
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
        """Get stock historical data with comprehensive error handling"""

        errors = []

        # Try Alpaca
        if 'alpaca_stock' in self.providers and self.circuit_breakers['alpaca'].can_attempt():
            try:
                self.provider_stats['alpaca']['request_count'] += 1
                data = await self._get_alpaca_historical(symbol, days)
                if data:
                    validate_historical_data(data, symbol, min_bars=1)
                    self._record_success('alpaca')
                    logger.info(f"✅ Alpaca: Got {len(data)} bars for {symbol}")
                    return data
            except DataProviderError as e:
                self._record_failure('alpaca', e)
                errors.append(f"Alpaca: {e.message}")
                logger.warning(f"Alpaca historical failed for {symbol}: {e.message}")
            except Exception as e:
                categorized_error = self._categorize_error(e, 'alpaca')
                self._record_failure('alpaca', categorized_error)
                errors.append(f"Alpaca: {categorized_error.message}")
                logger.warning(f"Alpaca historical unexpected error for {symbol}: {type(e).__name__}: {e}")

        # Try yfinance
        if 'yfinance' in self.providers and self.circuit_breakers['yfinance'].can_attempt():
            try:
                self.provider_stats['yfinance']['request_count'] += 1
                data = await self._get_yfinance_historical(symbol, days)
                if data:
                    validate_historical_data(data, symbol, min_bars=1)
                    self._record_success('yfinance')
                    logger.info(f"✅ yfinance: Got {len(data)} bars for {symbol}")
                    return data
            except DataProviderError as e:
                self._record_failure('yfinance', e)
                errors.append(f"yfinance: {e.message}")
                logger.warning(f"yfinance historical failed for {symbol}: {e.message}")
            except Exception as e:
                categorized_error = self._categorize_error(e, 'yfinance')
                self._record_failure('yfinance', categorized_error)
                errors.append(f"yfinance: {categorized_error.message}")
                logger.warning(f"yfinance historical unexpected error for {symbol}: {type(e).__name__}: {e}")

        # All providers failed
        logger.error(
            f"❌ All providers failed for historical data {symbol}. Errors:\n" +
            "\n".join(f"  - {err}" for err in errors)
        )
        return []

    @retry_with_backoff(max_retries=2)
    async def _get_alpaca_historical(self, symbol: str, days: int) -> List[Dict]:
        """Get historical data from Alpaca with retry logic"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date
            )

            bars = await with_timeout(
                asyncio.to_thread(self.providers['alpaca_stock'].get_stock_bars, request),
                timeout=REQUEST_TIMEOUT * 2,  # Historical data may take longer
                provider='alpaca'
            )

            if not bars or symbol not in bars:
                raise EmptyDataError('alpaca', f"No historical data returned for {symbol}")

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

            if not data:
                raise EmptyDataError('alpaca', f"Empty bar list for {symbol}")

            return data
        except DataProviderError:
            raise
        except Exception as e:
            raise self._categorize_error(e, 'alpaca')

    @retry_with_backoff(max_retries=2)
    async def _get_yfinance_historical(self, symbol: str, days: int) -> List[Dict]:
        """Get historical data from yfinance with retry logic"""
        try:
            ticker = yf.Ticker(symbol)
            hist = await with_timeout(
                asyncio.to_thread(ticker.history, period=f"{days}d"),
                timeout=REQUEST_TIMEOUT * 2,
                provider='yfinance'
            )

            if hist.empty:
                raise EmptyDataError('yfinance', f"No historical data returned for {symbol}")

            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in hist.columns]
            if missing_columns:
                raise DataValidationError(
                    'yfinance',
                    f"Missing required columns for {symbol}: {missing_columns}"
                )

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

            return data
        except DataProviderError:
            raise
        except Exception as e:
            raise self._categorize_error(e, 'yfinance')
    
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
