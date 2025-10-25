#!/usr/bin/env python3
"""
Timeseries Repository Example - fullon_ohlcv_api

Demonstrates OHLCV aggregation via API, mirroring fullon_ohlcv TimeseriesRepository patterns.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta

import aiohttp
from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main():
    """Timeseries repository API example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("⏰ Timeseries Repository API Example")
    print(f"API URL: {base_url}")

    async with aiohttp.ClientSession() as session:
        # Use exchange/symbol that matches demo data from fill_data_examples.py
        exchange = "kraken"
        symbol = "BTC/USDC"
        timeframe = "1h"

        # Generate OHLCV from trade data
        # Use a wider time range to capture demo data (which was filled in the past)
        try:
            url = f"{base_url}/api/timeseries/{exchange}/{symbol}/ohlcv"
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(
                days=7
            )  # 7 days to ensure we capture demo data

            params = {
                "timeframe": timeframe,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "limit": 10,
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    ohlcv_data = data.get("ohlcv", [])
                    print(
                        f"✅ Generated {len(ohlcv_data)} {timeframe} OHLCV candles from trade data"
                    )

                    for i, ohlcv in enumerate(ohlcv_data[:3]):
                        ohlc = f"O:{ohlcv.get('open')} H:{ohlcv.get('high')} L:{ohlcv.get('low')} C:{ohlcv.get('close')}"
                        print(f"  OHLCV {i+1}: {ohlc} Vol:{ohlcv.get('vol')}")
                else:
                    print(f"⚠️  API returned status {response.status}")

        except Exception as e:
            print(f"⚠️  Failed to get OHLCV aggregation: {e}")

        # Try different timeframes (using same wide time range)
        timeframes = ["5m", "15m", "1h"]
        end_time_tf = datetime.now(UTC)
        start_time_tf = end_time_tf - timedelta(days=7)  # Same 7-day range

        for tf in timeframes:
            try:
                params = {
                    "timeframe": tf,
                    "start_time": start_time_tf.isoformat(),
                    "end_time": end_time_tf.isoformat(),
                    "limit": 5,
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        ohlcv_data = data.get("ohlcv", [])
                        print(f"✅ Generated {len(ohlcv_data)} {tf} candles")
                    else:
                        print(f"⚠️  {tf} aggregation returned status {response.status}")

            except Exception as e:
                print(f"⚠️  Failed to get {tf} aggregation: {e}")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
