"""
FastAPI routers for fullon_ohlcv_api endpoints.

This package contains all API endpoint routers organized by functionality:
- trades: Trade data operations
- candles: OHLCV candle data operations
- timeseries: OHLCV aggregation operations
- websocket: Real-time streaming operations
- exchanges: Exchange catalog operations
- symbols: Symbol catalog operations
"""

from .candles import router as candles_router
from .exchanges import router as exchanges_router
from .symbols import router as symbols_router
from .timeseries import router as timeseries_router
from .trades import router as trades_router
from .websocket import router as websocket_router

__all__ = [
    "trades_router",
    "candles_router",
    "timeseries_router",
    "websocket_router",
    "exchanges_router",
    "symbols_router",
]
