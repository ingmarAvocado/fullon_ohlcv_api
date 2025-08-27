"""
Trades router for fullon_ohlcv_api.

This module implements READ-ONLY trade data endpoints that follow the exact
specification defined by trade_repository_example.py.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fullon_log import get_component_logger
from fullon_ohlcv.repositories.ohlcv import TradeRepository

from ..dependencies.database import get_trade_repository
from ..models.responses import TradesResponse

logger = get_component_logger("fullon.api.ohlcv.trades")

router = APIRouter()


@router.get("/{exchange}/{symbol}", response_model=TradesResponse)
async def get_recent_trades(
    exchange: str,
    symbol: str,
    limit: int = Query(
        default=100, ge=1, le=5000, description="Number of trades to retrieve"
    ),
    repo: TradeRepository = Depends(get_trade_repository),
) -> TradesResponse:
    """
    Get recent trades for a specific exchange and symbol.

    This endpoint matches the specification from trade_repository_example.py:
    - GET /api/trades/{exchange}/{symbol}?limit=10
    - Response format: {"trades": [...], "count": int, ...}

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')
        limit: Maximum number of trades to retrieve (default: 100)
        repo: TradeRepository dependency

    Returns:
        TradesResponse: Trade data with standardized format
    """
    logger.info("Getting recent trades", exchange=exchange, symbol=symbol, limit=limit)

    # Retrieve recent trades using fullon_ohlcv TradeRepository
    trades = await repo.get_recent_trades(limit=limit)

    # Convert trades to dict format for response
    trades_data = [
        {
            "timestamp": trade.timestamp.isoformat(),
            "price": float(trade.price),
            "volume": float(trade.volume),
            "side": trade.side,
            "type": trade.type,
        }
        for trade in trades
    ]

    logger.info(
        "Retrieved recent trades",
        exchange=exchange,
        symbol=symbol,
        count=len(trades_data),
    )

    return TradesResponse(
        trades=trades_data,
        count=len(trades_data),
        exchange=exchange,
        symbol=symbol,
        limit=limit,
    )


@router.get("/{exchange}/{symbol}/range", response_model=TradesResponse)
async def get_trades_in_range(
    exchange: str,
    symbol: str,
    start_time: datetime = Query(
        ..., description="Start time for trade range (ISO format)"
    ),
    end_time: datetime = Query(
        ..., description="End time for trade range (ISO format)"
    ),
    limit: int = Query(
        default=1000, ge=1, le=10000, description="Maximum number of trades to retrieve"
    ),
    repo: TradeRepository = Depends(get_trade_repository),
) -> TradesResponse:
    """
    Get trades within a specific time range for an exchange and symbol.

    This endpoint matches the specification from trade_repository_example.py:
    - GET /api/trades/{exchange}/{symbol}/range
    - Parameters: start_time, end_time (ISO format)
    - Response format: {"trades": [...], "count": int, ...}

    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')
        start_time: Start time for the range query (timezone-aware)
        end_time: End time for the range query (timezone-aware)
        limit: Maximum number of trades to retrieve (default: 1000)
        repo: TradeRepository dependency

    Returns:
        TradesResponse: Trade data within the specified range
    """
    logger.info(
        "Getting trades in range",
        exchange=exchange,
        symbol=symbol,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        limit=limit,
    )

    # Retrieve trades in range using fullon_ohlcv TradeRepository
    trades = await repo.get_trades_in_range(
        start_time=start_time, end_time=end_time, limit=limit
    )

    # Convert trades to dict format for response
    trades_data = [
        {
            "timestamp": trade.timestamp.isoformat(),
            "price": float(trade.price),
            "volume": float(trade.volume),
            "side": trade.side,
            "type": trade.type,
        }
        for trade in trades
    ]

    logger.info(
        "Retrieved trades in range",
        exchange=exchange,
        symbol=symbol,
        count=len(trades_data),
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
    )

    return TradesResponse(
        trades=trades_data,
        count=len(trades_data),
        exchange=exchange,
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
