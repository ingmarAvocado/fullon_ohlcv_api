#!/usr/bin/env python3
"""
Timeseries Repository SDK Example - fullon_ohlcv_api

Demonstrates OHLCV aggregation via the future fullon_ohlcv_sdk client.
This is a goal-spec example: it shows intended SDK usage and outputs.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main() -> None:
    """Timeseries repository SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("⏰ Timeseries Repository SDK Example")
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

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)

    async with FullonOhlcvClient(base_url) as client:  # type: ignore
        ohlcv = await client.get_ohlcv_timeseries(
            exchange,
            symbol,
            timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=10,
        )
        print(f"✅ Generated {len(ohlcv)} {timeframe} OHLCV candles from trade data")
        for i, c in enumerate(ohlcv[:3]):
            print(
                f"  OHLCV {i+1}: O:{c.open} H:{c.high} L:{c.low} C:{c.close} Vol:{c.vol}"
            )


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
