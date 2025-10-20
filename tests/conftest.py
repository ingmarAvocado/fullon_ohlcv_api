"""
Test configuration and fixtures for fullon_ohlcv_api tests.

This module provides test fixtures and configuration for parallel test execution
using real test databases instead of mocking. Each test file gets its own database
to enable safe parallel execution.
"""

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
import arrow

# Load .env file from project root BEFORE importing any fullon modules
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from current directory as fallback
    load_dotenv()

# Import fullon_ohlcv dependencies
from fullon_ohlcv.utils.config import config
from fullon_ohlcv.utils.logger import get_logger
from fullon_ohlcv_api import FullonOhlcvGateway
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = get_logger(__name__)

# Store database names for cleanup
_test_databases: dict[str, str] = {}


def get_test_db_name(request) -> str:
    """
    Generate a unique test database name for each test file.

    Format: fullon_api_test_{test_file}_{random_suffix}
    """
    # Get the test file name without extension
    test_file = os.path.basename(request.node.fspath).replace(".py", "")

    # Generate unique suffix to avoid conflicts in parallel runs
    unique_suffix = str(uuid.uuid4())[:8]

    # Create database name
    db_name = f"fullon_api_test_{test_file}_{unique_suffix}"

    # Store for cleanup
    _test_databases[request.node.nodeid] = db_name

    return db_name


async def create_test_database(db_name: str) -> bool:
    """Create a test database with TimescaleDB extension (isolated per module)."""
    # Use os.getenv directly like examples do - this ensures we get the right values
    db_user = os.getenv("DB_USER", "fullon")
    db_password = os.getenv("DB_PASSWORD", "fullon")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    admin_url = (
        f"postgresql+asyncpg://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/postgres"
    )

    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            await conn.execute(text(f"CREATE DATABASE {db_name}"))
            logger.info(f"Created test database: {db_name}")
    finally:
        await engine.dispose()

    # Enable TimescaleDB in the new database
    db_url = (
        f"postgresql+asyncpg://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )
    engine = create_async_engine(db_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            logger.info(f"Enabled timescaledb extension in: {db_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable timescaledb in {db_name}: {e}")
        return False
    finally:
        await engine.dispose()


async def drop_test_database(db_name: str) -> bool:
    """Drop a test database, terminating active connections."""
    # Use os.getenv directly like examples do
    db_user = os.getenv("DB_USER", "fullon")
    db_password = os.getenv("DB_PASSWORD", "fullon")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    admin_url = (
        f"postgresql+asyncpg://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/postgres"
    )

    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
                    """
                )
            )
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            logger.info(f"Dropped test database: {db_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to drop test database {db_name}: {e}")
        return False
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def event_loop_policy():
    """Create a custom event loop policy with uvloop if available."""
    # Install uvloop for high-performance testing
    try:
        import uvloop

        uvloop.install()
        logger.info("uvloop installed for test event loops")
    except ImportError:
        logger.debug("uvloop not available, using default asyncio for tests")
    except Exception as e:
        logger.warning(f"Failed to install uvloop for tests: {e}")

    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session with uvloop if available."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


class TestConfig:
    """Test-specific configuration that can be modified per test."""

    def __init__(self, db_name: str):
        # Use os.getenv directly for consistency
        self.database = type(
            "obj",
            (object,),
            {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER", "fullon"),
                "password": os.getenv("DB_PASSWORD", "fullon"),
                "name": db_name,
                "test_name": db_name,
            },
        )
        self.logging = config.logging


@pytest_asyncio.fixture(scope="module")
async def test_db_name(request) -> str:
    """Get the test database name for this module."""
    return get_test_db_name(request)


@pytest_asyncio.fixture(scope="module")
async def test_db(test_db_name: str) -> AsyncGenerator[dict, None]:
    """
    Create a unique test database for each test module.

    Returns a dict with database configuration instead of an engine
    to avoid event loop issues.
    """
    # Create an isolated database per module with TimescaleDB enabled
    success = await create_test_database(test_db_name)
    assert success, f"Failed to create test database: {test_db_name}"

    # Use os.getenv directly for consistency
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": test_db_name,
        "user": os.getenv("DB_USER", "fullon"),
        "password": os.getenv("DB_PASSWORD", "fullon"),
    }

    try:
        yield db_config
    finally:
        await drop_test_database(test_db_name)


@pytest_asyncio.fixture(scope="module")
async def clean_test_schemas(test_db: dict):
    """No-op schema cleaner (no direct DB access)."""
    yield


@pytest.fixture
def anyio_backend():
    """Specify asyncio backend for anyio compatibility."""
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_sqlalchemy_models():
    """
    Reset fullon_ohlcv model configuration between tests.

    This prevents model state from leaking between tests.
    """
    from fullon_ohlcv.models import Candle, Trade

    # Reset model configuration
    Trade._exchange = None
    Trade._symbol = None
    Candle._exchange = None
    Candle._symbol = None

    yield

    # Cleanup after test
    Trade._exchange = None
    Trade._symbol = None
    Candle._exchange = None
    Candle._symbol = None


# FastAPI Gateway fixtures adapted for database testing
@pytest.fixture
def gateway() -> FullonOhlcvGateway:
    """Create a FullonOhlcvGateway instance for testing."""
    return FullonOhlcvGateway(
        title="Test OHLCV API",
        description="Test instance of fullon_ohlcv_api with real database support",
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
def prefixed_client() -> TestClient:
    """Create a test client using a gateway with a URL prefix."""
    gateway = FullonOhlcvGateway(
        title="Test OHLCV API",
        description="Test instance of fullon_ohlcv_api with prefix",
        version="0.1.0-test",
        prefix="/ohlcv",
    )
    app = gateway.get_app()
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    # httpx 0.27+ requires ASGITransport instead of the deprecated `app` arg
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_trades_bulk():
    """Provide a small set of sample trades in API response shape."""
    from tests.factories import create_api_trade_list

    trades = create_api_trade_list(count=2, exchange="binance", symbol="BTC/USDT")
    return {
        "trades": [
            {
                "timestamp": t.timestamp.isoformat(),
                "price": float(t.price),
                "volume": float(t.volume),
                "side": t.side,
                "type": t.type,
            }
            for t in trades
        ]
    }

@pytest.fixture
def sample_candle_data():
    """Provide a single sample candle in API response shape."""
    from datetime import UTC, datetime

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "open": 45000.0,
        "high": 45100.0,
        "low": 44900.0,
        "close": 45050.0,
        "vol": 10.5,
    }


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API endpoint tests")
    config.addinivalue_line("markers", "requires_timescale: tests require TimescaleDB functions")


# NOTE: We do not skip Timescale-marked tests globally.
# The per-module test_db fixture provisions a Timescale-enabled database,
# so Timescale-dependent tests run against the correct environment.


# Patch config for repository test support
@pytest_asyncio.fixture
async def config_with_test_db(test_db: dict, monkeypatch):
    """
    Patch fullon_ohlcv config to use our test database.

    This ensures all repository instances use the test database.
    """
    # Point repositories at the isolated per-module database
    # Patch ALL database connection parameters to ensure proper connection
    monkeypatch.setattr(config.database, "test_name", test_db["database"], raising=False)
    monkeypatch.setattr(config.database, "name", test_db["database"], raising=False)
    monkeypatch.setattr(config.database, "host", test_db["host"], raising=False)
    monkeypatch.setattr(config.database, "port", test_db["port"], raising=False)
    monkeypatch.setattr(config.database, "user", test_db["user"], raising=False)
    monkeypatch.setattr(config.database, "password", test_db["password"], raising=False)

    yield config

    # Config cleanup is handled by monkeypatch automatically
