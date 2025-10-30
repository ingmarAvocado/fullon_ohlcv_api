# Fullon OHLCV SDK

A Python SDK for the `fullon_ohlcv_api` that provides a clean, async interface returning proper `fullon_ohlcv` objects instead of raw JSON responses.

## Features

- **Async HTTP Client**: Clean async API for all `fullon_ohlcv_api` endpoints
- **Object Deserialization**: Automatic conversion of JSON responses to `fullon_ohlcv` `Trade` and `Candle` objects
- **WebSocket Streaming**: Real-time OHLCV data streaming yielding `Candle` objects
- **Type Safety**: Full IDE support with proper typing
- **Error Handling**: Comprehensive exception hierarchy

## Installation

```bash
# Install from the sdk/ directory
pip install -e sdk/

# Or install dependencies manually
pip install httpx websockets fullon_ohlcv python-dotenv
```

## Quick Start

```python
from fullon_ohlcv_sdk import FullonOhlcvClient

async def main():
    async with FullonOhlcvClient("http://localhost:9000") as client:
        # Get trades as Trade objects (not JSON!)
        trades = await client.get_trades("binance", "BTC/USDT", limit=10)

        for trade in trades:
            print(f"Trade: ${trade.price} @ {trade.timestamp}")

        # Get candles as Candle objects (not JSON!)
        candles = await client.get_candles("binance", "ETH/USDT", "1h", limit=24)

        for candle in candles:
            print(f"Candle: O:{candle.open} H:{candle.high} L:{candle.low} C:{candle.close}")

asyncio.run(main())
```

## API Reference

### FullonOhlcvClient

#### HTTP Methods

- `get_trades(exchange, symbol, limit=None, start_time=None, end_time=None)` → `List[Trade]`
- `get_candles(exchange, symbol, timeframe, limit=None, start_time=None, end_time=None)` → `List[Candle]`
- `get_ohlcv_timeseries(exchange, symbol, timeframe, start_time=None, end_time=None)` → `List[Candle]`
- `get_exchanges()` → `List[str]`
- `get_exchange_symbols(exchange)` → `List[str]`

#### WebSocket Streaming

```python
from fullon_ohlcv_sdk import OhlcvWebSocketClient

async def stream_candles():
    async with OhlcvWebSocketClient("http://localhost:9000") as client:
        async for candle in client.stream_ohlcv("binance", "BTC/USDT", "1m"):
            print(f"New candle: {candle.close}")  # candle is a fullon_ohlcv.Candle object
```

## Object Types

The SDK returns proper `fullon_ohlcv` objects:

### Trade Object
```python
@dataclass
class Trade:
    timestamp: datetime  # UTC timezone-aware
    price: float
    volume: float
    side: str  # "BUY" or "SELL"
    type: str  # "MARKET" or "LIMIT"
```

### Candle Object
```python
@dataclass
class Candle:
    timestamp: datetime  # UTC timezone-aware
    open: float
    high: float
    low: float
    close: float
    vol: float  # volume
```

## Error Handling

```python
from fullon_ohlcv_sdk import (
    FullonOhlcvError,
    APIConnectionError,
    ExchangeNotFoundError,
    SymbolNotFoundError,
    TimeframeError,
    DeserializationError,
)

try:
    trades = await client.get_trades("invalid_exchange", "BTC/USDT")
except ExchangeNotFoundError:
    print("Exchange not found")
except APIConnectionError:
    print("Connection failed")
```

## Examples

See the `examples/` directory for complete usage examples:

- `trade_repository_sdk_example.py` - Trade data retrieval
- `candle_repository_sdk_example.py` - OHLCV candle data
- `timeseries_repository_sdk_example.py` - OHLCV aggregation
- `websocket_live_ohlcv_sdk_example.py` - Real-time streaming
- `run_all_sdk.py` - Run all examples

## Comparison with Raw API

### Raw HTTP (JSON responses)
```python
import httpx

async def get_trades_raw():
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get("http://localhost:9000/api/trades/binance/BTC/USDT")
        trades_json = response.json()["trades"]

        # Manual parsing required
        for trade_dict in trades_json:
            price = float(trade_dict["price"])
            timestamp = datetime.fromisoformat(trade_dict["timestamp"])
            # ... manual conversion for each field
```

### SDK (Object responses)
```python
from fullon_ohlcv_sdk import FullonOhlcvClient

async def get_trades_sdk():
    async with FullonOhlcvClient("http://localhost:9000") as client:
        trades = await client.get_trades("binance", "BTC/USDT")

        # Direct object access
        for trade in trades:
            print(f"Price: {trade.price}")  # Already a float
            print(f"Time: {trade.timestamp}")  # Already a datetime
```

## Development

The SDK is organized as follows:

```
sdk/
├── fullon_ohlcv_sdk/
│   ├── __init__.py      # Main exports
│   ├── client.py        # HTTP client
│   ├── websocket.py     # WebSocket client
│   ├── models.py        # JSON→object conversion
│   └── exceptions.py    # Error classes
├── examples/            # Usage examples
├── pyproject.toml       # Packaging
└── README.md           # This file
```

## Requirements

- Python 3.13+
- `httpx` - Async HTTP client
- `websockets` - WebSocket support
- `fullon_ohlcv` - Core data models
- `python-dotenv` - Environment configuration

## License

MIT License