# fullon_ohlcv API Reference for REST Gateway Implementation

## Overview

Based on exploration of the fullon_ohlcv library, this document provides the complete API reference needed to implement the REST gateway endpoints.

## Key Classes and Repository Patterns

### Data Models

#### OHLCVTrade
```python
from fullon_ohlcv import OHLCVTrade

trade = OHLCVTrade(
    timestamp=datetime.now(timezone.utc),  # UTC timezone required
    price=45000.50,                        # Trade price
    volume=0.5,                           # Volume in base currency
    side="buy",                           # "buy" or "sell"
    type="market"                         # "market" or "limit"
)
```

#### OHLCVCandle
```python
from fullon_ohlcv import OHLCVCandle

candle = OHLCVCandle(
    timestamp=datetime.now(timezone.utc),  # Candle start time (UTC)
    open=45000.0,                         # Opening price
    high=45500.0,                         # Highest price
    low=44800.0,                          # Lowest price
    close=45200.0,                        # Closing price
    vol=1234.56                           # Total volume
)
```

### Repository Classes

#### TradeRepository (READ-ONLY Operations)
```python
from fullon_ohlcv import TradeRepository

# Context manager pattern (recommended)
async with TradeRepository("binance", "BTC/USDT") as repo:
    # Recent trades
    trades = await repo.get_recent_trades(limit=100, offset=0)
    
    # Trades in time range
    trades = await repo.get_trades_in_range(
        start_time=start_datetime,
        end_time=end_datetime,
        limit=1000  # Optional
    )
    
    # Latest timestamp
    latest = await repo.get_latest_timestamp()
    
    # Oldest timestamp  
    oldest = await repo.get_oldest_timestamp()
```

**Key READ-ONLY Methods:**
- `get_recent_trades(limit: int = 100, offset: int = 0) -> List[Trade]`
- `get_trades_in_range(start_time: datetime, end_time: datetime, limit: Optional[int] = None) -> List[Trade]`
- `get_latest_timestamp(table_name: Optional[str] = None) -> Optional[datetime]`
- `get_oldest_timestamp(table_name: Optional[str] = None) -> Optional[datetime]`

#### CandleRepository (READ-ONLY Operations)
```python
from fullon_ohlcv import CandleRepository

async with CandleRepository("binance", "BTC/USDT") as repo:
    # Fetch OHLCV data with compression (timeframe)
    data = await repo.fetch_ohlcv(
        compression=60,        # 60 minutes = 1 hour
        fromdate=arrow.now().shift(days=-1),
        todate=arrow.now()
    )
    
    # Latest/oldest timestamps
    latest = await repo.get_latest_timestamp()
    oldest = await repo.get_oldest_timestamp()
```

**Key READ-ONLY Methods:**
- `fetch_ohlcv(compression: int, fromdate: Arrow, todate: Arrow) -> List[Tuple]`
- `get_latest_timestamp(table_name: Optional[str] = None) -> Optional[Arrow]`
- `get_oldest_timestamp(table_name: Optional[str] = None) -> Optional[Arrow]`

#### TimeseriesRepository (READ-ONLY Operations)
```python
from fullon_ohlcv import TimeseriesRepository

async with TimeseriesRepository("binance", "BTC/USDT") as repo:
    # Unified OHLCV fetching (from trades or candles)
    data = await repo.fetch_ohlcv(
        compression=60,
        period="1h",
        fromdate=arrow.now().shift(days=-1),
        todate=arrow.now()
    )
```

## Timeframe/Compression Values

Based on the fullon_ohlcv patterns:
- `1` = 1 minute
- `5` = 5 minutes  
- `15` = 15 minutes
- `60` = 1 hour
- `240` = 4 hours
- `1440` = 1 day

## REST API Endpoint Mapping

### Trade Endpoints

| HTTP Endpoint | Repository Method | Description |
|---------------|------------------|-------------|
| `GET /api/trades/{exchange}/{symbol}?limit=N` | `get_recent_trades(limit=N)` | Recent trades |
| `GET /api/trades/{exchange}/{symbol}/range?start=T1&end=T2` | `get_trades_in_range(T1, T2)` | Historical trades |
| `GET /api/trades/{exchange}/{symbol}/stats` | Custom aggregation | Trade statistics |

### Candle Endpoints

| HTTP Endpoint | Repository Method | Description |
|---------------|------------------|-------------|
| `GET /api/candles/{exchange}/{symbol}/{timeframe}` | `fetch_ohlcv(compression, fromdate, todate)` | OHLCV candles |
| `GET /api/candles/{exchange}/{symbol}/{timeframe}/range` | `fetch_ohlcv(compression, fromdate, todate)` | Historical candles |

### Exchange/Symbol Endpoints

These will need to be implemented by querying database schemas and tables:
- `GET /api/exchanges` - List database schemas
- `GET /api/exchanges/{exchange}/symbols` - List tables in schema

## Database Connection Pattern

All repositories require these environment variables:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_OHLCV_NAME=fullon_ohlcv
DB_USER=username
DB_PASSWORD=password
```

## Error Handling Patterns

```python
from fullon_ohlcv import TradeRepository

try:
    async with TradeRepository("binance", "BTC/USDT") as repo:
        trades = await repo.get_recent_trades(limit=100)
except Exception as e:
    # Handle database connection errors, invalid symbols, etc.
    logger.error(f"Repository error: {e}")
    raise HTTPException(status_code=500, detail="Database error")
```

## UTC Timezone Requirements

All datetime objects must be timezone-aware UTC:
```python
from datetime import datetime, timezone

# Correct
timestamp = datetime.now(timezone.utc)

# Also correct with arrow
import arrow
timestamp = arrow.utcnow().datetime
```

## Integration Notes

1. **Context Manager Usage**: Always use `async with` pattern for automatic resource cleanup
2. **UTC Timestamps**: All timestamps must be timezone-aware UTC 
3. **Symbol Normalization**: The repositories handle symbol normalization automatically
4. **Table Creation**: Repositories create tables automatically on first use
5. **Error Handling**: Repositories raise exceptions for database errors
6. **Performance**: Use limit parameters to avoid large result sets

## Example FastAPI Dependency

```python
from fastapi import Depends, HTTPException
from fullon_ohlcv import TradeRepository

async def get_trade_repository(exchange: str, symbol: str):
    """FastAPI dependency for TradeRepository."""
    try:
        repo = TradeRepository(exchange, symbol)
        await repo.initialize()
        yield repo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if repo:
            await repo.close()
```

This reference provides everything needed to implement the fullon_ohlcv_api REST gateway!