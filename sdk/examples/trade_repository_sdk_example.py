#!/usr/bin/env python3
"""
Trade Repository SDK Example - fullon_ohlcv_sdk

Demonstrates trade data retrieval using the Python SDK, returning fullon_ohlcv Trade objects
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
    """Trade repository SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("💹 Trade Repository SDK Example")
    print(f"API URL: {base_url}")

    # Use exchange/symbol that matches demo data from fill_data_examples.py
    exchange = "kraken"
    symbol = "BTC/USDC"

    async with FullonOhlcvClient(base_url) as client:
        # Get recent trades - returns List[Trade] objects, not JSON!
        try:
            trades = await client.get_trades(exchange, symbol, limit=10)
            print(f"✅ Retrieved {len(trades)} recent trades as Trade objects")

            for i, trade in enumerate(trades[:3]):
                print(f"  Trade {i+1}: ${trade.price} vol:{trade.volume} {trade.side}")
                print(f"    Timestamp: {trade.timestamp}")
                print(f"    Type: {trade.type}")
        except Exception as e:
            print(f"⚠️  Failed to get trades: {e}")

        # Get trades in range - returns List[Trade] objects!
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=1)

            trades_range = await client.get_trades(
                exchange,
                symbol,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
            )
            print(
                f"✅ Retrieved {len(trades_range)} trades in 1h range as Trade objects"
            )

            # Demonstrate object properties
            if trades_range:
                first_trade = trades_range[0]
                print(f"  First trade: {first_trade.price} @ {first_trade.timestamp}")
                print(f"  Is buy order: {first_trade.side == 'BUY'}")
                print(f"  Volume: {first_trade.volume}")

        except Exception as e:
            print(f"⚠️  Failed to get trade range: {e}")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
