"""
WebSocket router for fullon_ohlcv_api.

This module implements real-time OHLCV streaming endpoints that follow the exact
specification defined by websocket_live_ohlcv_example.py.
"""

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from fullon_log import get_component_logger

logger = get_component_logger("fullon.api.ohlcv.websocket")

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections and subscriptions."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []
        self.subscriptions: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Connect a WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected", total_connections=len(self.active_connections)
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all subscriptions
        for subscription_key in list(self.subscriptions.keys()):
            if websocket in self.subscriptions[subscription_key]:
                self.subscriptions[subscription_key].remove(websocket)
                if not self.subscriptions[subscription_key]:
                    del self.subscriptions[subscription_key]

        logger.info(
            "WebSocket client disconnected",
            total_connections=len(self.active_connections),
        )

    def subscribe(self, websocket: WebSocket, subscription_key: str) -> None:
        """Subscribe a WebSocket client to updates."""
        if subscription_key not in self.subscriptions:
            self.subscriptions[subscription_key] = []

        if websocket not in self.subscriptions[subscription_key]:
            self.subscriptions[subscription_key].append(websocket)
            logger.info(
                "Client subscribed",
                subscription=subscription_key,
                clients=len(self.subscriptions[subscription_key]),
            )

    def unsubscribe(self, websocket: WebSocket, subscription_key: str) -> None:
        """Unsubscribe a WebSocket client from updates."""
        if (
            subscription_key in self.subscriptions
            and websocket in self.subscriptions[subscription_key]
        ):
            self.subscriptions[subscription_key].remove(websocket)
            if not self.subscriptions[subscription_key]:
                del self.subscriptions[subscription_key]
            logger.info("Client unsubscribed", subscription=subscription_key)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send message to a specific WebSocket client."""
        # Check if WebSocket is still connected before sending
        if websocket.client_state != WebSocketState.CONNECTED:
            logger.debug("Cannot send message - WebSocket not in CONNECTED state",
                        state=websocket.client_state)
            return

        try:
            await websocket.send_text(message)
        except (RuntimeError, WebSocketDisconnect) as e:
            # WebSocket already closed, just log at debug level
            logger.debug("Cannot send message - WebSocket disconnected", error=str(e))
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))

    async def broadcast_to_subscription(
        self, message: str, subscription_key: str
    ) -> None:
        """Broadcast message to all clients subscribed to a specific key."""
        if subscription_key not in self.subscriptions:
            return

        disconnected_clients = []
        for websocket in self.subscriptions[subscription_key]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning("Failed to send message to client", error=str(e))
                disconnected_clients.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ohlcv")
async def websocket_ohlcv_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time OHLCV streaming.

    This endpoint matches the specification from websocket_live_ohlcv_example.py:
    - WebSocket URL: ws://host:port/ws/ohlcv
    - Subscription message format:
      {
        "action": "subscribe",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1m",
        "type": "ohlcv_live"
      }
    - Update message format:
      {
        "type": "ohlcv_update",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1m",
        "data": {...}
      }
    """
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                await manager.send_personal_message(
                    json.dumps(error_response), websocket
                )
            except Exception as e:
                logger.error("Error handling WebSocket message", error=str(e))
                error_response = {
                    "type": "error",
                    "message": f"Message handling error: {str(e)}",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                await manager.send_personal_message(
                    json.dumps(error_response), websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected normally")
    except RuntimeError as e:
        # Handle "WebSocket is not connected" errors during cleanup
        if "not connected" in str(e).lower():
            manager.disconnect(websocket)
            logger.debug("WebSocket cleanup after disconnect", error=str(e))
        else:
            raise
    except Exception as e:
        logger.error("Unexpected WebSocket error", error=str(e))
        manager.disconnect(websocket)


async def handle_websocket_message(
    websocket: WebSocket, message: dict[str, Any]
) -> None:
    """Handle incoming WebSocket message."""
    action = message.get("action")

    if action == "subscribe":
        await handle_subscribe(websocket, message)
    elif action == "unsubscribe":
        await handle_unsubscribe(websocket, message)
    else:
        error_response = {
            "type": "error",
            "message": f"Unknown action: {action}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)


async def handle_subscribe(websocket: WebSocket, message: dict[str, Any]) -> None:
    """Handle subscription request."""
    try:
        exchange = message.get("exchange")
        symbol = message.get("symbol")
        timeframe = message.get("timeframe")
        message_type = message.get("type")

        if not all([exchange, symbol, timeframe, message_type]):
            error_response = {
                "type": "error",
                "message": "Missing required fields: exchange, symbol, timeframe, type",
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await manager.send_personal_message(json.dumps(error_response), websocket)
            return

        # Type assertions for mypy - we know these are strings after validation
        assert isinstance(exchange, str)
        assert isinstance(symbol, str)
        assert isinstance(timeframe, str)
        assert isinstance(message_type, str)

        # Create subscription key
        subscription_key = f"{exchange}:{symbol}:{timeframe}:{message_type}"
        manager.subscribe(websocket, subscription_key)

        # Send confirmation
        confirmation = {
            "type": "subscription_confirmed",
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "subscription_type": message_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"status": "subscribed"},
        }
        await manager.send_personal_message(json.dumps(confirmation), websocket)

        logger.info(
            "WebSocket subscription created",
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            type=message_type,
        )

        # For demo purposes, send a sample OHLCV update
        # In a real implementation, this would connect to live data feeds
        await send_sample_ohlcv_update(subscription_key, exchange, symbol, timeframe)

    except Exception as e:
        logger.error("Error handling subscribe", error=str(e))
        error_response = {
            "type": "error",
            "message": f"Subscription error: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)


async def handle_unsubscribe(websocket: WebSocket, message: dict[str, Any]) -> None:
    """Handle unsubscription request."""
    try:
        exchange = message.get("exchange")
        symbol = message.get("symbol")
        timeframe = message.get("timeframe")
        message_type = message.get("type")

        if not all([exchange, symbol, timeframe, message_type]):
            error_response = {
                "type": "error",
                "message": "Missing required fields: exchange, symbol, timeframe, type",
                "timestamp": datetime.now(UTC).isoformat(),
            }
            await manager.send_personal_message(json.dumps(error_response), websocket)
            return

        # Create subscription key
        subscription_key = f"{exchange}:{symbol}:{timeframe}:{message_type}"
        manager.unsubscribe(websocket, subscription_key)

        # Send confirmation
        confirmation = {
            "type": "unsubscription_confirmed",
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "subscription_type": message_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"status": "unsubscribed"},
        }
        await manager.send_personal_message(json.dumps(confirmation), websocket)

        logger.info(
            "WebSocket unsubscription processed",
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            type=message_type,
        )

    except Exception as e:
        logger.error("Error handling unsubscribe", error=str(e))
        error_response = {
            "type": "error",
            "message": f"Unsubscription error: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)


async def send_sample_ohlcv_update(
    subscription_key: str, exchange: str, symbol: str, timeframe: str
) -> None:
    """Send a sample OHLCV update for demonstration purposes."""
    # In a real implementation, this would be triggered by actual market data
    sample_update = {
        "type": "ohlcv_update",
        "exchange": exchange,
        "symbol": symbol,
        "timeframe": timeframe,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {
            "timestamp": datetime.now(UTC).isoformat(),
            "open": 50000.0,
            "high": 50100.0,
            "low": 49950.0,
            "close": 50050.0,
            "volume": 1.5,
            "is_final": False,  # Whether this is the final value for this timeframe
        },
    }

    await manager.broadcast_to_subscription(json.dumps(sample_update), subscription_key)
    logger.debug("Sample OHLCV update sent", subscription=subscription_key)


# Additional utility functions for real-time data integration
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
