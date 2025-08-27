"""
Dependency injection modules for fullon_ohlcv_api.

This package contains FastAPI dependency providers for database sessions,
repository instances, and other shared resources.
"""

from .database import (
    get_candle_repository,
    get_timeseries_repository,
    get_trade_repository,
    validate_exchange_symbol,
)

__all__ = [
    "get_candle_repository",
    "get_timeseries_repository",
    "get_trade_repository",
    "validate_exchange_symbol",
]
