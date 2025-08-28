"""
Test factories for generating API test data.

This module provides factory functions for creating test data objects
for fullon_ohlcv_api tests with sensible defaults that can be easily overridden.
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List
import factory
from factory import fuzzy

from fullon_ohlcv.models import Trade, Candle


class TradeFactory(factory.Factory):
    """Factory for creating Trade test instances for API testing."""
    
    class Meta:
        model = Trade
    
    timestamp = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    price = factory.LazyFunction(lambda: round(random.uniform(30000, 50000), 2))
    volume = factory.LazyFunction(lambda: round(random.uniform(0.01, 10.0), 8))
    side = fuzzy.FuzzyChoice(['buy', 'sell'])
    type = fuzzy.FuzzyChoice(['market', 'limit'])
    ord = factory.LazyFunction(lambda: f"order_{random.randint(1000, 9999)}" if random.random() > 0.5 else None)


class CandleFactory(factory.Factory):
    """Factory for creating Candle test instances for API testing."""
    
    class Meta:
        model = Candle
    
    timestamp = factory.LazyFunction(
        lambda: datetime.now(timezone.utc).replace(second=0, microsecond=0)
    )
    open = factory.LazyFunction(lambda: round(random.uniform(30000, 50000), 2))
    high = factory.LazyAttribute(lambda obj: obj.open + random.uniform(0, 1000))
    low = factory.LazyAttribute(lambda obj: obj.open - random.uniform(0, 1000))
    close = factory.LazyAttribute(
        lambda obj: obj.low + random.uniform(0, obj.high - obj.low)
    )
    vol = factory.LazyFunction(lambda: round(random.uniform(100, 10000), 4))


def create_api_trade_list(
    count: int = 10,
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    base_time: Optional[datetime] = None,
    time_interval: timedelta = timedelta(seconds=1),
    **kwargs
) -> List[Trade]:
    """
    Create a list of trades with incrementing timestamps for API testing.
    
    Args:
        count: Number of trades to create
        exchange: Exchange name for testing
        symbol: Trading pair symbol for testing
        base_time: Starting timestamp (defaults to now - count seconds)
        time_interval: Time between trades
        **kwargs: Override any trade attributes
    
    Returns:
        List of Trade objects
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc) - timedelta(seconds=count)
    
    trades = []
    for i in range(count):
        timestamp = base_time + (time_interval * i)
        trade = TradeFactory(timestamp=timestamp, **kwargs)
        trades.append(trade)
    
    return trades


def create_api_candle_list(
    count: int = 24,
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    base_time: Optional[datetime] = None,
    timeframe: str = "1h",
    **kwargs
) -> List[Candle]:
    """
    Create a list of candles with proper time spacing for API testing.
    
    Args:
        count: Number of candles to create
        exchange: Exchange name for testing
        symbol: Trading pair symbol for testing
        base_time: Starting timestamp (defaults to now)
        timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        **kwargs: Override any candle attributes
    
    Returns:
        List of Candle objects
    """
    # Map timeframe to timedelta
    timeframe_map = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }
    
    interval = timeframe_map.get(timeframe, timedelta(hours=1))
    
    if base_time is None:
        base_time = datetime.now(timezone.utc) - (interval * count)
        # Align to timeframe boundary
        if timeframe == "1h":
            base_time = base_time.replace(minute=0, second=0, microsecond=0)
        elif timeframe == "1d":
            base_time = base_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    candles = []
    for i in range(count):
        timestamp = base_time + (interval * i)
        candle = CandleFactory(timestamp=timestamp, **kwargs)
        candles.append(candle)
    
    return candles


def create_realistic_api_trades(
    count: int = 100,
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    start_time: Optional[datetime] = None,
    price_volatility: float = 0.001,
    volume_range: tuple = (0.01, 2.0)
) -> List[Trade]:
    """
    Create realistic trade data for API endpoint testing.
    
    Args:
        count: Number of trades
        exchange: Exchange name
        symbol: Trading symbol
        start_time: Starting timestamp
        price_volatility: Price movement volatility
        volume_range: Min/max volume range
    
    Returns:
        List of realistic Trade objects
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    # Generate price series
    prices = create_price_series(
        start_price=45000.0,
        count=count,
        volatility=price_volatility
    )
    
    trades = []
    for i in range(count):
        # Random time intervals (0.1 to 10 seconds)
        time_delta = timedelta(seconds=random.uniform(0.1, 10))
        timestamp = start_time + time_delta * i
        
        # Determine side based on price movement
        if i > 0 and prices[i] > prices[i-1]:
            side = "buy" if random.random() > 0.3 else "sell"
        else:
            side = "sell" if random.random() > 0.3 else "buy"
        
        trade = TradeFactory(
            timestamp=timestamp,
            price=prices[i],
            volume=random.uniform(*volume_range),
            side=side,
            type="market" if random.random() > 0.2 else "limit"
        )
        trades.append(trade)
    
    return trades


def create_realistic_api_candles(
    count: int = 24,
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    start_time: Optional[datetime] = None,
    base_price: float = 45000.0,
    volatility: float = 0.02
) -> List[Candle]:
    """
    Create realistic OHLCV candles for API endpoint testing.
    
    Args:
        count: Number of candles
        exchange: Exchange name
        symbol: Trading symbol
        timeframe: Candle timeframe
        start_time: Starting timestamp
        base_price: Starting price
        volatility: Price volatility
    
    Returns:
        List of realistic Candle objects
    """
    candles = []
    current_price = base_price
    
    # Get time interval
    timeframe_map = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }
    interval = timeframe_map.get(timeframe, timedelta(hours=1))
    
    if start_time is None:
        start_time = datetime.now(timezone.utc) - (interval * count)
        if timeframe in ["1h", "4h"]:
            start_time = start_time.replace(minute=0, second=0, microsecond=0)
        elif timeframe == "1d":
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    for i in range(count):
        timestamp = start_time + (interval * i)
        
        # Generate OHLC with realistic relationships
        open_price = current_price
        
        # Generate high and low
        max_move = current_price * volatility
        high = open_price + random.uniform(0, max_move)
        low = open_price - random.uniform(0, max_move)
        
        # Close should be between high and low
        close = random.uniform(low, high)
        
        # Volume with some correlation to price movement
        price_change = abs(close - open_price) / open_price
        base_volume = 1000.0
        volume = base_volume * (1 + price_change * 10) * random.uniform(0.5, 1.5)
        
        candle = Candle(
            timestamp=timestamp,
            open=round(open_price, 2),
            high=round(high, 2),
            low=round(low, 2),
            close=round(close, 2),
            vol=round(volume, 4)
        )
        candles.append(candle)
        
        # Next candle opens at previous close
        current_price = close
    
    return candles


def create_price_series(
    start_price: float = 45000.0,
    count: int = 100,
    volatility: float = 0.01,
    trend: float = 0.0
) -> List[float]:
    """
    Create a realistic price series with random walk for API testing.
    
    Args:
        start_price: Initial price
        count: Number of prices to generate
        volatility: Price volatility (0.01 = 1%)
        trend: Trend bias (-1 to 1)
    
    Returns:
        List of prices
    """
    prices = [start_price]
    
    for _ in range(count - 1):
        change = random.gauss(trend * volatility, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.01))  # Ensure positive
    
    return prices


def create_volume_series(
    base_volume: float = 100.0,
    count: int = 100,
    volatility: float = 0.5
) -> List[float]:
    """
    Create realistic volume series for API testing.
    
    Args:
        base_volume: Average volume
        count: Number of volumes to generate
        volatility: Volume volatility
    
    Returns:
        List of volumes
    """
    return [
        max(random.gauss(base_volume, base_volume * volatility), 0.01)
        for _ in range(count)
    ]


# API-specific test data helpers
def create_trades_for_range_testing(
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    hours_back: int = 2,
    trades_per_hour: int = 50
) -> List[Trade]:
    """
    Create trades specifically for testing time range queries in API endpoints.
    
    Args:
        exchange: Exchange name
        symbol: Trading symbol
        hours_back: How many hours back to create data for
        trades_per_hour: Number of trades per hour
    
    Returns:
        List of trades distributed over time range
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours_back)
    
    total_trades = hours_back * trades_per_hour
    time_per_trade = timedelta(hours=hours_back) / total_trades
    
    trades = []
    for i in range(total_trades):
        timestamp = start_time + (time_per_trade * i)
        trade = TradeFactory(timestamp=timestamp)
        trades.append(trade)
    
    return trades


def create_candles_for_timeframe_testing(
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    timeframes: List[str] = None,
    count_per_timeframe: int = 10
) -> dict:
    """
    Create candle data for testing multiple timeframes in API endpoints.
    
    Args:
        exchange: Exchange name
        symbol: Trading symbol
        timeframes: List of timeframes to create data for
        count_per_timeframe: Number of candles per timeframe
    
    Returns:
        Dictionary mapping timeframe to list of candles
    """
    if timeframes is None:
        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    candles_by_timeframe = {}
    
    for timeframe in timeframes:
        candles = create_api_candle_list(
            count=count_per_timeframe,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe
        )
        candles_by_timeframe[timeframe] = candles
    
    return candles_by_timeframe


def create_test_data_for_aggregation(
    exchange: str = "binance",
    symbol: str = "BTC/USDT",
    trade_count: int = 1000,
    time_span_hours: int = 1
) -> List[Trade]:
    """
    Create trade data specifically for testing OHLCV aggregation endpoints.
    
    Creates high-frequency trade data that can be aggregated into OHLCV candles.
    
    Args:
        exchange: Exchange name
        symbol: Trading symbol
        trade_count: Number of trades to create
        time_span_hours: Time span to distribute trades over
    
    Returns:
        List of trades suitable for aggregation testing
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=time_span_hours)
    
    # Create trades with realistic price movements
    trades = create_realistic_api_trades(
        count=trade_count,
        exchange=exchange,
        symbol=symbol,
        start_time=start_time,
        price_volatility=0.0001,  # Small movements for aggregation
        volume_range=(0.001, 0.1)  # Smaller volumes
    )
    
    # Ensure trades are sorted by timestamp
    trades.sort(key=lambda t: t.timestamp)
    
    return trades