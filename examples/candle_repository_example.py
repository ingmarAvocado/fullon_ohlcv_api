#!/usr/bin/env python3
"""
Candle Repository Example - fullon_ohlcv_api

Demonstrates candle data retrieval via API, mirroring fullon_ohlcv CandleRepository patterns.
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
    """Candle repository API example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("🕯️  Candle Repository API Example")
    print(f"API URL: {base_url}")

    async with aiohttp.ClientSession() as session:
        exchange = "binance"
        symbol = "BTC/USDT"
        timeframe = "1m"  # Use timeframe that matches populated data

        # Get recent candles
        try:
            url = f"{base_url}/api/candles/{exchange}/{symbol}/{timeframe}"
            params = {"limit": 10}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    candles = data.get("candles", [])
                    print(f"✅ Retrieved {len(candles)} recent {timeframe} candles")

                    for i, candle in enumerate(candles[:3]):
                        ohlc = f"O:{candle.get('open')} H:{candle.get('high')} L:{candle.get('low')} C:{candle.get('close')}"
                        print(f"  Candle {i+1}: {ohlc} Vol:{candle.get('vol')}")
                else:
                    print(f"⚠️  API returned status {response.status}")

        except Exception as e:
            print(f"⚠️  Failed to get candles: {e}")

        # Get candles in range
        try:
            url = f"{base_url}/api/candles/{exchange}/{symbol}/{timeframe}/range"
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(days=1)

            params = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    candles = data.get("candles", [])
                    print(f"✅ Retrieved {len(candles)} candles in 1d range")
                else:
                    print(f"⚠️  Range query returned status {response.status}")

        except Exception as e:
            print(f"⚠️  Failed to get candle range: {e}")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
