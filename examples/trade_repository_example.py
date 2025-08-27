#!/usr/bin/env python3
"""
Trade Repository Example - fullon_ohlcv_api

Demonstrates trade data retrieval via API, mirroring fullon_ohlcv TradeRepository patterns.
"""

import json
import os
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


def main():
    """Trade repository API example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", "8000")
    base_url = f"http://{api_host}:{api_port}"

    print("💹 Trade Repository API Example")
    print(f"API URL: {base_url}")

    exchange = "binance"
    symbol = "BTCUSDT"

    # Get recent trades
    try:
        params = urlencode({"limit": 10})
        url = f"{base_url}/api/trades/{exchange}/{symbol}?{params}"

        with urlopen(url, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                trades = data.get("trades", [])
                print(f"✅ Retrieved {len(trades)} recent trades")

                for i, trade in enumerate(trades[:3]):
                    print(
                        f"  Trade {i+1}: ${trade.get('price')} vol:{trade.get('volume')} {trade.get('side')}"
                    )
            else:
                print(f"⚠️  API returned status {response.getcode()}")

    except HTTPError as e:
        print(f"⚠️  HTTP Error: {e.code} {e.reason}")
    except Exception as e:
        print(f"⚠️  Failed to get trades: {e}")

    # Get trades in range
    try:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=1)

        params = urlencode(
            {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }
        )
        url = f"{base_url}/api/trades/{exchange}/{symbol}/range?{params}"

        with urlopen(url, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                trades = data.get("trades", [])
                print(f"✅ Retrieved {len(trades)} trades in 1h range")
            else:
                print(f"⚠️  Range query returned status {response.getcode()}")

    except HTTPError as e:
        print(f"⚠️  HTTP Error: {e.code} {e.reason}")
    except Exception as e:
        print(f"⚠️  Failed to get trade range: {e}")


if __name__ == "__main__":
    install_uvloop()
    main()
