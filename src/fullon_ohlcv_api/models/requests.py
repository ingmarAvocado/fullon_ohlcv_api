"""
Request models for fullon_ohlcv_api.

This module contains Pydantic models for API request validation based on
the examples-driven requirements from the examples/ folder.
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TimeframeEnum(str, Enum):
    """Valid timeframe values for OHLCV data."""

    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


class PaginationRequest(BaseModel):
    """
    Pagination parameters for API requests.

    Used across multiple endpoints for limiting and offsetting results.
    Follows constraints from examples: limit between 1-5000.
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    limit: int = Field(
        default=100,
        ge=1,
        le=5000,
        description="Maximum number of records to return (1-5000)",
    )
    offset: int = Field(
        default=0, ge=0, description="Number of records to skip for pagination"
    )


class TradeRangeRequest(BaseModel):
    """
    Request model for trade data retrieval.

    Based on trade_repository_example.py:
    - GET /api/trades/{exchange}/{symbol}
    - GET /api/trades/{exchange}/{symbol}/range
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    exchange: str = Field(
        ..., min_length=1, description="Exchange name (e.g., 'binance', 'coinbase')"
    )
    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')",
    )
    start_time: Optional[datetime] = Field(
        default=None,
        description="Start time for trade range query (timezone-aware UTC)",
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time for trade range query (timezone-aware UTC)"
    )
    limit: int = Field(
        default=100, ge=1, le=5000, description="Maximum number of trades to return"
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware (preferably UTC)."""
        if v is not None and v.tzinfo is None:
            raise ValueError(
                "Datetime must be timezone-aware. Use datetime with timezone.utc"
            )
        return v

    @field_validator("exchange", "symbol")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure strings are not empty after stripping."""
        if not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class CandleRangeRequest(BaseModel):
    """
    Request model for candle data retrieval.

    Based on candle_repository_example.py:
    - GET /api/candles/{exchange}/{symbol}/{timeframe}
    - GET /api/candles/{exchange}/{symbol}/{timeframe}/range
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    exchange: str = Field(..., min_length=1, description="Exchange name")
    symbol: str = Field(..., min_length=1, description="Trading pair symbol")
    timeframe: TimeframeEnum = Field(
        ..., description="OHLCV timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)"
    )
    start_time: Optional[datetime] = Field(
        default=None,
        description="Start time for candle range query (timezone-aware UTC)",
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time for candle range query (timezone-aware UTC)"
    )
    limit: int = Field(
        default=100, ge=1, le=5000, description="Maximum number of candles to return"
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError(
                "Datetime must be timezone-aware. Use datetime with timezone.utc"
            )
        return v

    @field_validator("exchange", "symbol")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure strings are not empty after stripping."""
        if not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class TimeseriesRequest(BaseModel):
    """
    Request model for timeseries OHLCV aggregation.

    Based on timeseries_repository_example.py:
    - GET /api/timeseries/{exchange}/{symbol}/ohlcv
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    exchange: str = Field(..., min_length=1, description="Exchange name")
    symbol: str = Field(..., min_length=1, description="Trading pair symbol")
    timeframe: TimeframeEnum = Field(..., description="OHLCV aggregation timeframe")
    start_time: Optional[datetime] = Field(
        default=None, description="Start time for OHLCV generation (timezone-aware UTC)"
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time for OHLCV generation (timezone-aware UTC)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=5000,
        description="Maximum number of OHLCV candles to generate",
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError(
                "Datetime must be timezone-aware. Use datetime with timezone.utc"
            )
        return v

    @field_validator("exchange", "symbol")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure strings are not empty after stripping."""
        if not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class WebSocketSubscription(BaseModel):
    """
    WebSocket subscription/unsubscription message model.

    Based on websocket_live_ohlcv_example.py WebSocket message format:
    {
        "action": "subscribe",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1m",
        "type": "ohlcv_live"
    }
    """

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    action: Literal["subscribe", "unsubscribe"] = Field(
        ..., description="WebSocket action: subscribe or unsubscribe"
    )
    exchange: str = Field(
        ..., min_length=1, description="Exchange name for subscription"
    )
    symbol: str = Field(
        ..., min_length=1, description="Trading pair symbol for subscription"
    )
    timeframe: TimeframeEnum = Field(
        ..., description="OHLCV timeframe for subscription"
    )
    type: Literal["ohlcv_live", "trade_live", "candle_live"] = Field(
        ..., description="Type of live data subscription"
    )

    @field_validator("exchange", "symbol")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure strings are not empty after stripping."""
        if not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class ExchangeListRequest(BaseModel):
    """
    Request model for listing available exchanges.

    Simple request model for exchange catalog endpoints.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    include_stats: bool = Field(
        default=False, description="Include exchange statistics (symbol count, etc.)"
    )
    active_only: bool = Field(default=True, description="Only return active exchanges")


class SymbolListRequest(BaseModel):
    """
    Request model for listing symbols for an exchange.

    For symbol catalog endpoints per exchange.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    exchange: str = Field(
        ..., min_length=1, description="Exchange name to get symbols for"
    )
    active_only: bool = Field(
        default=True, description="Only return active trading pairs"
    )
    base_currency: Optional[str] = Field(
        default=None, description="Filter by base currency (e.g., 'BTC')"
    )
    quote_currency: Optional[str] = Field(
        default=None, description="Filter by quote currency (e.g., 'USDT')"
    )

    @field_validator("exchange", "base_currency", "quote_currency")
    @classmethod
    def validate_non_empty_string(cls, v: Optional[str]) -> Optional[str]:
        """Ensure strings are not empty after stripping."""
        if v is not None and not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip() if v is not None else None
