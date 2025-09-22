#!/usr/bin/env python3
"""
WebSocket Live OHLCV SDK Example - fullon_ohlcv_api

Demonstrates real-time OHLCV streaming via the future fullon_ohlcv_sdk client.
This is a goal-spec example: it shows intended SDK usage and outputs.
"""

import os
import asyncio
from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main() -> None:
    """WebSocket live OHLCV SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("📡 WebSocket Live OHLCV SDK Example")
    print(f"Base URL: {base_url}")

    exchange = "binance"
    symbol = "BTC/USDT"
    timeframe = "1m"

    try:
        from fullon_ohlcv_sdk import FullonOhlcvClient  # type: ignore
    except Exception as e:  # pragma: no cover - SDK not yet implemented
        print(f"❌ SDK import failed: {e}")
        print("💡 Implement fullon_ohlcv_sdk to run this example")
        return

    updates = 0
    async with FullonOhlcvClient(base_url) as client:  # type: ignore
        async for candle in client.stream_ohlcv(exchange, symbol, timeframe):
            updates += 1
            print(f"📈 Update {updates}: ${candle.close} @ {candle.timestamp}")
            print(f"   Volume: {candle.vol}")
            if updates >= 5:
                break


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())

