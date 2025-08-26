"""
Pydantic data models for fullon_ohlcv_api.

This package contains request and response models for API validation
and OpenAPI documentation generation.
"""

# Request models
from .requests import (
    CandleRangeRequest,
    ExchangeListRequest,
    PaginationRequest,
    SymbolListRequest,
    TimeframeEnum,
    TimeseriesRequest,
    TradeRangeRequest,
    WebSocketSubscription,
)

# Response models
from .responses import (
    BaseResponse,
    CandlesResponse,
    ErrorResponse,
    ExchangesResponse,
    HealthResponse,
    PaginatedResponse,
    SymbolsResponse,
    TimeseriesResponse,
    TradesResponse,
    ValidationErrorDetail,
    WebSocketUpdate,
)

__all__ = [
    # Request models
    "PaginationRequest",
    "TradeRangeRequest",
    "CandleRangeRequest",
    "TimeseriesRequest",
    "WebSocketSubscription",
    "ExchangeListRequest",
    "SymbolListRequest",
    "TimeframeEnum",
    # Response models
    "BaseResponse",
    "TradesResponse",
    "CandlesResponse",
    "TimeseriesResponse",
    "WebSocketUpdate",
    "ErrorResponse",
    "ExchangesResponse",
    "SymbolsResponse",
    "HealthResponse",
    "ValidationErrorDetail",
    "PaginatedResponse",
]
