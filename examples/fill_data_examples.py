#!/usr/bin/env python3
"""
Fill Data Examples - fullon_ohlcv_api

Creates realistic test data using fullon_ohlcv methods directly.
Based on FULLON_OHLCV_METHOD_REFERENCE.md patterns.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from typing import List

from dotenv import load_dotenv

# Load environment variables before importing fullon_ohlcv
load_dotenv()

# fullon_ohlcv uses DB_* environment variables directly
print("🔍 Using fullon_ohlcv with DB environment variables for TEST database")

try:
    from fullon_ohlcv.models import Candle, Trade
    from fullon_ohlcv.repositories.ohlcv import CandleRepository, TradeRepository
    from fullon_ohlcv.utils import install_uvloop
except ImportError as e:
    print(f"❌ fullon_ohlcv not available: {e}")
    print("💡 Install with: poetry add git+ssh://git@github.com/ingmarAvocado/fullon_ohlcv.git")
    exit(1)

from fullon_log import get_component_logger

logger = get_component_logger("fullon.examples.fill_data")


class ExampleDataFiller:
    """
    Creates realistic market data for examples using fullon_ohlcv methods.
    
    Based on the Method Reference documentation patterns.
    """

    def __init__(self, test_mode: bool = True):
        self.test_mode = test_mode
        
        # fullon_ohlcv uses individual DB_* environment variables directly
        self.exchanges = ["binance"]
        self.symbols = ["BTC/USDT", "ETH/USDT"] 
        
        # Realistic price levels for different symbols
        self.base_prices = {
            "BTC/USDT": 50000.0,
            "ETH/USDT": 3000.0,
        }

    def generate_realistic_trades(self, symbol: str, count: int = 100) -> List[Trade]:
        """Generate realistic trade data with price movements."""
        trades = []
        base_price = self.base_prices.get(symbol, 1000.0)
        current_price = base_price
        base_time = datetime.now(UTC)
        
        logger.info(f"Generating {count} trades for {symbol} starting at ${base_price}")
        
        for i in range(count):
            # Create realistic price movements (random walk)
            price_change_pct = (i % 7 - 3) * 0.001  # Small price movements
            current_price *= (1 + price_change_pct)
            
            # Realistic volume based on trade type
            is_large_trade = i % 10 == 0
            volume = 5.0 + (i * 0.1) if is_large_trade else 0.1 + (i * 0.01)
            
            trade = Trade(
                timestamp=base_time - timedelta(minutes=i * 2),  # 2-minute intervals
                price=round(current_price, 2),
                volume=round(volume, 6),
                side="BUY" if i % 3 != 0 else "SELL",  # More buys than sells
                type="MARKET" if i % 4 != 0 else "LIMIT",  # Mostly market orders
            )
            trades.append(trade)
            
        logger.info(f"Generated {len(trades)} trades with prices from ${min(t.price for t in trades):.2f} to ${max(t.price for t in trades):.2f}")
        return trades

    def generate_realistic_candles(self, symbol: str, count: int = 50) -> List[Candle]:
        """Generate realistic OHLCV candle data."""
        candles = []
        base_price = self.base_prices.get(symbol, 1000.0)
        current_close = base_price
        base_time = datetime.now(UTC)
        
        logger.info(f"Generating {count} candles for {symbol} starting at ${base_price}")
        
        for i in range(count):
            # Realistic OHLCV with proper relationships
            open_price = current_close
            
            # Generate high/low with realistic spread
            volatility = base_price * 0.002  # 0.2% volatility
            high_price = open_price + (volatility * (1 + i % 3))
            low_price = open_price - (volatility * (1 + i % 2))
            
            # Close price trends slightly upward
            close_change = (i % 5 - 2) * volatility * 0.5
            close_price = open_price + close_change
            current_close = close_price
            
            # Realistic volume (higher during volatile periods)
            base_volume = 100.0 + (i * 2)
            volatility_multiplier = abs(close_price - open_price) / open_price * 1000
            volume = base_volume * (1 + volatility_multiplier)
            
            candle = Candle(
                timestamp=base_time - timedelta(hours=i),  # Hourly candles
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                vol=round(volume, 2),
            )
            candles.append(candle)
            
        logger.info(f"Generated {len(candles)} candles with volume from {min(c.vol for c in candles):.2f} to {max(c.vol for c in candles):.2f}")
        return candles

    async def fill_trade_data(self, exchange: str, symbol: str, count: int = 100) -> bool:
        """Fill trade data using TradeRepository methods."""
        logger.info(f"Filling trade data for {exchange}/{symbol}")
        
        try:
            trades = self.generate_realistic_trades(symbol, count)
            
            # Use the context manager pattern from Method Reference
            async with TradeRepository(exchange, symbol, test=self.test_mode) as repo:
                logger.info(f"Saving {len(trades)} trades to {exchange}.{symbol}")
                success = await repo.save_trades(trades)
                
                if success:
                    logger.info(f"✅ Successfully saved {len(trades)} trades for {symbol}")
                    
                    # Verify data was saved
                    recent_trades = await repo.get_recent_trades(limit=5)
                    oldest_ts = await repo.get_oldest_timestamp()
                    latest_ts = await repo.get_latest_timestamp()
                    
                    print(f"✅ Trade data for {symbol}:")
                    print(f"   📊 {len(trades)} trades saved")
                    print(f"   🕒 Time range: {oldest_ts} to {latest_ts}")
                    print(f"   💰 Sample prices: ${recent_trades[0].price:.2f} - ${recent_trades[-1].price:.2f}")
                    
                    return True
                else:
                    logger.error(f"❌ Failed to save trades for {symbol}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error filling trade data for {symbol}: {e}")
            return False

    async def fill_candle_data(self, exchange: str, symbol: str, count: int = 50) -> bool:
        """Fill candle data using CandleRepository methods."""
        logger.info(f"Filling candle data for {exchange}/{symbol}")
        
        try:
            candles = self.generate_realistic_candles(symbol, count)
            
            # Use the context manager pattern from Method Reference
            async with CandleRepository(exchange, symbol, test=self.test_mode) as repo:
                logger.info(f"Saving {len(candles)} candles to {exchange}.{symbol}")
                success = await repo.save_candles(candles)
                
                if success:
                    logger.info(f"✅ Successfully saved {len(candles)} candles for {symbol}")
                    
                    # Verify data was saved
                    oldest_ts = await repo.get_oldest_timestamp()
                    latest_ts = await repo.get_latest_timestamp()
                    
                    print(f"✅ Candle data for {symbol}:")
                    print(f"   📊 {len(candles)} candles saved")
                    print(f"   🕒 Time range: {oldest_ts} to {latest_ts}")
                    print(f"   📈 OHLC range: ${min(c.low for c in candles):.2f} - ${max(c.high for c in candles):.2f}")
                    
                    return True
                else:
                    logger.error(f"❌ Failed to save candles for {symbol}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error filling candle data for {symbol}: {e}")
            return False

    async def fill_all_data(self) -> bool:
        """Fill all test data for examples."""
        print("🗄️  Filling example database with realistic market data...")
        
        all_success = True
        
        for exchange in self.exchanges:
            for symbol in self.symbols:
                print(f"\n📈 Processing {exchange}/{symbol}...")
                
                # Fill both trades and candles
                trade_success = await self.fill_trade_data(exchange, symbol, count=150)
                candle_success = await self.fill_candle_data(exchange, symbol, count=72)  # 3 days of hourly candles
                
                if not (trade_success and candle_success):
                    all_success = False
                    
        if all_success:
            print("\n🎉 All example data filled successfully!")
            print("💡 The API examples will now demonstrate working functionality with real data")
        else:
            print("\n⚠️  Some data filling operations failed")
            print("💡 Examples may still work but with limited data")
            
        return all_success

    async def clear_all_data(self) -> bool:
        """Clear all test data after examples (no direct DB access)."""
        print("🧹 Skipping direct database cleanup (read-only policy)")
        print("💡 Test data resides in isolated schemas; manually clean if needed.")
        return True


async def main():
    """Main function for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fill example data for fullon_ohlcv_api")
    parser.add_argument("--clear", action="store_true", help="Clear data instead of filling")
    parser.add_argument("--prod", action="store_true", help="Use production database (default: test)")
    parser.add_argument(
        "--yes-really",
        action="store_true",
        help="Confirm writes against production when used with --prod",
    )
    args = parser.parse_args()
    
    # Safety guard: refuse prod writes without explicit confirmation
    if args.prod and not args.yes_really and os.getenv("ALLOW_EXAMPLES_PROD") != "1":
        print(
            "❌ Refusing to run in production mode without --yes-really or ALLOW_EXAMPLES_PROD=1"
        )
        return

    filler = ExampleDataFiller(test_mode=not args.prod)
    
    if args.clear:
        await filler.clear_all_data()
    else:
        await filler.fill_all_data()


if __name__ == "__main__":
    install_uvloop()  # Performance optimization from Method Reference
    asyncio.run(main())
