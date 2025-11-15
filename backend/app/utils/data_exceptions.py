"""
Custom exceptions for data fetching operations
"""


class DataProviderError(Exception):
    """Base exception for all data provider errors"""

    def __init__(self, provider: str, message: str, original_error: Exception = None):
        self.provider = provider
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")


class NetworkError(DataProviderError):
    """Network-related errors (timeouts, connection failures)"""
    pass


class AuthenticationError(DataProviderError):
    """API key or authentication errors"""
    pass


class RateLimitError(DataProviderError):
    """Rate limit exceeded errors"""
    pass


class InvalidSymbolError(DataProviderError):
    """Invalid or unsupported symbol errors"""
    pass


class EmptyDataError(DataProviderError):
    """No data returned by provider"""
    pass


class DataValidationError(DataProviderError):
    """Data validation failed (invalid prices, missing fields, etc.)"""
    pass


class ProviderUnavailableError(DataProviderError):
    """Provider is temporarily unavailable (circuit breaker)"""
    pass
