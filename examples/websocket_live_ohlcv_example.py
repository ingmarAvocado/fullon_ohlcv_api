#!/usr/bin/env python3
"""
WebSocket Live OHLCV Example - fullon_ohlcv_api

Demonstrates real-time OHLCV streaming via WebSocket connection.
"""

import asyncio
import json
import os

import websockets
from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main():
    """WebSocket live OHLCV example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", "8000")
    ws_url = f"ws://{api_host}:{api_port}/ws/ohlcv"

    print("📡 WebSocket Live OHLCV Example")
    print(f"WebSocket URL: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected")

            # Subscribe to live OHLCV
            subscribe_msg = {
                "action": "subscribe",
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "timeframe": "1m",
                "type": "ohlcv_live",
            }

            await websocket.send(json.dumps(subscribe_msg))
            print("📊 Subscribed to live BTC/USDT 1m bars")

            # Listen for updates
            update_count = 0
            while update_count < 5:  # Limit for example
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)

                    if data.get("type") == "ohlcv_update":
                        update_count += 1
                        ohlcv = data.get("data", {})

                        timestamp = ohlcv.get("timestamp", "N/A")
                        close = ohlcv.get("close", "N/A")
                        volume = ohlcv.get("volume", "N/A")
                        is_final = ohlcv.get("is_final", False)

                        print(f"📈 Update {update_count}: ${close} @ {timestamp}")
                        print(
                            f"   Volume: {volume} | Final: {'Yes' if is_final else 'No'}"
                        )

                except asyncio.TimeoutError:
                    print("⏰ No updates received (timeout)")
                    break
                except Exception as e:
                    print(f"⚠️  Error receiving update: {e}")
                    break

            # Unsubscribe
            unsubscribe_msg = {
                "action": "unsubscribe",
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "timeframe": "1m",
                "type": "ohlcv_live",
            }

            await websocket.send(json.dumps(unsubscribe_msg))
            print("✅ Unsubscribed from live OHLCV")

    except Exception as e:
        print(f"⚠️  WebSocket connection failed: {e}")
        print("💡 This is expected if no WebSocket server is running")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
