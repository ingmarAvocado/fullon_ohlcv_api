"""WebSocket client for real-time OHLCV streaming."""

import asyncio
import json
from typing import AsyncGenerator, Optional, Dict, Any
from urllib.parse import urljoin

import websockets

from fullon_ohlcv.models import Candle
from .models import json_to_candle
from .exceptions import (
    FullonOhlcvError,
    APIConnectionError,
    ExchangeNotFoundError,
    SymbolNotFoundError,
    TimeframeError,
    DeserializationError,
)


class OhlcvWebSocketClient:
    """WebSocket client for streaming real-time OHLCV data.

    Provides an async generator that yields fullon_ohlcv Candle objects
    instead of raw JSON messages.
    """

    def __init__(self, base_url: str):
        """Initialize the WebSocket client.

        Args:
            base_url: Base URL of the fullon_ohlcv_api server
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.base_url = ws_url.rstrip("/")
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the WebSocket connection."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def stream_ohlcv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
    ) -> AsyncGenerator[Candle, None]:
        """Stream real-time OHLCV candles.

        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '1h')

        Yields:
            Candle: Real-time candle objects

        Raises:
            ExchangeNotFoundError: If exchange doesn't exist
            SymbolNotFoundError: If symbol doesn't exist
            TimeframeError: If timeframe is invalid
            APIConnectionError: If WebSocket connection fails
            DeserializationError: If message cannot be converted to Candle
        """
        # Validate timeframe
        if not timeframe or not isinstance(timeframe, str):
            raise TimeframeError(f"Invalid timeframe: {timeframe}")

        # Construct WebSocket URL
        ws_url = urljoin(self.base_url + "/", f"ws/ohlcv")

        # Subscription message
        subscription = {
            "action": "subscribe",
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
        }

        try:
            async with websockets.connect(ws_url) as websocket:
                self._websocket = websocket

                # Send subscription
                await websocket.send(json.dumps(subscription))

                # Listen for messages
                async for message in websocket:
                    try:
                        data = json.loads(message)

                        # Handle different message types
                        if data.get("type") == "candle":
                            candle_data = data.get("data", {})
                            candle = json_to_candle(candle_data)
                            yield candle
                        elif data.get("type") == "error":
                            error_msg = data.get("message", "Unknown error")
                            if "exchange" in error_msg.lower():
                                raise ExchangeNotFoundError(error_msg)
                            elif "symbol" in error_msg.lower():
                                raise SymbolNotFoundError(error_msg)
                            elif "timeframe" in error_msg.lower():
                                raise TimeframeError(error_msg)
                            else:
                                raise FullonOhlcvError(error_msg)
                        # Ignore other message types (like subscription confirmations)

                    except json.JSONDecodeError as e:
                        raise DeserializationError(f"Invalid JSON message: {e}") from e
                    except DeserializationError:
                        # Re-raise deserialization errors
                        raise
                    except Exception as e:
                        raise FullonOhlcvError(f"Error processing message: {e}") from e

        except websockets.exceptions.InvalidURI as e:
            raise APIConnectionError(f"Invalid WebSocket URL: {e}") from e
        except websockets.exceptions.ConnectionClosedError as e:
            raise APIConnectionError(f"WebSocket connection closed: {e}") from e
        except Exception as e:
            raise APIConnectionError(f"WebSocket connection failed: {e}") from e
        finally:
            self._websocket = None
