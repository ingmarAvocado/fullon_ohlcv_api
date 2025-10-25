"""
Database-related dependencies strictly via fullon_ohlcv.

This module intentionally avoids direct database drivers, SQLAlchemy, or raw SQL.
Only fullon_ohlcv repositories are used where a DB-backed object is needed.
"""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import (  # type: ignore
    CandleRepository,
    TimeseriesRepository,
    TradeRepository,
)

logger = get_component_logger("fullon.api.ohlcv.dependencies")


def validate_exchange_symbol(exchange: str | None, symbol: str | None) -> None:
    """
    Validate exchange and symbol parameters.

    Args:
        exchange: Exchange name to validate
        symbol: Trading pair symbol to validate

    Raises:
        HTTPException: 422 status code if validation fails
    """
    if exchange is None or not exchange or not exchange.strip():
        raise HTTPException(status_code=422, detail="Exchange cannot be empty")

    if symbol is None or not symbol or not symbol.strip():
        raise HTTPException(status_code=422, detail="Symbol cannot be empty")


async def get_trade_repository(exchange: str, symbol: str) -> AsyncGenerator[Any, None]:
    """
    FastAPI dependency for TradeRepository with proper cleanup.

    Creates a TradeRepository instance for the given exchange and symbol,
    ensures proper async context management and cleanup. Connects to the
    database specified by DB_OHLCV_NAME environment variable.

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')

    Yields:
        TradeRepository: Initialized repository instance

    Raises:
        HTTPException: 500 status code for database connection errors
    """
    validate_exchange_symbol(exchange, symbol)

    logger.info("Creating TradeRepository", exchange=exchange, symbol=symbol)

    try:
        # Create repository (production mode by default)
        repo = TradeRepository(exchange, symbol)
        try:
            # Enter async context manager (connection/setup + auto init_symbol)
            await repo.__aenter__()
        except Exception as e:
            logger.error(
                "Repository initialization error",
                error=str(e),
                exchange=exchange,
                symbol=symbol,
            )
            raise HTTPException(
                status_code=500, detail=f"Repository initialization error: {str(e)}"
            ) from e
        logger.debug(
            "TradeRepository context entered", exchange=exchange, symbol=symbol
        )
    except Exception as e:
        logger.error(
            "Failed to create TradeRepository",
            error=str(e),
            exchange=exchange,
            symbol=symbol,
        )
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        ) from e
    try:
        yield repo
    finally:
        # Ensure cleanup happens
        try:
            await repo.__aexit__(None, None, None)
            logger.info("TradeRepository cleaned up", exchange=exchange, symbol=symbol)
        except Exception as cleanup_error:
            logger.warning(
                "Error during repository cleanup",
                error=str(cleanup_error),
                exchange=exchange,
                symbol=symbol,
            )


async def get_candle_repository(
    exchange: str, symbol: str
) -> AsyncGenerator[Any, None]:
    """
    FastAPI dependency for CandleRepository with proper cleanup.

    Creates a CandleRepository instance for the given exchange and symbol,
    ensures proper async context management and cleanup. Connects to the
    database specified by DB_OHLCV_NAME environment variable.

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')

    Yields:
        CandleRepository: Initialized repository instance

    Raises:
        HTTPException: 500 status code for database connection errors
    """
    validate_exchange_symbol(exchange, symbol)

    logger.info("Creating CandleRepository", exchange=exchange, symbol=symbol)

    try:
        # Create repository (production mode by default)
        repo = CandleRepository(exchange, symbol)
        # Enter async context manager (connection/setup + auto init_symbol)
        await repo.__aenter__()
        logger.debug(
            "CandleRepository context entered", exchange=exchange, symbol=symbol
        )
    except Exception as e:
        logger.error(
            "Failed to create CandleRepository",
            error=str(e),
            exchange=exchange,
            symbol=symbol,
        )
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        ) from e
    try:
        yield repo
    finally:
        # Ensure cleanup happens
        try:
            await repo.__aexit__(None, None, None)
            logger.info("CandleRepository cleaned up", exchange=exchange, symbol=symbol)
        except Exception as cleanup_error:
            logger.warning(
                "Error during repository cleanup",
                error=str(cleanup_error),
                exchange=exchange,
                symbol=symbol,
            )


async def get_timeseries_repository(
    exchange: str, symbol: str
) -> AsyncGenerator[Any, None]:
    """
    FastAPI dependency for TimeseriesRepository with proper cleanup.

    Creates a TimeseriesRepository instance for the given exchange and symbol,
    ensures proper async context management and cleanup. Connects to the
    database specified by DB_OHLCV_NAME environment variable.

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')

    Yields:
        TimeseriesRepository: Initialized repository instance

    Raises:
        HTTPException: 500 status code for database connection errors
    """
    validate_exchange_symbol(exchange, symbol)

    logger.info("Creating TimeseriesRepository", exchange=exchange, symbol=symbol)

    try:
        # Create repository (production mode by default)
        repo = TimeseriesRepository(exchange, symbol)
        # Enter async context manager (connection/setup + auto init_symbol)
        await repo.__aenter__()
        logger.debug(
            "TimeseriesRepository context entered", exchange=exchange, symbol=symbol
        )
    except Exception as e:
        logger.error(
            "Failed to create TimeseriesRepository",
            error=str(e),
            exchange=exchange,
            symbol=symbol,
        )
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        ) from e
    try:
        yield repo
    finally:
        # Ensure cleanup happens
        try:
            await repo.__aexit__(None, None, None)
            logger.info(
                "TimeseriesRepository cleaned up", exchange=exchange, symbol=symbol
            )
        except Exception as cleanup_error:
            logger.warning(
                "Error during repository cleanup",
                error=str(cleanup_error),
                exchange=exchange,
                symbol=symbol,
            )


# NOTE: Intentionally no direct DB connection helpers here.
# Exchange/symbol discovery should be implemented through explicit
# APIs in fullon_ohlcv (if/when available) or delegated to another
# component. We do not expose raw connections.
