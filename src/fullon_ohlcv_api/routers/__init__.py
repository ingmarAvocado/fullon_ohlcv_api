"""
FastAPI routers for fullon_ohlcv_api endpoints.

This package contains all API endpoint routers organized by functionality:
- trades: Trade data operations
- candles: OHLCV candle data operations
- exchanges: Exchange catalog operations
- symbols: Symbol catalog operations
"""

from .candles import router as candles_router
from .exchanges import router as exchanges_router
from .trades import router as trades_router

__all__ = ["trades_router", "candles_router", "exchanges_router"]
