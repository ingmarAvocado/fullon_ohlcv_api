"""
Candles router for fullon_ohlcv_api.

This module implements READ-ONLY candle data endpoints that follow the exact
specification defined by candle_repository_example.py.
"""

from datetime import datetime

import arrow
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import TimeseriesRepository

from ..dependencies.database import (
    get_timeseries_repository as _get_timeseries_repository,
)
from ..models.responses import CandlesResponse

logger = get_component_logger("fullon.api.ohlcv.candles")

router = APIRouter()


async def get_timeseries_repository(
    exchange: str = Path(...),
    base_currency: str = Path(...),
    quote_currency: str = Path(...),
):
    """Wrapper for timeseries repository dependency with path parameters."""
    symbol = f"{base_currency}/{quote_currency}"
    async for repo in _get_timeseries_repository(exchange, symbol):
        yield repo


def convert_timeframe_to_compression(timeframe: str) -> tuple[int, str]:
    """
    Convert human-readable timeframe to compression and period.

    Args:
        timeframe: Human-readable timeframe (e.g., '1h', '5m', '1d')

    Returns:
        tuple: (compression, period) for TimeseriesRepository.fetch_ohlcv

    Raises:
        HTTPException: 422 status code if timeframe is invalid
    """
    timeframe_map = {
        # Minutes
        "1m": (1, "minutes"),
        "3m": (3, "minutes"),
        "5m": (5, "minutes"),
        "15m": (15, "minutes"),
        "30m": (30, "minutes"),
        # Hours
        "1h": (1, "hours"),
        "2h": (2, "hours"),
        "4h": (4, "hours"),
        "6h": (6, "hours"),
        "8h": (8, "hours"),
        "12h": (12, "hours"),
        # Days
        "1d": (1, "days"),
        "3d": (3, "days"),
        # Weeks
        "1w": (1, "weeks"),
        # Months
        "1M": (1, "months"),
    }

    if timeframe not in timeframe_map:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid timeframe '{timeframe}'. Supported: {', '.join(sorted(timeframe_map.keys()))}",
        )

    return timeframe_map[timeframe]


@router.get(
    "/{exchange}/{base_currency}/{quote_currency}/{timeframe}",
    response_model=CandlesResponse,
)
async def get_recent_candles(
    exchange: str = Path(
        ..., description="Exchange name (e.g., 'binance', 'coinbase')"
    ),
    base_currency: str = Path(..., description="Base currency (e.g., 'BTC', 'ETH')"),
    quote_currency: str = Path(..., description="Quote currency (e.g., 'USDT', 'USD')"),
    timeframe: str = Path(..., description="Timeframe (e.g., '1h', '1d', '5m')"),
    limit: int = Query(
        default=100, ge=1, le=5000, description="Number of candles to retrieve"
    ),
    repo: TimeseriesRepository = Depends(get_timeseries_repository),
) -> CandlesResponse:
    """
    Get recent candles for a specific exchange, symbol, and timeframe.

    This endpoint matches the specification from candle_repository_example.py:
    - GET /api/candles/{exchange}/{base_currency}/{quote_currency}/{timeframe}?limit=10
    - Response format: {"candles": [...], "count": int, ...}

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        base_currency: Base currency (e.g., 'BTC', 'ETH')
        quote_currency: Quote currency (e.g., 'USDT', 'USD')
        timeframe: Candle timeframe (e.g., '1h', '1d', '5m')
        limit: Maximum number of candles to retrieve (default: 100)
        repo: CandleRepository dependency

    Returns:
        CandlesResponse: Candle data with standardized format
    """
    # Combine symbol from base and quote currencies
    symbol = f"{base_currency}/{quote_currency}"

    # Convert timeframe to compression and period
    compression, period = convert_timeframe_to_compression(timeframe)

    logger.info(
        "Getting recent candles",
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        compression=compression,
        period=period,
        limit=limit,
    )

    # Calculate time range for recent candles based on timeframe and limit
    end_time = arrow.now()
    if period == "minutes":
        start_time = end_time.shift(minutes=-compression * limit)
    elif period == "hours":
        start_time = end_time.shift(hours=-compression * limit)
    elif period == "days":
        start_time = end_time.shift(days=-compression * limit)
    elif period == "weeks":
        start_time = end_time.shift(weeks=-compression * limit)
    elif period == "months":
        start_time = end_time.shift(months=-compression * limit)
    else:
        start_time = end_time.shift(hours=-24)  # Default fallback

    # Retrieve OHLCV data using TimeseriesRepository
    ohlcv_data = await repo.fetch_ohlcv(
        compression=compression, period=period, fromdate=start_time, todate=end_time
    )

    # Convert OHLCV tuples to dict format for response
    # fetch_ohlcv returns: List[(timestamp, open, high, low, close, volume)]
    candles_data = [
        {
            "timestamp": timestamp.datetime.isoformat()
            if hasattr(timestamp, "datetime")
            else timestamp.isoformat(),
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "vol": float(volume),
        }
        for timestamp, open_price, high_price, low_price, close_price, volume in ohlcv_data[
            -limit:
        ]  # Get last N candles
    ]

    logger.info(
        "Retrieved recent candles",
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        count=len(candles_data),
    )

    return CandlesResponse(
        candles=candles_data,
        count=len(candles_data),
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )


@router.get(
    "/{exchange}/{base_currency}/{quote_currency}/{timeframe}/range",
    response_model=CandlesResponse,
)
async def get_candles_in_range(
    exchange: str = Path(
        ..., description="Exchange name (e.g., 'binance', 'coinbase')"
    ),
    base_currency: str = Path(..., description="Base currency (e.g., 'BTC', 'ETH')"),
    quote_currency: str = Path(..., description="Quote currency (e.g., 'USDT', 'USD')"),
    timeframe: str = Path(..., description="Timeframe (e.g., '1h', '1d', '5m')"),
    start_time: datetime = Query(
        ..., description="Start time for candle range (ISO format)"
    ),
    end_time: datetime = Query(
        ..., description="End time for candle range (ISO format)"
    ),
    repo: TimeseriesRepository = Depends(get_timeseries_repository),
) -> CandlesResponse:
    """
    Get candles within a specific time range for an exchange, symbol, and timeframe.

    This endpoint matches the specification from candle_repository_example.py:
    - GET /api/candles/{exchange}/{base_currency}/{quote_currency}/{timeframe}/range
    - Parameters: start_time, end_time (ISO format)
    - Response format: {"candles": [...], "count": int, ...}

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        base_currency: Base currency (e.g., 'BTC', 'ETH')
        quote_currency: Quote currency (e.g., 'USDT', 'USD')
        timeframe: Candle timeframe (e.g., '1h', '1d', '5m')
        start_time: Start time for the range query (timezone-aware)
        end_time: End time for the range query (timezone-aware)
        repo: CandleRepository dependency

    Returns:
        CandlesResponse: Candle data within the specified range
    """
    # Combine symbol from base and quote currencies
    symbol = f"{base_currency}/{quote_currency}"

    # Convert timeframe to compression and period
    compression, period = convert_timeframe_to_compression(timeframe)

    logger.info(
        "Getting candles in range",
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        compression=compression,
        period=period,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
    )

    # Convert datetime to arrow for TimeseriesRepository
    start_arrow = arrow.get(start_time)
    end_arrow = arrow.get(end_time)

    # Retrieve OHLCV data using TimeseriesRepository
    ohlcv_data = await repo.fetch_ohlcv(
        compression=compression, period=period, fromdate=start_arrow, todate=end_arrow
    )

    # Convert OHLCV tuples to dict format for response
    # fetch_ohlcv returns: List[(timestamp, open, high, low, close, volume)]
    candles_data = [
        {
            "timestamp": timestamp.datetime.isoformat()
            if hasattr(timestamp, "datetime")
            else timestamp.isoformat(),
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "vol": float(volume),
        }
        for timestamp, open_price, high_price, low_price, close_price, volume in ohlcv_data
    ]

    logger.info(
        "Retrieved candles in range",
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        count=len(candles_data),
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
    )

    return CandlesResponse(
        candles=candles_data,
        count=len(candles_data),
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        start_time=start_time,
        end_time=end_time,
    )
