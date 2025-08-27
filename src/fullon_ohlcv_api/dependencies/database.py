"""
Database dependency injection for fullon_ohlcv_api.

This module provides FastAPI dependency functions for creating and managing
fullon_ohlcv repository instances with proper async context management and cleanup.
"""

from collections.abc import AsyncGenerator

from fastapi import HTTPException
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import (
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


async def get_trade_repository(
    exchange: str, symbol: str
) -> AsyncGenerator[TradeRepository, None]:
    """
    FastAPI dependency for TradeRepository with proper cleanup.

    Creates a TradeRepository instance in test mode for the given exchange
    and symbol, ensures proper async context management and cleanup.

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
        # Create repository in test mode to avoid production data contamination
        repo = TradeRepository(exchange, symbol, test=True)

        try:
            # Enter async context manager
            await repo.__aenter__()
            logger.debug(
                "TradeRepository context entered", exchange=exchange, symbol=symbol
            )
            yield repo

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

        finally:
            # Ensure cleanup happens
            try:
                await repo.__aexit__(None, None, None)
                logger.info(
                    "TradeRepository cleaned up", exchange=exchange, symbol=symbol
                )
            except Exception as cleanup_error:
                logger.warning(
                    "Error during repository cleanup",
                    error=str(cleanup_error),
                    exchange=exchange,
                    symbol=symbol,
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


async def get_candle_repository(
    exchange: str, symbol: str
) -> AsyncGenerator[CandleRepository, None]:
    """
    FastAPI dependency for CandleRepository with proper cleanup.

    Creates a CandleRepository instance in test mode for the given exchange
    and symbol, ensures proper async context management and cleanup.

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
        # Create repository in test mode to avoid production data contamination
        repo = CandleRepository(exchange, symbol, test=True)

        try:
            # Enter async context manager
            await repo.__aenter__()
            logger.debug(
                "CandleRepository context entered", exchange=exchange, symbol=symbol
            )
            yield repo

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

        finally:
            # Ensure cleanup happens
            try:
                await repo.__aexit__(None, None, None)
                logger.info(
                    "CandleRepository cleaned up", exchange=exchange, symbol=symbol
                )
            except Exception as cleanup_error:
                logger.warning(
                    "Error during repository cleanup",
                    error=str(cleanup_error),
                    exchange=exchange,
                    symbol=symbol,
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


async def get_timeseries_repository(
    exchange: str, symbol: str
) -> AsyncGenerator[TimeseriesRepository, None]:
    """
    FastAPI dependency for TimeseriesRepository with proper cleanup.

    Creates a TimeseriesRepository instance in test mode for the given exchange
    and symbol, ensures proper async context management and cleanup.

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
        # Create repository in test mode to avoid production data contamination
        repo = TimeseriesRepository(exchange, symbol, test=True)

        try:
            # Enter async context manager
            await repo.__aenter__()
            logger.debug(
                "TimeseriesRepository context entered", exchange=exchange, symbol=symbol
            )
            yield repo

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
