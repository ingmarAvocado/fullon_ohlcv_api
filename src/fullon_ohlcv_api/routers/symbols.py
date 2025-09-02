"""
Symbols router (no direct DB access).

This module avoids raw SQL/SQLAlchemy and does not open direct DB connections
for symbol discovery. Endpoints return safe, read-only responses without
introspection. Discovery should be delegated to a separate catalog component
or to fullon_ohlcv when it exposes such APIs.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from fullon_log import get_component_logger

logger = get_component_logger("fullon.api.ohlcv.symbols")

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


def normalize_symbol_name(symbol: str) -> str:
    """
    Normalize symbol name for URL paths (replace / with encoded form).

    Args:
        symbol: Symbol in format like BTC/USDT

    Returns:
        Normalized symbol name
    """
    return symbol.strip().upper()


def extract_symbol_from_table_name(table_name: str) -> str | None:
    """
    Extract trading symbol from database table name.

    Table patterns:
    - {base}_{quote}_trades -> BASE/QUOTE
    - {base}_{quote}_candles{timeframe} -> BASE/QUOTE

    Args:
        table_name: Database table name

    Returns:
        Normalized symbol (e.g., "BTC/USDT") or None if not a valid pattern
    """
    try:
        # Remove common suffixes
        table_name = table_name.lower()

        # Handle trades tables
        if table_name.endswith("_trades"):
            symbol_part = table_name[:-7]  # Remove "_trades"
        # Handle candles tables (with timeframe suffixes)
        elif "_candles" in table_name:
            symbol_part = table_name.split("_candles")[0]
        else:
            return None

        # Split into base and quote currencies
        parts = symbol_part.split("_")
        if len(parts) != 2:
            return None

        base, quote = parts
        return f"{base.upper()}/{quote.upper()}"

    except Exception:
        logger.debug("Failed to extract symbol from table name", table_name=table_name)
        return None


def get_data_types_for_symbol(tables: list[dict[str, str]], symbol: str) -> list[str]:
    """
    Determine available data types (trades, candles) for a symbol.

    Args:
        tables: List of table dictionaries with table_name
        symbol: Symbol to check for (e.g., "BTC/USDT")

    Returns:
        List of available data types
    """
    data_types = []
    symbol_lower = symbol.lower().replace("/", "_")

    for table in tables:
        table_name = table["table_name"].lower()

        # Check if this table belongs to the symbol
        if table_name.startswith(symbol_lower):
            if table_name.endswith("_trades"):
                if "trades" not in data_types:
                    data_types.append("trades")
            elif "_candles" in table_name:
                if "candles" not in data_types:
                    data_types.append("candles")

    return sorted(data_types)


def parse_symbol_components(symbol: str) -> tuple[str, str]:
    """
    Parse symbol into base and quote currencies.

    Args:
        symbol: Symbol like "BTC/USDT"

    Returns:
        Tuple of (base_currency, quote_currency)
    """
    try:
        parts = symbol.split("/")
        if len(parts) == 2:
            return parts[0].upper(), parts[1].upper()
        else:
            return symbol.upper(), ""
    except Exception:
        return symbol.upper(), ""


@router.get("/exchanges/{exchange}/symbols")
async def get_exchange_symbols(
    exchange: str = Path(..., description="Exchange name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of symbols to return"),
    offset: int = Query(0, ge=0, description="Number of symbols to skip"),
) -> dict[str, Any]:
    """Return empty symbol list (no DB introspection)."""
    exchange_name = normalize_exchange_name(exchange)
    logger.info("Symbol list requested (no DB introspection)", exchange=exchange_name)
    return {
        "success": True,
        "message": f"Symbol catalog not available for {exchange_name}",
        "timestamp": datetime.now(UTC),
        "exchange": exchange_name,
        "symbols": [],
        "count": 0,
        "total_available": 0,
        "pagination": {"limit": limit, "offset": offset, "total": 0, "has_more": False},
    }


@router.get("/exchanges/{exchange}/symbols/{symbol:path}/info")
async def get_symbol_info(
    exchange: str = Path(..., description="Exchange name"),
    symbol: str = Path(..., description="Symbol name (e.g., BTC/USDT)"),
) -> dict[str, Any]:
    """
    Get detailed information about a specific trading symbol.

    Retrieves symbol metadata including data availability, timestamps,
    and record counts from the database.

    Args:
        exchange: Exchange name
        symbol: Symbol name in format BASE/QUOTE
        connection: Database connection dependency

    Returns:
        Detailed symbol information with statistics and metadata

    Raises:
        HTTPException: 404 if exchange/symbol not found, 500 for database errors
    """
    exchange_name = normalize_exchange_name(exchange)
    symbol_name = normalize_symbol_name(symbol)
    logger.info("Symbol info requested (not available)", exchange=exchange_name, symbol=symbol_name)
    raise HTTPException(status_code=404, detail="Symbol info not available")


@router.get("/exchanges/{exchange}/symbols/{symbol:path}/metadata")
async def get_symbol_metadata(
    exchange: str = Path(..., description="Exchange name"),
    symbol: str = Path(..., description="Symbol name (e.g., BTC/USDT)"),
) -> dict[str, Any]:
    """
    Get comprehensive metadata and statistics for a specific symbol.

    Provides detailed statistics about data availability, freshness,
    table information, and data quality metrics.

    Args:
        exchange: Exchange name
        symbol: Symbol name in format BASE/QUOTE
        connection: Database connection dependency

    Returns:
        Comprehensive symbol metadata and statistics

    Raises:
        HTTPException: 404 if exchange/symbol not found, 500 for database errors
    """
    exchange_name = normalize_exchange_name(exchange)
    symbol_name = normalize_symbol_name(symbol)
    logger.info("Symbol metadata requested (not available)", exchange=exchange_name, symbol=symbol_name)
    raise HTTPException(status_code=404, detail="Symbol metadata not available")


@router.get("/symbols/search")
async def search_symbols(
    q: str = Query(..., description="Search query for symbol names"),
    exchange: str | None = Query(None, description="Filter by specific exchange"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
) -> dict[str, Any]:
    """
    Search for trading symbols across exchanges with optional filtering.

    Supports fuzzy matching and cross-exchange symbol discovery.
    Search is case-insensitive and matches against symbol names.

    Args:
        q: Search query string
        exchange: Optional exchange filter
        limit: Maximum number of search results
        connection: Database connection dependency

    Returns:
        Search results with matching symbols across exchanges

    Raises:
        HTTPException: 500 for database errors
    """
    search_query = q.strip().upper()
    exchange_filter = normalize_exchange_name(exchange) if exchange else None

    logger.info(
        "Symbol search requested (no DB introspection)", query=search_query, exchange_filter=exchange_filter
    )
    return {
        "success": True,
        "message": "Symbol search not available in read-only mode",
        "timestamp": datetime.now(UTC),
        "query": q,
        "exchange_filter": exchange_filter,
        "results": [],
        "count": 0,
        "total_matches": 0,
        "truncated": False,
    }
