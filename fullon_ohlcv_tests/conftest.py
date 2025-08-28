"""
Test configuration and fixtures.

This module provides test fixtures and configuration for parallel test execution.
Each test file gets its own database to enable safe parallel execution.
"""

import os
import pytest
import pytest_asyncio
import asyncio
import uuid
from typing import AsyncGenerator, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
import redis

from fullon_ohlcv.utils.config import config
from fullon_ohlcv.utils.logger import get_logger

logger = get_logger(__name__)

# Store database names for cleanup
_test_databases: Dict[str, str] = {}


def get_test_db_name(request) -> str:
    """
    Generate a unique test database name for each test file.
    
    Format: fullon_test_{test_file}_{random_suffix}
    """
    # Get the test file name without extension
    test_file = os.path.basename(request.node.fspath).replace('.py', '')
    
    # Generate unique suffix to avoid conflicts in parallel runs
    unique_suffix = str(uuid.uuid4())[:8]
    
    # Create database name
    db_name = f"fullon_test_{test_file}_{unique_suffix}"
    
    # Store for cleanup
    _test_databases[request.node.nodeid] = db_name
    
    return db_name


async def create_test_database(db_name: str) -> bool:
    """Create a test database with TimescaleDB extension."""
    # Connect to postgres database to create the test database
    admin_url = (
        f"postgresql+asyncpg://{config.database.user}:{config.database.password}@"
        f"{config.database.host}:{config.database.port}/postgres"
    )
    
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    try:
        async with engine.begin() as conn:
            # Drop if exists (for reruns)
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            
            # Create new database
            await conn.execute(text(f"CREATE DATABASE {db_name}"))
            logger.info(f"Created test database: {db_name}")
        
        await engine.dispose()
        
        # Connect to new database and add TimescaleDB
        db_url = (
            f"postgresql+asyncpg://{config.database.user}:{config.database.password}@"
            f"{config.database.host}:{config.database.port}/{db_name}"
        )
        
        engine = create_async_engine(db_url)
        
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            logger.info(f"Added TimescaleDB extension to: {db_name}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create test database {db_name}: {e}")
        if 'engine' in locals():
            await engine.dispose()
        return False


async def drop_test_database(db_name: str) -> bool:
    """Drop a test database."""
    admin_url = (
        f"postgresql+asyncpg://{config.database.user}:{config.database.password}@"
        f"{config.database.host}:{config.database.port}/postgres"
    )
    
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    try:
        async with engine.begin() as conn:
            # Terminate connections
            await conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """))
            
            # Drop database
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


@pytest.fixture(scope="module")
def event_loop(request):
    """Create an event loop for the test module with uvloop if available."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()




class TestConfig:
    """Test-specific configuration that can be modified per test."""
    def __init__(self, db_name: str):
        self.database = type('obj', (object,), {
            'host': config.database.host,
            'port': config.database.port,
            'user': config.database.user,
            'password': config.database.password,
            'name': db_name,
            'test_name': db_name
        })
        self.logging = config.logging


@pytest_asyncio.fixture(scope="module")
async def test_db_name(request) -> str:
    """Get the test database name for this module."""
    return get_test_db_name(request)


@pytest_asyncio.fixture(scope="module")
async def test_db(test_db_name: str) -> AsyncGenerator[Dict, None]:
    """
    Create a unique test database for each test module.
    
    Returns a dict with database configuration instead of an engine
    to avoid event loop issues.
    """
    # Create the test database
    success = await create_test_database(test_db_name)
    assert success, f"Failed to create test database: {test_db_name}"
    
    # Return configuration dict
    db_config = {
        "host": config.database.host,
        "port": config.database.port,
        "database": test_db_name,
        "user": config.database.user,
        "password": config.database.password
    }
    
    try:
        yield db_config
    finally:
        # Cleanup
        await drop_test_database(test_db_name)


@pytest_asyncio.fixture
async def db_session(test_db: Dict) -> AsyncGenerator[AsyncSession, None]:
    """Create a new async database session for a test."""
    db_url = (
        f"postgresql+asyncpg://{test_db['user']}:{test_db['password']}@"
        f"{test_db['host']}:{test_db['port']}/{test_db['database']}"
    )
    
    engine = create_async_engine(db_url, pool_pre_ping=True)
    
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def clean_test_schemas(test_db: Dict):
    """
    Ensure a clean database state for each test module.
    
    This fixture drops all schemas except system schemas at the start
    and end of each test module.
    """
    db_url = (
        f"postgresql+asyncpg://{test_db['user']}:{test_db['password']}@"
        f"{test_db['host']}:{test_db['port']}/{test_db['database']}"
    )
    
    engine = create_async_engine(db_url)
    
    # Clean before tests
    async with engine.begin() as conn:
        # Get all non-system schemas
        result = await conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('public', 'pg_catalog', 'information_schema', 
                                     'timescaledb_internal', '_timescaledb_catalog',
                                     '_timescaledb_config', '_timescaledb_cache',
                                     '_timescaledb_functions', 'timescaledb_information',
                                     'timescaledb_experimental', 'toolkit_experimental')
            AND schema_name NOT LIKE 'pg_%'
            AND schema_name NOT LIKE '_timescaledb%'
        """))
        
        schemas = [row[0] for row in result]
        
        # Drop all user schemas
        for schema in schemas:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            logger.debug(f"Dropped schema before tests: {schema}")
    
    await engine.dispose()
    
    yield
    
    # Clean after tests
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('public', 'pg_catalog', 'information_schema', 
                                     'timescaledb_internal', '_timescaledb_catalog',
                                     '_timescaledb_config', '_timescaledb_cache',
                                     '_timescaledb_functions', 'timescaledb_information',
                                     'timescaledb_experimental', 'toolkit_experimental')
            AND schema_name NOT LIKE 'pg_%'
            AND schema_name NOT LIKE '_timescaledb%'
        """))
        
        schemas = [row[0] for row in result]
        
        # Drop all user schemas
        for schema in schemas:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            logger.debug(f"Dropped schema after tests: {schema}")
    
    await engine.dispose()


@pytest.fixture
def anyio_backend():
    """Specify asyncio backend for anyio compatibility."""
    return "asyncio"


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(autouse=True)
def reset_sqlalchemy_models():
    """
    Reset SQLAlchemy model configuration between tests.
    
    This prevents model state from leaking between tests.
    """
    from fullon_ohlcv.models import Trade, Candle
    
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


def get_redis_db_for_worker(worker_id: str) -> int:
    """
    Get a Redis database number based on worker ID.
    
    Args:
        worker_id: pytest-xdist worker ID (e.g., 'gw0', 'gw1', 'master')
        
    Returns:
        Redis database number (1-15 for tests, 0 reserved for production)
    """
    if worker_id == "master":
        # Running without pytest-xdist
        return 1
    
    # Extract worker number from ID like 'gw0', 'gw1', etc.
    try:
        worker_num = int(worker_id[2:])
        # Use databases 1-15 for testing (0 is reserved for production)
        return (worker_num % 15) + 1
    except (ValueError, IndexError):
        # Fallback to database 1
        return 1


@pytest.fixture(scope="session")
def redis_test_db(worker_id) -> int:
    """
    Get Redis database number for this test worker.
    
    Returns:
        Redis database number for isolation
    """
    return get_redis_db_for_worker(worker_id)


@pytest_asyncio.fixture
async def redis_cache_db(redis_test_db: int) -> AsyncGenerator[int, None]:
    """
    Provide a clean Redis database for cache testing.
    
    Yields:
        Redis database number
    """
    # Clear the Redis database before use
    redis_client = redis.from_url(
        f"redis://{config.redis.host}:{config.redis.port}/{redis_test_db}",
        decode_responses=True
    )
    
    try:
        # Clear the database
        redis_client.flushdb()
        logger.debug(f"Cleared Redis test database {redis_test_db}")
        
        yield redis_test_db
        
    finally:
        # Clear again after test
        redis_client.flushdb()
        redis_client.close()


@pytest.fixture
def cache_enabled_config(redis_test_db: int):
    """
    Override cache configuration for testing.
    
    Returns:
        Modified config with cache enabled and test Redis DB
    """
    # Save original values
    original_enabled = config.redis.cache_enabled
    original_db = config.redis.db
    
    # Enable cache and set test database
    config.redis.cache_enabled = True
    config.redis.db = redis_test_db
    
    yield config
    
    # Restore original values
    config.redis.cache_enabled = original_enabled
    config.redis.db = original_db


@pytest.fixture
def cache_disabled_config():
    """
    Override cache configuration to disable caching.
    
    Returns:
        Modified config with cache disabled
    """
    # Save original value
    original_enabled = config.redis.cache_enabled
    
    # Disable cache
    config.redis.cache_enabled = False
    
    yield config
    
    # Restore original value
    config.redis.cache_enabled = original_enabled