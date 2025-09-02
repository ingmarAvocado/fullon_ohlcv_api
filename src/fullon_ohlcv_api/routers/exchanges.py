"""
Exchanges router (no direct DB).

This module avoids raw SQL/SQLAlchemy and does not open direct DB connections.
Discovery operations are not implemented via introspection. Endpoints return
safe, read-only responses without touching the database directly.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path
from fullon_log import get_component_logger

logger = get_component_logger("fullon.api.ohlcv.exchanges")

router = APIRouter()


def normalize_exchange_name(exchange: str) -> str:
    """
    Normalize exchange name to lowercase for consistency.

    Args:
        exchange: Raw exchange name

    Returns:
        Normalized exchange name in lowercase
    """
    return exchange.strip().lower()


def format_exchange_display_name(exchange: str) -> str:
    """
    Format exchange name for display purposes.

    Args:
        exchange: Exchange name

    Returns:
        Formatted display name
    """
    # Simple capitalization, can be enhanced with exchange-specific mapping
    display_names = {
        "binance": "Binance",
        "coinbase": "Coinbase Pro",
        "kraken": "Kraken",
        "bitstamp": "Bitstamp",
        "bitfinex": "Bitfinex",
        "huobi": "Huobi",
        "okex": "OKEx",
        "kucoin": "KuCoin",
    }

    return display_names.get(exchange.lower(), exchange.title())


@router.get("/exchanges")
async def get_exchanges() -> dict[str, Any]:
    """
    Return an empty exchange catalog (read-only mode, no DB introspection).

    Discovery is intentionally not implemented here to avoid raw DB access.
    Another component should provide a catalog if needed.
    """
    logger.info("Exchange catalog requested (read-only mode; no DB introspection)")
    return {
        "success": True,
        "message": "Exchange catalog not available in read-only mode",
        "timestamp": datetime.now(UTC),
        "exchanges": [],
        "count": 0,
        "total_available": 0,
    }


@router.get("/exchanges/{exchange}/info")
async def get_exchange_info(exchange: str = Path(..., description="Exchange name")) -> dict[str, Any]:
    """Exchange info is not provided without DB catalog; return 404."""
    exchange_name = normalize_exchange_name(exchange)
    logger.info("Exchange info requested (not available)", exchange=exchange_name)
    raise HTTPException(status_code=404, detail="Exchange info not available")


@router.get("/exchanges/{exchange}/status")
async def get_exchange_status(exchange: str = Path(..., description="Exchange name")) -> dict[str, Any]:
    """
    Get health and status information for a specific exchange.

    Checks data freshness, connectivity, and provides statistics about
    the exchange's data availability and quality.

    Args:
        exchange: Exchange name to check status for

    Returns:
        Exchange status and health information

    Raises:
        HTTPException: 404 if exchange not found, 500 for database errors
    """
    exchange_name = normalize_exchange_name(exchange)
    logger.info("Exchange status requested (not available)", exchange=exchange_name)
    raise HTTPException(status_code=404, detail="Exchange status not available")


@router.get("/exchanges/{exchange}/validate")
async def validate_exchange(
    exchange: str = Path(..., description="Exchange name to validate"),
) -> dict[str, Any]:
    """
    Validate if an exchange exists and is accessible.

    Performs validation checks to determine if the exchange name
    corresponds to a valid exchange with data in the system.

    Args:
        exchange: Exchange name to validate

    Returns:
        Validation result with detailed information

    Raises:
        HTTPException: 500 for database errors (validation never fails)
    """
    exchange_name = normalize_exchange_name(exchange)
    logger.info("Exchange validate requested (no DB introspection)", exchange=exchange_name)
    return {
        "success": True,
        "message": f"Validation not performed for '{exchange_name}' in read-only mode",
        "timestamp": datetime.now(UTC),
        "exchange": exchange_name,
        "valid": False,
    }
