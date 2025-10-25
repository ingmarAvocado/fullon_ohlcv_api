"""
Candles router for fullon_ohlcv_api.

This module implements READ-ONLY candle data endpoints that follow the exact
specification defined by candle_repository_example.py.
"""

from datetime import datetime

import arrow
from fastapi import APIRouter, HTTPException, Path, Query
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import TimeseriesRepository  # type: ignore

# No dependency injection required for TimeseriesRepository (created per-request)
from ..models.responses import CandlesResponse

logger = get_component_logger("fullon.api.ohlcv.candles")

router = APIRouter()


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


# No Python aggregation helpers by design. Aggregation must occur in TimescaleDB.


@router.get(
    "/{exchange}/{symbol:path}/{timeframe}/range", response_model=CandlesResponse
)
async def get_candles_in_range(  # type: ignore[no-any-unimported]
    exchange: str = Path(
        ..., description="Exchange name (e.g., 'binance', 'coinbase')"
    ),
    symbol: str = Path(..., description="Trading pair (e.g., 'BTC/USDT')"),
    timeframe: str = Path(..., description="Timeframe (e.g., '1h', '1d', '5m')"),
    start_time: datetime = Query(
        ..., description="Start time for candle range (ISO format)"
    ),
    end_time: datetime = Query(
        ..., description="End time for candle range (ISO format)"
    ),
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

    async with TimeseriesRepository(exchange, symbol) as ts_repo:
        tuples = await ts_repo.fetch_ohlcv(
            compression=compression,
            period=period,
            fromdate=arrow.get(start_time),
            todate=arrow.get(end_time),
        )

    def _f(x):
        return float(x) if x is not None else 0.0

    candles_data = [
        {
            "timestamp": (
                ts.datetime.isoformat() if hasattr(ts, "datetime") else ts.isoformat()
            ),
            "open": _f(o),
            "high": _f(h),
            "low": _f(l),
            "close": _f(c),
            "vol": _f(v),
        }
        for ts, o, h, l, c, v in tuples
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


@router.get("/{exchange}/{symbol:path}/{timeframe}", response_model=CandlesResponse)
async def get_recent_candles(  # type: ignore[no-any-unimported]
    exchange: str = Path(
        ..., description="Exchange name (e.g., 'binance', 'coinbase')"
    ),
    symbol: str = Path(..., description="Trading pair (e.g., 'BTC/USDT')"),
    timeframe: str = Path(..., description="Timeframe (e.g., '1h', '1d', '5m')"),
    limit: int = Query(
        default=100, ge=1, le=5000, description="Number of candles to retrieve"
    ),
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
    # Validate timeframe and derive an approximate recent window
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

    # Compute a time window and query via CandleRepository (READ-ONLY)
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
        start_time = end_time.shift(hours=-24)

    async with TimeseriesRepository(exchange, symbol) as ts_repo:
        tuples = await ts_repo.fetch_ohlcv(
            compression=compression,
            period=period,
            fromdate=start_time,
            todate=end_time,
        )

    # Keep only the last N entries
    tuples = tuples[-limit:]

    def _f(x):
        return float(x) if x is not None else 0.0

    candles_data = [
        {
            "timestamp": (
                ts.datetime.isoformat() if hasattr(ts, "datetime") else ts.isoformat()
            ),
            "open": _f(o),
            "high": _f(h),
            "low": _f(l),
            "close": _f(c),
            "vol": _f(v),
        }
        for ts, o, h, l, c, v in tuples
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
