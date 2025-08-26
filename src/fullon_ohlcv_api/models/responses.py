"""
Response models for fullon_ohlcv_api.

This module contains Pydantic models for API response formatting based on
the examples-driven requirements from the examples/ folder.
"""

from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
    )

    success: bool = Field(
        default=True, description="Indicates if the request was successful"
    )
    message: Optional[str] = Field(
        default=None, description="Optional message about the response"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response timestamp in UTC",
    )


class TradesResponse(BaseResponse):
    """
    Response model for trade data endpoints.

    Based on trade_repository_example.py expected response format:
    {
        "trades": [...],
        "count": int,
        ...
    }
    """

    trades: list[dict[str, Any]] = Field(..., description="List of trade data objects")
    count: int = Field(..., ge=0, description="Number of trades in the response")
    exchange: str = Field(..., description="Exchange name for the trades")
    symbol: str = Field(..., description="Trading pair symbol for the trades")

    # Pagination fields (optional)
    offset: Optional[int] = Field(
        default=None, ge=0, description="Offset used for pagination"
    )
    limit: Optional[int] = Field(
        default=None, ge=1, description="Limit used for pagination"
    )
    total_available: Optional[int] = Field(
        default=None, ge=0, description="Total number of trades available"
    )

    # Time range fields (for range queries)
    start_time: Optional[datetime] = Field(
        default=None, description="Start time of the queried range"
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time of the queried range"
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return v


class CandlesResponse(BaseResponse):
    """
    Response model for candle data endpoints.

    Based on candle_repository_example.py expected response format:
    {
        "candles": [...],
        "count": int,
        ...
    }
    """

    candles: list[dict[str, Any]] = Field(
        ..., description="List of OHLCV candle data objects"
    )
    count: int = Field(..., ge=0, description="Number of candles in the response")
    exchange: str = Field(..., description="Exchange name for the candles")
    symbol: str = Field(..., description="Trading pair symbol for the candles")
    timeframe: str = Field(
        ..., description="Timeframe of the candles (e.g., '1h', '1d')"
    )

    # Pagination fields (optional)
    offset: Optional[int] = Field(
        default=None, ge=0, description="Offset used for pagination"
    )
    limit: Optional[int] = Field(
        default=None, ge=1, description="Limit used for pagination"
    )
    total_available: Optional[int] = Field(
        default=None, ge=0, description="Total number of candles available"
    )

    # Time range fields (for range queries)
    start_time: Optional[datetime] = Field(
        default=None, description="Start time of the queried range"
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time of the queried range"
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return v


class TimeseriesResponse(BaseResponse):
    """
    Response model for timeseries OHLCV aggregation endpoints.

    Based on timeseries_repository_example.py expected response format:
    {
        "ohlcv": [...],
        "count": int,
        ...
    }
    """

    ohlcv: list[dict[str, Any]] = Field(
        ..., description="List of generated OHLCV data objects"
    )
    count: int = Field(..., ge=0, description="Number of OHLCV candles generated")
    exchange: str = Field(..., description="Exchange name for the OHLCV data")
    symbol: str = Field(..., description="Trading pair symbol for the OHLCV data")
    timeframe: str = Field(..., description="Timeframe used for OHLCV aggregation")

    # Time range fields (for aggregation range)
    start_time: Optional[datetime] = Field(
        default=None, description="Start time of the aggregation range"
    )
    end_time: Optional[datetime] = Field(
        default=None, description="End time of the aggregation range"
    )

    # Metadata about the aggregation
    trades_processed: Optional[int] = Field(
        default=None, ge=0, description="Number of trades used for OHLCV aggregation"
    )
    generation_time_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Time taken to generate OHLCV data in milliseconds",
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware."""
        if v is not None and v.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return v


class WebSocketUpdate(BaseModel):
    """
    WebSocket update message model.

    Based on websocket_live_ohlcv_example.py expected message format for
    real-time OHLCV updates.
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        validate_assignment=True,
    )

    type: str = Field(
        ...,
        description="Type of update (e.g., 'ohlcv_update', 'error', 'subscription_confirmed')",
    )
    exchange: str = Field(..., description="Exchange name for the update")
    symbol: str = Field(..., description="Trading pair symbol for the update")
    timeframe: str = Field(..., description="Timeframe for the OHLCV update")
    data: dict[str, Any] = Field(
        ..., description="Update data payload (OHLCV, error details, etc.)"
    )
    timestamp: datetime = Field(..., description="Timestamp of the update")

    # Subscription tracking
    subscription_id: Optional[str] = Field(
        default=None, description="Unique identifier for the subscription"
    )
    sequence: Optional[int] = Field(
        default=None, ge=0, description="Sequence number for ordering updates"
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        if v.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        return v


class ErrorResponse(BaseResponse):
    """
    Error response model for API errors.

    Standardized error format for all API endpoints.
    """

    success: bool = Field(default=False, description="Always False for error responses")
    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(
        ..., ge=400, le=599, description="HTTP status code for the error"
    )
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Additional error details and context"
    )

    # Request context (helpful for debugging)
    request_id: Optional[str] = Field(
        default=None, description="Unique identifier for the request"
    )
    path: Optional[str] = Field(
        default=None, description="API endpoint path that generated the error"
    )


class ExchangesResponse(BaseResponse):
    """
    Response model for exchange catalog endpoints.

    Lists available exchanges with optional statistics.
    """

    exchanges: list[dict[str, Any]] = Field(
        ..., description="List of available exchanges"
    )
    count: int = Field(..., ge=0, description="Number of exchanges returned")
    total_available: Optional[int] = Field(
        default=None, ge=0, description="Total number of exchanges available"
    )


class SymbolsResponse(BaseResponse):
    """
    Response model for symbol catalog endpoints.

    Lists available trading pairs for an exchange.
    """

    symbols: list[dict[str, Any]] = Field(
        ..., description="List of available trading pairs"
    )
    count: int = Field(..., ge=0, description="Number of symbols returned")
    exchange: str = Field(..., description="Exchange name for the symbols")
    total_available: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total number of symbols available on the exchange",
    )

    # Filter context (if filters were applied)
    base_currency: Optional[str] = Field(
        default=None, description="Base currency filter that was applied"
    )
    quote_currency: Optional[str] = Field(
        default=None, description="Quote currency filter that was applied"
    )


class HealthResponse(BaseResponse):
    """
    Response model for health check endpoints.

    Provides API health and status information.
    """

    status: str = Field(
        ..., description="Overall API status (healthy, degraded, unhealthy)"
    )
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., ge=0, description="API uptime in seconds")

    # Component health status
    database: Optional[dict[str, Any]] = Field(
        default=None, description="Database connection health"
    )
    dependencies: Optional[dict[str, Any]] = Field(
        default=None, description="External dependency health status"
    )


class ValidationErrorDetail(BaseModel):
    """
    Detailed validation error information.

    Used within ErrorResponse for Pydantic validation errors.
    """

    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any = Field(
        default=None, description="The invalid value that was provided"
    )
    constraint: Optional[str] = Field(
        default=None, description="Validation constraint that was violated"
    )


class PaginatedResponse(BaseResponse):
    """
    Base model for paginated responses.

    Can be extended by other response models that support pagination.
    """

    page: int = Field(default=1, ge=1, description="Current page number")
    per_page: int = Field(
        default=100, ge=1, le=5000, description="Number of items per page"
    )
    total_pages: Optional[int] = Field(
        default=None, ge=0, description="Total number of pages available"
    )
    total_items: Optional[int] = Field(
        default=None, ge=0, description="Total number of items available"
    )
    has_next: bool = Field(
        default=False, description="Whether there are more pages available"
    )
    has_previous: bool = Field(
        default=False, description="Whether there are previous pages available"
    )
