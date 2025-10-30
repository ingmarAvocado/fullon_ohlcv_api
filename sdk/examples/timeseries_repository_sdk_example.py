#!/usr/bin/env python3
"""
Timeseries Repository SDK Example - fullon_ohlcv_sdk

Demonstrates OHLCV aggregation using the Python SDK, returning fullon_ohlcv Candle objects
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
    """Timeseries repository SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("⏰ Timeseries Repository SDK Example")
    print(f"API URL: {base_url}")

    async with FullonOhlcvClient(base_url) as client:
        # Use exchange/symbol that matches demo data from fill_data_examples.py
        exchange = "kraken"
        symbol = "BTC/USDC"
        timeframe = "1h"

        # Generate OHLCV from trade data - returns List[Candle] objects!
        # Use a wider time range to capture demo data (which was filled in the past)
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(
                days=7
            )  # 7 days to ensure we capture demo data

            ohlcv_candles = await client.get_ohlcv_timeseries(
                exchange,
                symbol,
                timeframe,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
            )
            print(
                f"✅ Generated {len(ohlcv_candles)} {timeframe} OHLCV candles as Candle objects"
            )

            for i, candle in enumerate(ohlcv_candles[:3]):
                ohlc = (
                    f"O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}"
                )
                print(f"  OHLCV {i+1}: {ohlc} Vol:{candle.vol}")
                print(f"    Timestamp: {candle.timestamp}")
        except Exception as e:
            print(f"⚠️  Failed to get OHLCV aggregation: {e}")

        # Try different timeframes (using same wide time range)
        timeframes = ["5m", "15m", "1h"]
        end_time_tf = datetime.now(UTC)
        start_time_tf = end_time_tf - timedelta(days=7)  # Same 7-day range

        for tf in timeframes:
            try:
                ohlcv_tf = await client.get_ohlcv_timeseries(
                    exchange,
                    symbol,
                    tf,
                    start_time=start_time_tf.isoformat(),
                    end_time=end_time_tf.isoformat(),
                )
                print(f"✅ Generated {len(ohlcv_tf)} {tf} candles as Candle objects")

                # Demonstrate object properties for first timeframe
                if tf == "5m" and ohlcv_tf:
                    first_candle = ohlcv_tf[0]
                    print(
                        f"  Sample {tf} candle: O:{first_candle.open} H:{first_candle.high} L:{first_candle.low} C:{first_candle.close}"
                    )
            except Exception as e:
                print(f"⚠️  Failed to get {tf} aggregation: {e}")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
