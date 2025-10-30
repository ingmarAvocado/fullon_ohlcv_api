#!/usr/bin/env python3
"""
WebSocket Live OHLCV SDK Example - fullon_ohlcv_sdk

Demonstrates real-time OHLCV streaming using the Python SDK, yielding fullon_ohlcv Candle objects
instead of raw JSON messages.
"""

import asyncio
import os

from dotenv import load_dotenv

from fullon_ohlcv_sdk import OhlcvWebSocketClient

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main():
    """WebSocket live OHLCV SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("📡 WebSocket Live OHLCV SDK Example")
    print(f"API URL: {base_url}")

    async with OhlcvWebSocketClient(base_url) as client:
        try:
            print("✅ WebSocket client initialized")

            # Stream live OHLCV - yields Candle objects, not JSON!
            update_count = 0
            async for candle in client.stream_ohlcv("binance", "BTC/USDT", "1m"):
                update_count += 1
                print(f"📈 Update {update_count}: ${candle.close} @ {candle.timestamp}")
                print(
                    f"   OHLC: O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}"
                )
                print(f"   Volume: {candle.vol}")

                # Limit for example
                if update_count >= 5:
                    break

        except Exception as e:
            print(f"⚠️  WebSocket streaming failed: {e}")
            print(
                "💡 This is expected if no WebSocket server is running or no live data"
            )


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
