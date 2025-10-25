"""
Timeseries router for fullon_ohlcv_api.

This module implements OHLCV aggregation endpoints that follow the exact
specification defined by timeseries_repository_example.py.
"""

from datetime import datetime

import arrow
from fastapi import APIRouter, HTTPException, Path, Query
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import TimeseriesRepository  # type: ignore

from ..models.responses import TimeseriesResponse
from .candles import convert_timeframe_to_compression

logger = get_component_logger("fullon.api.ohlcv.timeseries")

router = APIRouter()


@router.get("/{exchange}/{symbol:path}/ohlcv", response_model=TimeseriesResponse)
async def get_ohlcv_aggregation(  # type: ignore[no-any-unimported]
    exchange: str = Path(..., description="Exchange name"),
    symbol: str = Path(..., description="Trading pair (e.g., 'BTC/USDT')"),
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
    limit: int | None = Query(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of OHLCV candles to generate",
    ),
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

    try:
        # Validate timeframe and convert to repo parameters (ensure 422 precedes repo init)
        compression, period = convert_timeframe_to_compression(timeframe)

        # Timescale-only aggregation path
        async with TimeseriesRepository(exchange, symbol) as repo:
            start_arrow = arrow.get(start_time)
            end_arrow = arrow.get(end_time)

            tuples = await repo.fetch_ohlcv(
                compression=compression,
                period=period,
                fromdate=start_arrow,
                todate=end_arrow,
            )

        # Apply limit on the result if provided
        if limit is not None:
            tuples = tuples[-limit:]

        # Convert tuples to dicts (handle potential NULLs from gapfill/LOCF)
        def _f(x):
            return float(x) if x is not None else 0.0

        ohlcv_list = [
            {
                "timestamp": (
                    ts.datetime.isoformat()
                    if hasattr(ts, "datetime")
                    else ts.isoformat()
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

    except HTTPException:
        # Preserve explicit HTTP errors like 422 for invalid timeframe
        raise
    except Exception as e:
        logger.error(
            "OHLCV aggregation failed",
            error=str(e),
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate OHLCV data: {str(e)}"
        ) from e
