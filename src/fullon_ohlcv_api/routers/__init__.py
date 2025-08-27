"""
FastAPI routers for fullon_ohlcv_api endpoints.

This package contains all API endpoint routers organized by functionality:
- trades: Trade data operations
- candles: OHLCV candle data operations
- exchanges: Exchange catalog operations
- symbols: Symbol catalog operations
"""

from .trades import router as trades_router

__all__ = ["trades_router"]
