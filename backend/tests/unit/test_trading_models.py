"""
Unit tests for trading models and validation
"""
import pytest
from pydantic import ValidationError
from app.models.trading_models import (
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    TradeRequest,
    AnalysisRequest,
    WatchlistAddRequest
)


class TestOrderModel:
    """Test Order model validation"""

    def test_valid_order(self):
        """Test creating a valid order"""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10.0
        )
        assert order.symbol == "AAPL"
        assert order.quantity == 10.0
        assert order.side == OrderSide.BUY

    def test_symbol_uppercase(self):
        """Test symbol is automatically uppercased"""
        order = Order(
            symbol="aapl",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10.0
        )
        assert order.symbol == "AAPL"

    def test_negative_quantity_rejected(self):
        """Test negative quantity is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=-10.0
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_zero_quantity_rejected(self):
        """Test zero quantity is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.0
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_excessive_quantity_rejected(self):
        """Test excessive quantity is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=2_000_000.0
            )
        assert "1,000,000" in str(exc_info.value)

    def test_negative_price_rejected(self):
        """Test negative price is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=10.0,
                price=-150.0
            )
        assert "price" in str(exc_info.value).lower()


class TestTradeRequest:
    """Test TradeRequest validation"""

    def test_valid_trade_request(self):
        """Test valid trade request"""
        request = TradeRequest(symbol="AAPL", quantity=10.0)
        assert request.symbol == "AAPL"
        assert request.quantity == 10.0

    def test_symbol_stripped_and_uppercased(self):
        """Test symbol is stripped and uppercased"""
        request = TradeRequest(symbol="  aapl  ", quantity=10.0)
        assert request.symbol == "AAPL"

    def test_quantity_optional(self):
        """Test quantity is optional"""
        request = TradeRequest(symbol="AAPL")
        assert request.symbol == "AAPL"
        assert request.quantity is None

    def test_empty_symbol_rejected(self):
        """Test empty symbol is rejected"""
        with pytest.raises(ValidationError):
            TradeRequest(symbol="")

    def test_long_symbol_rejected(self):
        """Test overly long symbol is rejected"""
        with pytest.raises(ValidationError):
            TradeRequest(symbol="TOOLONGSYMBOL")


class TestAnalysisRequest:
    """Test AnalysisRequest validation"""

    def test_valid_analysis_request(self):
        """Test valid analysis request"""
        request = AnalysisRequest(symbol="AAPL")
        assert request.symbol == "AAPL"

    def test_whitespace_symbol_rejected(self):
        """Test whitespace-only symbol is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(symbol="   ")
        assert "empty" in str(exc_info.value).lower()

    def test_symbol_uppercased(self):
        """Test symbol is uppercased"""
        request = AnalysisRequest(symbol="tsla")
        assert request.symbol == "TSLA"


class TestWatchlistAddRequest:
    """Test WatchlistAddRequest validation"""

    def test_valid_watchlist_request(self):
        """Test valid watchlist request"""
        request = WatchlistAddRequest(
            symbol="AAPL",
            notes="Good long-term investment"
        )
        assert request.symbol == "AAPL"
        assert request.notes == "Good long-term investment"

    def test_notes_optional(self):
        """Test notes are optional"""
        request = WatchlistAddRequest(symbol="AAPL")
        assert request.notes is None

    def test_long_notes_rejected(self):
        """Test overly long notes are rejected"""
        with pytest.raises(ValidationError):
            WatchlistAddRequest(
                symbol="AAPL",
                notes="x" * 600  # Exceeds 500 char limit
            )
