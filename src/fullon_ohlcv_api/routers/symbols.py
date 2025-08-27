"""
Symbols router for fullon_ohlcv_api.

This module provides READ-ONLY endpoints for discovering and searching
available trading symbols per exchange through database table introspection.

Endpoints:
- GET /exchanges/{exchange}/symbols - Get all symbols for specific exchange
- GET /exchanges/{exchange}/symbols/{symbol}/info - Get detailed symbol information
- GET /exchanges/{exchange}/symbols/{symbol}/metadata - Get symbol metadata and statistics
- GET /symbols/search - Search symbols across exchanges with filtering
"""

from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fullon_log import get_component_logger

from ..dependencies.database import get_database_connection

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


def extract_symbol_from_table_name(table_name: str) -> Optional[str]:
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
        logger.debug(f"Failed to extract symbol from table name: {table_name}")
        return None


def get_data_types_for_symbol(tables: list[dict], symbol: str) -> list[str]:
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
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of symbols to return"
    ),
    offset: int = Query(0, ge=0, description="Number of symbols to skip"),
    connection=Depends(get_database_connection),
) -> dict[str, Any]:
    """
    Get all trading symbols available for a specific exchange.

    Discovers symbols by introspecting database tables in the exchange schema.
    Tables follow patterns like {symbol}_trades and {symbol}_candles{timeframe}.

    Args:
        exchange: Exchange name to get symbols for
        limit: Maximum number of symbols to return
        offset: Number of symbols to skip for pagination
        connection: Database connection dependency

    Returns:
        List of available symbols with metadata and pagination info

    Raises:
        HTTPException: 404 if exchange not found, 500 for database errors
    """
    exchange_name = normalize_exchange_name(exchange)

    try:
        logger.info("Discovering symbols for exchange", exchange=exchange_name)

        # Check if exchange exists
        check_query = """
        SELECT EXISTS(
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = $1
        ) as exists
        """

        existence_result = await connection.fetchrow(check_query, exchange_name)

        if not existence_result["exists"]:
            logger.warning(
                "Exchange not found for symbol discovery", exchange=exchange_name
            )
            raise HTTPException(
                status_code=404, detail=f"Exchange '{exchange_name}' not found"
            )

        # Get all tables in the exchange schema
        tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = $1 AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        table_rows = await connection.fetch(tables_query, exchange_name)

        # Extract unique symbols from table names
        symbols_dict = {}

        for row in table_rows:
            table_name = row["table_name"]
            symbol = extract_symbol_from_table_name(table_name)

            if symbol:
                if symbol not in symbols_dict:
                    symbols_dict[symbol] = []
                symbols_dict[symbol].append({"table_name": table_name})

        # Build symbol list with metadata
        symbols_list = []
        for symbol, tables in symbols_dict.items():
            base_currency, quote_currency = parse_symbol_components(symbol)
            data_types = get_data_types_for_symbol(tables, symbol)

            symbol_info = {
                "symbol": symbol,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "data_types": data_types,
                "table_count": len(tables),
            }

            symbols_list.append(symbol_info)

        # Sort symbols consistently
        symbols_list.sort(key=lambda x: x["symbol"])

        # Apply pagination
        total_count = len(symbols_list)
        paginated_symbols = symbols_list[offset : offset + limit]

        logger.info(
            "Symbol discovery completed",
            exchange=exchange_name,
            total_symbols=total_count,
            returned_symbols=len(paginated_symbols),
        )

        return {
            "success": True,
            "message": f"Found {total_count} symbols for exchange {exchange_name}",
            "timestamp": datetime.now(UTC),
            "exchange": exchange_name,
            "symbols": paginated_symbols,
            "count": len(paginated_symbols),
            "total_available": total_count,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_more": offset + limit < total_count,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to discover symbols", exchange=exchange_name, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Symbol discovery error: {str(e)}"
        ) from e


@router.get("/exchanges/{exchange}/symbols/{symbol:path}/info")
async def get_symbol_info(
    exchange: str = Path(..., description="Exchange name"),
    symbol: str = Path(..., description="Symbol name (e.g., BTC/USDT)"),
    connection=Depends(get_database_connection),
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

    try:
        logger.info(
            "Retrieving symbol information", exchange=exchange_name, symbol=symbol_name
        )

        # Check if exchange exists
        check_query = """
        SELECT EXISTS(
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = $1
        ) as exists
        """

        existence_result = await connection.fetchrow(check_query, exchange_name)

        if not existence_result["exists"]:
            logger.warning("Exchange not found for symbol info", exchange=exchange_name)
            raise HTTPException(
                status_code=404, detail=f"Exchange '{exchange_name}' not found"
            )

        # Convert symbol to table name format
        table_symbol = symbol_name.lower().replace("/", "_")

        # Check if symbol tables exist
        symbol_check_query = """
        SELECT COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = $1
        AND table_type = 'BASE TABLE'
        AND (table_name LIKE $2 OR table_name LIKE $3)
        """

        symbol_result = await connection.fetchrow(
            symbol_check_query,
            exchange_name,
            f"{table_symbol}_trades",
            f"{table_symbol}_candles%",
        )

        if not symbol_result or symbol_result["table_count"] == 0:
            logger.warning(
                "Symbol not found", exchange=exchange_name, symbol=symbol_name
            )
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{symbol_name}' not found for exchange '{exchange_name}'",
            )

        # Get symbol statistics
        base_currency, quote_currency = parse_symbol_components(symbol_name)

        # Initialize info structure
        symbol_info = {
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "oldest_timestamp": None,
            "latest_timestamp": None,
            "total_trades": 0,
            "total_candles": 0,
        }

        # Try to get trade statistics
        try:
            trades_query = f"""
            SELECT
                MIN(timestamp) as oldest_timestamp,
                MAX(timestamp) as latest_timestamp,
                COUNT(*) as trade_count
            FROM "{exchange_name}"."{table_symbol}_trades"
            """

            trade_result = await connection.fetchrow(trades_query)
            if trade_result:
                symbol_info["oldest_timestamp"] = trade_result["oldest_timestamp"]
                symbol_info["latest_timestamp"] = trade_result["latest_timestamp"]
                symbol_info["total_trades"] = trade_result["trade_count"] or 0

        except Exception:
            logger.debug(
                "No trade data found", exchange=exchange_name, symbol=symbol_name
            )

        # Try to get candle statistics
        try:
            candles_query = f"""
            SELECT
                MIN(timestamp) as oldest_timestamp,
                MAX(timestamp) as latest_timestamp,
                COUNT(*) as candle_count
            FROM "{exchange_name}"."{table_symbol}_candles1m"
            """

            candle_result = await connection.fetchrow(candles_query)
            if candle_result:
                # Update timestamps if candle data is older/newer
                if not symbol_info["oldest_timestamp"] or (
                    candle_result["oldest_timestamp"]
                    and candle_result["oldest_timestamp"]
                    < symbol_info["oldest_timestamp"]
                ):
                    symbol_info["oldest_timestamp"] = candle_result["oldest_timestamp"]

                if not symbol_info["latest_timestamp"] or (
                    candle_result["latest_timestamp"]
                    and candle_result["latest_timestamp"]
                    > symbol_info["latest_timestamp"]
                ):
                    symbol_info["latest_timestamp"] = candle_result["latest_timestamp"]

                symbol_info["total_candles"] = candle_result["candle_count"] or 0

        except Exception:
            logger.debug(
                "No candle data found", exchange=exchange_name, symbol=symbol_name
            )

        logger.info(
            "Symbol information retrieved",
            exchange=exchange_name,
            symbol=symbol_name,
            total_trades=symbol_info["total_trades"],
            total_candles=symbol_info["total_candles"],
        )

        return {
            "success": True,
            "message": f"Symbol information for {symbol_name} on {exchange_name}",
            "timestamp": datetime.now(UTC),
            "exchange": exchange_name,
            "symbol": symbol_name,
            "info": symbol_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get symbol info",
            exchange=exchange_name,
            symbol=symbol_name,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Symbol info retrieval error: {str(e)}"
        ) from e


@router.get("/exchanges/{exchange}/symbols/{symbol:path}/metadata")
async def get_symbol_metadata(
    exchange: str = Path(..., description="Exchange name"),
    symbol: str = Path(..., description="Symbol name (e.g., BTC/USDT)"),
    connection=Depends(get_database_connection),
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

    try:
        logger.info(
            "Retrieving symbol metadata", exchange=exchange_name, symbol=symbol_name
        )

        # Check if exchange exists
        check_query = """
        SELECT EXISTS(
            SELECT 1 FROM information_schema.schemata
            WHERE schema_name = $1
        ) as exists
        """

        existence_result = await connection.fetchrow(check_query, exchange_name)

        if not existence_result["exists"]:
            logger.warning("Exchange not found for metadata", exchange=exchange_name)
            raise HTTPException(
                status_code=404, detail=f"Exchange '{exchange_name}' not found"
            )

        # Convert symbol to table name format
        table_symbol = symbol_name.lower().replace("/", "_")

        # Check symbol existence and get table count
        tables_query = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = $1
        AND table_type = 'BASE TABLE'
        AND (table_name LIKE $2 OR table_name LIKE $3)
        """

        table_results = await connection.fetch(
            tables_query,
            exchange_name,
            f"{table_symbol}_trades",
            f"{table_symbol}_candles%",
        )

        if not table_results:
            logger.warning(
                "Symbol not found for metadata",
                exchange=exchange_name,
                symbol=symbol_name,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Symbol '{symbol_name}' not found for exchange '{exchange_name}'",
            )

        # Initialize metadata
        metadata = {
            "table_count": len(table_results),
            "total_records": 0,
            "data_freshness": "unknown",
            "oldest_timestamp": None,
            "latest_timestamp": None,
            "tables": [row["table_name"] for row in table_results],
        }

        # Get aggregated statistics across all tables
        total_records = 0
        oldest_ts = None
        latest_ts = None

        for table_row in table_results:
            table_name = table_row["table_name"]

            try:
                stats_query = f"""
                SELECT
                    COUNT(*) as record_count,
                    MIN(timestamp) as min_timestamp,
                    MAX(timestamp) as max_timestamp
                FROM "{exchange_name}"."{table_name}"
                """

                stats_result = await connection.fetchrow(stats_query)

                if stats_result:
                    total_records += stats_result["record_count"] or 0

                    # Update overall timestamps
                    if stats_result["min_timestamp"]:
                        if not oldest_ts or stats_result["min_timestamp"] < oldest_ts:
                            oldest_ts = stats_result["min_timestamp"]

                    if stats_result["max_timestamp"]:
                        if not latest_ts or stats_result["max_timestamp"] > latest_ts:
                            latest_ts = stats_result["max_timestamp"]

            except Exception as table_error:
                logger.debug(
                    "Failed to get stats for table",
                    table=table_name,
                    error=str(table_error),
                )

        metadata["total_records"] = total_records
        metadata["oldest_timestamp"] = oldest_ts
        metadata["latest_timestamp"] = latest_ts

        # Determine data freshness
        if latest_ts:
            time_diff = datetime.now(UTC) - latest_ts.replace(tzinfo=UTC)
            if time_diff.days == 0:
                metadata["data_freshness"] = "excellent"
            elif time_diff.days <= 1:
                metadata["data_freshness"] = "good"
            elif time_diff.days <= 7:
                metadata["data_freshness"] = "moderate"
            else:
                metadata["data_freshness"] = "stale"

        # Calculate average daily records if we have enough data
        if oldest_ts and latest_ts and total_records > 0:
            time_span = (latest_ts - oldest_ts).days
            if time_span > 0:
                metadata["avg_daily_records"] = round(total_records / time_span, 2)
            else:
                metadata["avg_daily_records"] = total_records

        logger.info(
            "Symbol metadata retrieved",
            exchange=exchange_name,
            symbol=symbol_name,
            table_count=metadata["table_count"],
            total_records=total_records,
            freshness=metadata["data_freshness"],
        )

        return {
            "success": True,
            "message": f"Metadata for {symbol_name} on {exchange_name}",
            "timestamp": datetime.now(UTC),
            "exchange": exchange_name,
            "symbol": symbol_name,
            "metadata": metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get symbol metadata",
            exchange=exchange_name,
            symbol=symbol_name,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Symbol metadata error: {str(e)}"
        ) from e


@router.get("/symbols/search")
async def search_symbols(
    q: str = Query(..., description="Search query for symbol names"),
    exchange: Optional[str] = Query(None, description="Filter by specific exchange"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    connection=Depends(get_database_connection),
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

    try:
        logger.info(
            "Searching symbols",
            query=search_query,
            exchange_filter=exchange_filter,
            limit=limit,
        )

        # Get available exchanges (filtered if specified)
        if exchange_filter:
            # Check specific exchange exists
            check_query = """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = $1
            ) as exists
            """

            existence_result = await connection.fetchrow(check_query, exchange_filter)

            if not existence_result["exists"]:
                logger.warning("Exchange filter not found", exchange=exchange_filter)
                raise HTTPException(
                    status_code=404, detail=f"Exchange '{exchange_filter}' not found"
                )

            exchanges = [{"schema_name": exchange_filter}]
        else:
            # Get all exchanges
            exchanges_query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public', 'pg_toast')
            ORDER BY schema_name
            """

            exchanges = await connection.fetch(exchanges_query)

        # Search symbols across exchanges
        search_results = []

        for exchange_row in exchanges:
            exchange_name = exchange_row["schema_name"]

            try:
                # Get tables for this exchange
                tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1 AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """

                table_rows = await connection.fetch(tables_query, exchange_name)

                # Extract symbols and filter by search query
                exchange_symbols = {}

                for table_row in table_rows:
                    table_name = table_row["table_name"]
                    symbol = extract_symbol_from_table_name(table_name)

                    if symbol and search_query in symbol.upper():
                        if symbol not in exchange_symbols:
                            exchange_symbols[symbol] = []
                        exchange_symbols[symbol].append({"table_name": table_name})

                # Add matching symbols to results
                for symbol, tables in exchange_symbols.items():
                    base_currency, quote_currency = parse_symbol_components(symbol)
                    data_types = get_data_types_for_symbol(tables, symbol)

                    result = {
                        "symbol": symbol,
                        "exchange": exchange_name,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "data_types": data_types,
                    }

                    search_results.append(result)

            except Exception as exchange_error:
                logger.debug(
                    "Failed to search exchange",
                    exchange=exchange_name,
                    error=str(exchange_error),
                )

        # Sort results by relevance (exact matches first, then alphabetically)
        search_results.sort(
            key=lambda x: (
                not x["symbol"].startswith(search_query),  # Exact prefix matches first
                x["symbol"],  # Then alphabetically
                x["exchange"],  # Then by exchange
            )
        )

        # Apply limit
        limited_results = search_results[:limit]

        logger.info(
            "Symbol search completed",
            query=search_query,
            exchange_filter=exchange_filter,
            total_results=len(search_results),
            returned_results=len(limited_results),
        )

        return {
            "success": True,
            "message": f"Found {len(search_results)} symbols matching '{q}'",
            "timestamp": datetime.now(UTC),
            "query": q,
            "exchange_filter": exchange_filter,
            "results": limited_results,
            "count": len(limited_results),
            "total_matches": len(search_results),
            "truncated": len(search_results) > limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to search symbols",
            query=search_query,
            exchange_filter=exchange_filter,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Symbol search error: {str(e)}"
        ) from e
