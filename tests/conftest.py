"""
Pytest configuration and shared fixtures for fullon_ohlcv_api tests.

This module provides common test fixtures, configuration, and utilities
that are shared across all test modules.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from fullon_ohlcv_api import FullonOhlcvGateway
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def gateway() -> FullonOhlcvGateway:
    """Create a FullonOhlcvGateway instance for testing."""
    return FullonOhlcvGateway(
        title="Test OHLCV API",
        description="Test instance of fullon_ohlcv_api",
        version="0.1.0-test",
    )


@pytest.fixture
def app(gateway):
    """Create a FastAPI app instance for testing."""
    return gateway.get_app()


@pytest.fixture
def client(app) -> TestClient:
    """Create a test client for synchronous testing."""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def gateway_with_prefix() -> FullonOhlcvGateway:
    """Create a FullonOhlcvGateway with custom prefix for testing composition."""
    return FullonOhlcvGateway(title="Test OHLCV API with Prefix", prefix="/ohlcv")


@pytest.fixture
def prefixed_app(gateway_with_prefix):
    """Create a FastAPI app with custom prefix for testing."""
    return gateway_with_prefix.get_app()


@pytest.fixture
def prefixed_client(prefixed_app) -> TestClient:
    """Create a test client for prefix testing."""
    return TestClient(prefixed_app)


# Mock data fixtures for testing
@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "timestamp": "2024-01-01T12:00:00Z",
        "price": 45000.50,
        "volume": 0.1,
        "side": "buy",
    }


@pytest.fixture
def sample_candle_data():
    """Sample candle data for testing."""
    return {
        "timestamp": "2024-01-01T12:00:00Z",
        "open": 45000.00,
        "high": 45100.00,
        "low": 44900.00,
        "close": 45050.00,
        "volume": 10.5,
        "closed": True,
        "timeframe": "1h",
    }


@pytest.fixture
def sample_trades_bulk():
    """Sample bulk trade data for testing."""
    return {
        "trades": [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "price": 45000.50,
                "volume": 0.1,
                "side": "buy",
            },
            {
                "timestamp": "2024-01-01T12:00:30Z",
                "price": 44999.75,
                "volume": 0.05,
                "side": "sell",
            },
        ]
    }


@pytest.fixture
def sample_exchange_data():
    """Sample exchange information for testing."""
    return {
        "name": "binance",
        "display_name": "Binance",
        "status": "active",
        "symbols_count": 1500,
        "last_updated": "2024-01-01T12:00:00Z",
    }


# Test configuration
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Custom assertions and utilities
class TestHelpers:
    """Helper methods for testing."""

    @staticmethod
    def assert_valid_timestamp(timestamp_str: str):
        """Assert that a timestamp string is valid ISO format."""
        from datetime import datetime

        try:
            datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}")

    @staticmethod
    def assert_valid_price(price: float):
        """Assert that a price is valid (positive number)."""
        assert isinstance(price, int | float), "Price must be a number"
        assert price > 0, "Price must be positive"

    @staticmethod
    def assert_valid_volume(volume: float):
        """Assert that a volume is valid (non-negative number)."""
        assert isinstance(volume, int | float), "Volume must be a number"
        assert volume >= 0, "Volume must be non-negative"


@pytest.fixture
def test_helpers():
    """Provide test helper methods."""
    return TestHelpers()
