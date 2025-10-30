"""JSON to fullon_ohlcv object conversion utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from fullon_ohlcv.models import Trade, Candle
from .exceptions import DeserializationError


def json_to_trade(json_data: Dict[str, Any]) -> Trade:
    """Convert API JSON response to fullon_ohlcv Trade object.

    Args:
        json_data: JSON response from the API

    Returns:
        Trade: A fullon_ohlcv Trade object

    Raises:
        DeserializationError: If the JSON cannot be converted
    """
    try:
        timestamp_str = json_data.get("timestamp")
        if not timestamp_str:
            raise DeserializationError("Missing timestamp in trade data")

        # Parse timestamp and ensure UTC
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        price = float(json_data.get("price", 0))
        volume = float(json_data.get("volume", 0))
        side = json_data.get("side", "").upper()
        trade_type = json_data.get("type", "MARKET").upper()

        if price <= 0:
            raise DeserializationError(f"Invalid price: {price}")
        if volume <= 0:
            raise DeserializationError(f"Invalid volume: {volume}")
        if side not in ("BUY", "SELL"):
            raise DeserializationError(f"Invalid side: {side}")

        return Trade(
            timestamp=timestamp,
            price=price,
            volume=volume,
            side=side,
            type=trade_type,
        )
    except (ValueError, TypeError, KeyError) as e:
        raise DeserializationError(f"Failed to deserialize trade: {e}") from e


def json_to_candle(json_data: Dict[str, Any]) -> Candle:
    """Convert API JSON response to fullon_ohlcv Candle object.

    Args:
        json_data: JSON response from the API

    Returns:
        Candle: A fullon_ohlcv Candle object

    Raises:
        DeserializationError: If the JSON cannot be converted
    """
    try:
        timestamp_str = json_data.get("timestamp")
        if not timestamp_str:
            raise DeserializationError("Missing timestamp in candle data")

        # Parse timestamp and ensure UTC
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        open_price = float(json_data.get("open", 0))
        high = float(json_data.get("high", 0))
        low = float(json_data.get("low", 0))
        close = float(json_data.get("close", 0))
        volume = float(json_data.get("volume", 0))

        # Basic validation
        if any(price <= 0 for price in [open_price, high, low, close]):
            raise DeserializationError("Invalid OHLC prices in candle data")
        if volume < 0:
            raise DeserializationError(f"Invalid volume: {volume}")

        return Candle(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close,
            vol=volume,
        )
    except (ValueError, TypeError, KeyError) as e:
        raise DeserializationError(f"Failed to deserialize candle: {e}") from e


def json_list_to_trades(json_list: List[Dict[str, Any]]) -> List[Trade]:
    """Convert list of JSON trade data to list of Trade objects.

    Args:
        json_list: List of JSON trade responses

    Returns:
        List[Trade]: List of Trade objects
    """
    return [json_to_trade(item) for item in json_list]


def json_list_to_candles(json_list: List[Dict[str, Any]]) -> List[Candle]:
    """Convert list of JSON candle data to list of Candle objects.

    Args:
        json_list: List of JSON candle responses

    Returns:
        List[Candle]: List of Candle objects
    """
    return [json_to_candle(item) for item in json_list]
