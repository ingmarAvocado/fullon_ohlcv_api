#!/usr/bin/env python3
"""
Candle Repository SDK Example - fullon_ohlcv_sdk

Demonstrates candle data retrieval using the Python SDK, returning fullon_ohlcv Candle objects
instead of raw JSON responses.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

from fullon_ohlcv_sdk import FullonOhlcvClient

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main():
    """Candle repository SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("🕯️  Candle Repository SDK Example")
    print(f"API URL: {base_url}")

    async with FullonOhlcvClient(base_url) as client:
        # Use exchange/symbol that matches demo data from fill_data_examples.py
        exchange = "kraken"
        symbol = "BTC/USDC"
        timeframe = "1h"  # Use timeframe that matches hourly candle data

        # Get recent candles - returns List[Candle] objects, not JSON!
        try:
            candles = await client.get_candles(exchange, symbol, timeframe, limit=10)
            print(
                f"✅ Retrieved {len(candles)} recent {timeframe} candles as Candle objects"
            )

            for i, candle in enumerate(candles[:3]):
                ohlc = (
                    f"O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}"
                )
                print(f"  Candle {i+1}: {ohlc} Vol:{candle.vol}")
                print(f"    Timestamp: {candle.timestamp}")
        except Exception as e:
            print(f"⚠️  Failed to get candles: {e}")

        # Get candles in range - returns List[Candle] objects!
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(days=1)

            candles_range = await client.get_candles(
                exchange,
                symbol,
                timeframe,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
            )
            print(
                f"✅ Retrieved {len(candles_range)} candles in 1d range as Candle objects"
            )

            # Demonstrate object properties
            if candles_range:
                first_candle = candles_range[0]
                print(
                    f"  First candle OHLC: {first_candle.open}/{first_candle.high}/{first_candle.low}/{first_candle.close}"
                )
                print(f"  Volume: {first_candle.vol}")
                print(f"  Timestamp: {first_candle.timestamp}")

        except Exception as e:
            print(f"⚠️  Failed to get candle range: {e}")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
