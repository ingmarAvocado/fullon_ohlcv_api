"""Fullon OHLCV API Python SDK.

A Pythonic client library for the fullon_ohlcv_api that returns proper
fullon_ohlcv objects instead of raw JSON responses.
"""

from .client import FullonOhlcvClient
from .websocket import OhlcvWebSocketClient
from .exceptions import (
    FullonOhlcvError,
    APIConnectionError,
    ExchangeNotFoundError,
    SymbolNotFoundError,
    TimeframeError,
    DeserializationError,
)

__version__ = "0.1.0"
__all__ = [
    "FullonOhlcvClient",
    "OhlcvWebSocketClient",
    "FullonOhlcvError",
    "APIConnectionError",
    "ExchangeNotFoundError",
    "SymbolNotFoundError",
    "TimeframeError",
    "DeserializationError",
]
