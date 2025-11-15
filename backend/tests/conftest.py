"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_trading.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("./test_trading.db"):
        os.remove("./test_trading.db")


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_symbol():
    """Return a sample stock symbol for testing"""
    return "AAPL"


@pytest.fixture
def sample_portfolio_data():
    """Return sample portfolio data for testing"""
    return {
        "total_value": 100000.0,
        "cash": 50000.0,
        "positions_value": 50000.0,
        "total_pnl": 5000.0,
        "daily_pnl": 500.0,
        "buying_power": 50000.0
    }


@pytest.fixture
def sample_order_data():
    """Return sample order data for testing"""
    return {
        "symbol": "AAPL",
        "side": "buy",
        "order_type": "market",
        "quantity": 10
    }
