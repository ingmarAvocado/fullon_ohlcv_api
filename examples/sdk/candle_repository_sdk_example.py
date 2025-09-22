#!/usr/bin/env python3
"""
Candle Repository SDK Example - fullon_ohlcv_api

Demonstrates candle data retrieval via the future fullon_ohlcv_sdk client.
This is a goal-spec example: it shows intended SDK usage and outputs.
"""

import os
import asyncio
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main() -> None:
    """Candle repository SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("🕯️  Candle Repository SDK Example")
    print(f"API URL: {base_url}")

    exchange = "binance"
    symbol = "BTC/USDT"
    timeframe = "1m"

    try:
        from fullon_ohlcv_sdk import FullonOhlcvClient  # type: ignore
    except Exception as e:  # pragma: no cover - SDK not yet implemented
        print(f"❌ SDK import failed: {e}")
        print("💡 Implement fullon_ohlcv_sdk to run this example")
        return

    async with FullonOhlcvClient(base_url) as client:  # type: ignore
        # Recent candles
        candles = await client.get_candles(exchange, symbol, timeframe, limit=10)
        print(f"✅ Retrieved {len(candles)} recent {timeframe} candles")
        for i, c in enumerate(candles[:3]):
            print(f"  Candle {i+1}: O:{c.open} H:{c.high} L:{c.low} C:{c.close} Vol:{c.vol}")

        # Range (1 day)
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=1)
        candles_range = await client.get_candles_range(
            exchange, symbol, timeframe, start_time=start_time, end_time=end_time
        )
        print(f"✅ Retrieved {len(candles_range)} candles in 1d range")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())

