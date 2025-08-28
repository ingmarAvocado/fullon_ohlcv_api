"""
Exchanges router for fullon_ohlcv_api.

This module provides READ-ONLY endpoints for discovering and validating
available exchanges through database schema introspection.

Endpoints:
- GET /exchanges - List all available exchanges
- GET /exchanges/{exchange}/info - Get detailed exchange information
- GET /exchanges/{exchange}/status - Get exchange status and health
- GET /exchanges/{exchange}/validate - Validate exchange existence
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from fullon_log import get_component_logger

from ..dependencies.database import get_database_connection

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
async def get_exchanges(
    connection=Depends(get_database_connection),
) -> Dict[str, Any]:
    """
    List all available exchanges via database schema introspection.

    Discovers exchanges by querying database schemas, excluding system schemas.
    Each exchange gets its own schema in the fullon_ohlcv database structure.

    Returns:
        ExchangesResponse: List of available exchanges with metadata

    Raises:
        HTTPException: 500 status code for database errors
    """
    try:
        logger.info("Discovering available exchanges via schema introspection")

        # Query for all non-system schemas
        query = """
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public', 'pg_toast')
        ORDER BY schema_name
        """

        schema_rows = await connection.fetch(query)

        exchanges = []
        for row in schema_rows:
            exchange_name = normalize_exchange_name(row["schema_name"])

            exchange_info = {
                "name": exchange_name,
                "display_name": format_exchange_display_name(exchange_name),
                "status": "active",  # Default status, can be enhanced with health checks
            }

            exchanges.append(exchange_info)

        logger.info(
            "Discovered exchanges via schema introspection", count=len(exchanges)
        )

        return {
            "success": True,
            "message": f"Found {len(exchanges)} available exchanges",
            "timestamp": datetime.now(UTC),
            "exchanges": exchanges,
            "count": len(exchanges),
            "total_available": len(exchanges),
        }

    except Exception as e:
        logger.error("Failed to discover exchanges", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Exchange discovery error: {str(e)}"
        ) from e


@router.get("/exchanges/{exchange}/info")
async def get_exchange_info(
    exchange: str = Path(..., description="Exchange name"),
    connection=Depends(get_database_connection),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific exchange.

    Retrieves exchange metadata including symbol count, data freshness,
    and other relevant statistics from the database.

    Args:
        exchange: Exchange name to get information for

    Returns:
        Exchange information with statistics and metadata

    Raises:
        HTTPException: 404 if exchange not found, 500 for database errors
    """
    exchange_name = normalize_exchange_name(exchange)

    try:
        logger.info("Retrieving exchange information", exchange=exchange_name)

        # Check if exchange schema exists
        check_query = """
        SELECT EXISTS(
            SELECT 1 FROM information_schema.schemata 
            WHERE schema_name = $1
        ) as exists
        """

        existence_result = await connection.fetchrow(check_query, exchange_name)

        if not existence_result["exists"]:
            logger.warning("Exchange not found", exchange=exchange_name)
            raise HTTPException(
                status_code=404, detail=f"Exchange '{exchange_name}' not found"
            )

        # Get symbol count (number of tables in the schema)
        symbol_count_query = """
        SELECT COUNT(*) as table_count
        FROM information_schema.tables 
        WHERE table_schema = $1 AND table_type = 'BASE TABLE'
        """

        symbol_result = await connection.fetchrow(symbol_count_query, exchange_name)
        symbol_count = symbol_result["table_count"] if symbol_result else 0

        # Get latest data timestamp (from any table in the schema)
        latest_data_query = f"""
        SELECT MAX(last_updated) as latest_timestamp
        FROM (
            SELECT MAX(timestamp) as last_updated
            FROM "{exchange_name}"."{exchange_name.upper()}_USDT_trades"
            UNION ALL
            SELECT MAX(timestamp) as last_updated  
            FROM "{exchange_name}"."{exchange_name.upper()}_BTC_trades"
        ) t
        """

        try:
            latest_result = await connection.fetchrow(latest_data_query)
            last_updated = (
                latest_result["latest_timestamp"]
                if latest_result
                else datetime.now(UTC)
            )
        except Exception:
            # If specific tables don't exist, use current time
            last_updated = datetime.now(UTC)

        exchange_info = {
            "name": exchange_name,
            "display_name": format_exchange_display_name(exchange_name),
            "status": "active" if symbol_count > 0 else "inactive",
            "symbol_count": symbol_count,
            "last_updated": last_updated,
        }

        logger.info(
            "Exchange information retrieved",
            exchange=exchange_name,
            symbol_count=symbol_count,
        )

        return {
            "success": True,
            "message": f"Exchange information for {exchange_name}",
            "timestamp": datetime.now(UTC),
            "exchange": exchange_name,
            "info": exchange_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get exchange info", exchange=exchange_name, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Exchange info retrieval error: {str(e)}"
        ) from e


@router.get("/exchanges/{exchange}/status")
async def get_exchange_status(
    exchange: str = Path(..., description="Exchange name"),
    connection=Depends(get_database_connection),
) -> Dict[str, Any]:
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

    try:
        logger.info("Checking exchange status", exchange=exchange_name)

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
                "Exchange not found for status check", exchange=exchange_name
            )
            raise HTTPException(
                status_code=404, detail=f"Exchange '{exchange_name}' not found"
            )

        # Initialize status info
        status_info = {
            "connection": "healthy",
            "data_freshness": "good",
            "last_trade_time": None,
            "last_candle_time": None,
            "total_trades": 0,
            "total_candles": 0,
        }

        try:
            # Get latest trade timestamp
            trade_query = f"""
            SELECT MAX(timestamp) as latest_trade
            FROM "{exchange_name}"."{exchange_name.upper()}_USDT_trades"
            """

            trade_result = await connection.fetchrow(trade_query)
            status_info["last_trade_time"] = (
                trade_result["latest_trade"] if trade_result else None
            )

        except Exception:
            logger.debug("No trade data found", exchange=exchange_name)

        try:
            # Get latest candle timestamp
            candle_query = f"""
            SELECT MAX(timestamp) as latest_candle
            FROM "{exchange_name}"."{exchange_name.upper()}_USDT_candles"
            """

            candle_result = await connection.fetchrow(candle_query)
            status_info["last_candle_time"] = (
                candle_result["latest_candle"] if candle_result else None
            )

        except Exception:
            logger.debug("No candle data found", exchange=exchange_name)

        try:
            # Get total trade count
            trade_count_query = f"""
            SELECT COUNT(*) as trade_count
            FROM "{exchange_name}"."{exchange_name.upper()}_USDT_trades"
            """

            trade_count_result = await connection.fetchrow(trade_count_query)
            status_info["total_trades"] = (
                trade_count_result["trade_count"] if trade_count_result else 0
            )

        except Exception:
            logger.debug("Could not get trade count", exchange=exchange_name)

        try:
            # Get total candle count
            candle_count_query = f"""
            SELECT COUNT(*) as candle_count
            FROM "{exchange_name}"."{exchange_name.upper()}_USDT_candles"
            """

            candle_count_result = await connection.fetchrow(candle_count_query)
            status_info["total_candles"] = (
                candle_count_result["candle_count"] if candle_count_result else 0
            )

        except Exception:
            logger.debug("Could not get candle count", exchange=exchange_name)

        # Determine overall health status
        if status_info["total_trades"] == 0 and status_info["total_candles"] == 0:
            status_info["connection"] = "degraded"
            status_info["data_freshness"] = "stale"

        logger.info(
            "Exchange status retrieved",
            exchange=exchange_name,
            connection=status_info["connection"],
            total_trades=status_info["total_trades"],
        )

        return {
            "success": True,
            "message": f"Status for exchange {exchange_name}",
            "timestamp": datetime.now(UTC),
            "exchange": exchange_name,
            "status": status_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get exchange status", exchange=exchange_name, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Exchange status check error: {str(e)}"
        ) from e


@router.get("/exchanges/{exchange}/validate")
async def validate_exchange(
    exchange: str = Path(..., description="Exchange name to validate"),
    connection=Depends(get_database_connection),
) -> Dict[str, Any]:
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

    try:
        logger.info("Validating exchange", exchange=exchange_name)

        # Check if exchange schema exists
        check_query = """
        SELECT EXISTS(
            SELECT 1 FROM information_schema.schemata 
            WHERE schema_name = $1
        ) as exists
        """

        existence_result = await connection.fetchrow(check_query, exchange_name)
        is_valid = existence_result["exists"] if existence_result else False

        message = (
            f"Exchange '{exchange_name}' is valid and available"
            if is_valid
            else f"Exchange '{exchange_name}' is invalid or not found"
        )

        logger.info(
            "Exchange validation completed", exchange=exchange_name, valid=is_valid
        )

        return {
            "success": True,
            "message": message,
            "timestamp": datetime.now(UTC),
            "exchange": exchange_name,
            "valid": is_valid,
        }

    except Exception as e:
        logger.error(
            "Failed to validate exchange", exchange=exchange_name, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Exchange validation error: {str(e)}"
        ) from e
