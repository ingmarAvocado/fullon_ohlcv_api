"""
Timeseries router for fullon_ohlcv_api.

This module implements OHLCV aggregation endpoints that follow the exact
specification defined by timeseries_repository_example.py.
"""

from datetime import datetime

import arrow
from fastapi import APIRouter, Depends, Query
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import TimeseriesRepository

from ..dependencies.database import get_timeseries_repository
from ..models.responses import TimeseriesResponse

logger = get_component_logger("fullon.api.ohlcv.timeseries")

router = APIRouter()


@router.get("/{exchange}/{symbol}/ohlcv", response_model=TimeseriesResponse)
async def get_ohlcv_aggregation(
    exchange: str,
    symbol: str,
    timeframe: str = Query(
        default="1m",
        description="Timeframe for OHLCV aggregation (e.g., '1m', '5m', '1h')",
    ),
    start_time: datetime = Query(
        ..., description="Start time for aggregation range (ISO format)"
    ),
    end_time: datetime = Query(
        ..., description="End time for aggregation range (ISO format)"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of OHLCV candles to generate",
    ),
    repo: TimeseriesRepository = Depends(get_timeseries_repository),
) -> TimeseriesResponse:
    """
    Generate OHLCV candles from trade data via timeseries aggregation.

    This endpoint matches the specification from timeseries_repository_example.py:
    - GET /api/timeseries/{exchange}/{symbol}/ohlcv
    - Parameters: timeframe, start_time, end_time, limit
    - Response format: {"ohlcv": [...], "count": int, ...}

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')
        timeframe: Timeframe for aggregation (e.g., '1m', '5m', '1h', '1d')
        start_time: Start time for the aggregation range (timezone-aware)
        end_time: End time for the aggregation range (timezone-aware)
        limit: Maximum number of OHLCV candles to generate (default: 100)
        repo: TimeseriesRepository dependency

    Returns:
        TimeseriesResponse: Generated OHLCV data with metadata
    """
    logger.info(
        "Generating OHLCV aggregation",
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        limit=limit,
    )

    # Convert datetime to Arrow objects
    fromdate = arrow.get(start_time)
    todate = arrow.get(end_time)

    # Map timeframe string to compression and period
    timeframe_mapping = {
        "1m": (1, "minute"),
        "5m": (5, "minute"),
        "15m": (15, "minute"),
        "30m": (30, "minute"),
        "1h": (1, "hour"),
        "4h": (4, "hour"),
        "1d": (1, "day"),
    }

    if timeframe not in timeframe_mapping:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422, detail=f"Unsupported timeframe: {timeframe}"
        )

    compression, period = timeframe_mapping[timeframe]

    # Generate OHLCV data using fullon_ohlcv TimeseriesRepository
    ohlcv_data = await repo.fetch_ohlcv(
        compression=compression,
        period=period,
        fromdate=fromdate,
        todate=todate,
    )

    # Convert OHLCV candles to dict format for response
    ohlcv_list = [
        {
            "timestamp": candle.timestamp.isoformat(),
            "open": float(candle.open),
            "high": float(candle.high),
            "low": float(candle.low),
            "close": float(candle.close),
            "vol": float(candle.vol),
        }
        for candle in ohlcv_data
    ]

    logger.info(
        "Generated OHLCV aggregation",
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        count=len(ohlcv_list),
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
    )

    return TimeseriesResponse(
        ohlcv=ohlcv_list,
        count=len(ohlcv_list),
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        start_time=start_time,
        end_time=end_time,
    )
