#!/usr/bin/env python3
"""
Trade Repository SDK Example - fullon_ohlcv_api

Demonstrates trade data retrieval via the future fullon_ohlcv_sdk client.
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
    """Trade repository SDK example."""
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("💹 Trade Repository SDK Example")
    print(f"API URL: {base_url}")

    exchange = "binance"
    symbol = "BTC/USDT"

    try:
        from fullon_ohlcv_sdk import FullonOhlcvClient  # type: ignore
    except Exception as e:  # pragma: no cover - SDK not yet implemented
        print(f"❌ SDK import failed: {e}")
        print("💡 Implement fullon_ohlcv_sdk to run this example")
        return

    async with FullonOhlcvClient(base_url) as client:  # type: ignore
        # Recent trades
        trades = await client.get_trades(exchange, symbol, limit=10)
        print(f"✅ Retrieved {len(trades)} recent trades")
        for i, trade in enumerate(trades[:3]):
            print(f"  Trade {i+1}: ${trade.price} vol:{trade.volume} {trade.side}")

        # Range query (last 1 hour)
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=1)
        trades_range = await client.get_trades_range(
            exchange, symbol, start_time=start_time, end_time=end_time
        )
        print(f"✅ Retrieved {len(trades_range)} trades in 1h range")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())
