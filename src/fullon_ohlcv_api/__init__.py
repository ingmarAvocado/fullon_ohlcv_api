"""
fullon_ohlcv_api - FastAPI Gateway for fullon_ohlcv with LRRS-compliant architecture.

This library provides a composable FastAPI gateway for OHLCV market data operations,
designed for integration into master_api alongside other fullon libraries.

Usage:
    # Library mode (for master_api composition)
    from fullon_ohlcv_api import FullonOhlcvGateway, get_all_routers

    # Standalone mode (for testing)
    python -m fullon_ohlcv_api.standalone_server
"""

from fastapi import APIRouter

from .gateway import FullonOhlcvGateway


def get_all_routers() -> list[APIRouter]:
    """
    Get all routers for master_api composition.

    Returns:
        List[APIRouter]: All OHLCV API routers for external composition
    """
    from .routers import (
        candles_router,
        exchanges_router,
        symbols_router,
        timeseries_router,
        trades_router,
        websocket_router,
    )

    return [
        trades_router,
        candles_router,
        timeseries_router,
        websocket_router,
        exchanges_router,
        symbols_router,
    ]


# Public API exports
__all__ = ["FullonOhlcvGateway", "get_all_routers"]
__version__ = "0.2.0"
