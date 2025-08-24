#!/usr/bin/env python3
"""
Basic usage examples for fullon_ohlcv_api.

This demonstrates the core patterns for using the OHLCV FastAPI gateway
for market data operations.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


class FullonOhlcvAPIClient:
    """Simple client for interacting with fullon_ohlcv_api."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    async def get(self, endpoint: str, params: dict[str, Any] = None) -> dict[Any, Any]:
        """Make GET request."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}", params=params or {}, headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: dict[Any, Any]) -> dict[Any, Any]:
        """Make POST request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}", json=data, headers=self.headers
            )
            response.raise_for_status()
            return response.json()


async def main():
    """Demonstrate basic OHLCV API usage."""

    # Initialize client
    client = FullonOhlcvAPIClient()

    print("🚀 fullon_ohlcv_api Basic Usage Examples")
    print("=" * 50)

    try:
        # Health check (always available)
        health = await client.get("/health")
        print(f"✅ Health check: {health}")

        # Root endpoint (always available)
        root = await client.get("/")
        print(f"📋 Root info: {root}")

        print("\n📊 OHLCV READ-ONLY Market Data Examples:")
        print("Note: The following examples require the API to be fully implemented")
        print("      and connected to a fullon_ohlcv database with market data")
        print("      This API only supports READ operations - no write/insert/update")

        # Example 1: Get recent trade data
        print("\n1️⃣ Recent Trade Data Example:")
        print("   Endpoint: GET /api/trades/binance/BTC-USDT?limit=5")
        # trade_data = await client.get("/api/trades/binance/BTC-USDT", {"limit": 5})
        # print(f"   Recent trades: {trade_data}")
        print(
            "   [Implementation pending - will return recent BTC/USDT trades from Binance]"
        )

        # Example 2: Get historical trade data with time range
        print("\n2️⃣ Historical Trade Data Example:")
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=1)
        print(f"   Time range: {start_time.isoformat()} to {end_time.isoformat()}")
        print("   Endpoint: GET /api/trades/binance/BTC-USDT/range")
        # historical_trades = await client.get(
        #     "/api/trades/binance/BTC-USDT/range",
        #     {
        #         "start_time": start_time.isoformat(),
        #         "end_time": end_time.isoformat()
        #     }
        # )
        # print(f"   Historical trades: {historical_trades}")
        print("   [Implementation pending - will return BTC/USDT trades in time range]")

        # Example 3: Get OHLCV candle data
        print("\n3️⃣ OHLCV Candle Data Example:")
        print("   Endpoint: GET /api/candles/binance/ETH-USDT/1h?limit=24")
        # candle_data = await client.get("/api/candles/binance/ETH-USDT/1h", {"limit": 24})
        # print(f"   Hourly candles: {candle_data}")
        print("   [Implementation pending - will return 24 hourly ETH/USDT candles]")

        # Example 4: Get exchange information
        print("\n4️⃣ Exchange Information Example:")
        print("   Endpoint: GET /api/exchanges")
        # exchanges = await client.get("/api/exchanges")
        # print(f"   Available exchanges: {exchanges}")
        print("   [Implementation pending - will return list of available exchanges]")

        # Example 5: Get symbols for an exchange
        print("\n5️⃣ Exchange Symbols Example:")
        print("   Endpoint: GET /api/exchanges/binance/symbols")
        # symbols = await client.get("/api/exchanges/binance/symbols")
        # print(f"   Binance symbols: {symbols}")
        print("   [Implementation pending - will return all Binance trading pairs]")

        # Example 6: Trade Statistics and Analysis
        print("\n6️⃣ Trade Statistics and Analysis Example:")
        print("   Endpoint: GET /api/trades/binance/BTC-USDT/stats?hours=24")
        # stats = await client.get("/api/trades/binance/BTC-USDT/stats", {"hours": 24})
        # print(f"   Trade statistics: {stats}")
        print("   [Implementation pending - will return volume, price stats, etc.]")

        print("\n7️⃣ Data Export Example:")
        print("   Endpoint: GET /api/trades/binance/BTC-USDT/export?format=csv")
        # csv_data = await client.get("/api/trades/binance/BTC-USDT/export", {"format": "csv"})
        # print(f"   CSV export: {csv_data}")
        print("   [Implementation pending - will export trade data as CSV/JSON]")

        print("\n✨ READ-ONLY Time-Series Query Patterns:")
        print("   📈 Recent data: GET /api/trades/{exchange}/{symbol}?limit=N")
        print(
            "   ⏰ Time range: GET /api/trades/{exchange}/{symbol}/range?start_time=T1&end_time=T2"
        )
        print("   🕯️ Candles: GET /api/candles/{exchange}/{symbol}/{timeframe}?limit=N")
        print("   📊 Statistics: GET /api/trades/{exchange}/{symbol}/stats")
        print("   💾 Data export: GET /api/trades/{exchange}/{symbol}/export?format=csv")
        print("   🔍 Analysis: GET /api/candles/{exchange}/{symbol}/analysis")

        print("\n🔗 Interactive Documentation:")
        print("   📚 Swagger UI: http://localhost:8000/docs")
        print("   📖 ReDoc: http://localhost:8000/redoc")
        print("   ❤️ Health: http://localhost:8000/health")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 404:
            print("   Endpoint not implemented yet")
        elif e.response.status_code == 500:
            print("   Server error - check database connection")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n💡 Next Steps:")
    print("   1. Run 'make dev' to start the development server")
    print("   2. Visit http://localhost:8000/docs for interactive API testing")
    print("   3. Implement the router endpoints for full functionality")
    print("   4. Connect to your fullon_ohlcv database")


if __name__ == "__main__":
    asyncio.run(main())
