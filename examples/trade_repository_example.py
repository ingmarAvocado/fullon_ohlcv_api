#!/usr/bin/env python3
"""
Trade Repository Example - fullon_ohlcv_api

Demonstrates trade data retrieval via API, mirroring fullon_ohlcv TradeRepository patterns.
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta
import aiohttp
from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:
    def install_uvloop():
        pass


async def main():
    """Trade repository API example."""
    load_dotenv()
    
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", "8000")
    base_url = f"http://{api_host}:{api_port}"
    
    print("💹 Trade Repository API Example")
    print(f"API URL: {base_url}")
    
    async with aiohttp.ClientSession() as session:
        exchange = "binance"
        symbol = "BTC/USDT"
        
        # Get recent trades
        try:
            url = f"{base_url}/api/trades/{exchange}/{symbol}"
            params = {"limit": 10}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    trades = data.get("trades", [])
                    print(f"✅ Retrieved {len(trades)} recent trades")
                    
                    for i, trade in enumerate(trades[:3]):
                        print(f"  Trade {i+1}: ${trade.get('price')} vol:{trade.get('volume')} {trade.get('side')}")
                else:
                    print(f"⚠️  API returned status {response.status}")
                    
        except Exception as e:
            print(f"⚠️  Failed to get trades: {e}")
        
        # Get trades in range
        try:
            url = f"{base_url}/api/trades/{exchange}/{symbol}/range"
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=1)
            
            params = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    trades = data.get("trades", [])
                    print(f"✅ Retrieved {len(trades)} trades in 1h range")
                else:
                    print(f"⚠️  Range query returned status {response.status}")
                    
        except Exception as e:
            print(f"⚠️  Failed to get trade range: {e}")


if __name__ == "__main__":
    install_uvloop()
    asyncio.run(main())