# 📚 fullon_ohlcv_api Examples

Simple examples demonstrating fullon_ohlcv_api usage patterns via HTTP API and WebSocket streaming.

## 🎯 Examples

| Example | Description |
|---------|-------------|
| `trade_repository_example.py` | Trade data retrieval via HTTP API |
| `candle_repository_example.py` | Candle/OHLCV data via HTTP API |
| `timeseries_repository_example.py` | OHLCV aggregation via HTTP API |
| `websocket_live_ohlcv_example.py` | Real-time OHLCV streaming via WebSocket |
| `run_all.py` | Execute all examples with test infrastructure management |

## 🚀 Quick Start

### Environment Setup

Copy `.env.example` to `.env`:

```bash
# API Server Configuration used by run_all
API_HOST=127.0.0.1
API_PORT=9000
```

### Dependencies

This project uses Poetry for dependency management.

```bash
poetry add aiohttp python-dotenv websockets
```

### Run Examples

```bash
# All examples (full integration test)
poetry run python examples/run_all.py

# Individual examples with test infrastructure
poetry run python examples/run_all.py --example trade_repository_example.py
poetry run python examples/run_all.py --example candle_repository_example.py
poetry run python examples/run_all.py --example timeseries_repository_example.py
poetry run python examples/run_all.py --example websocket_live_ohlcv_example.py

# Development modes
poetry run python examples/run_all.py --setup-only     # Setup test DB + start server, keep running
poetry run python examples/run_all.py --cleanup-only   # Cleanup any running servers
poetry run python examples/run_all.py --list          # List available examples

# Direct execution (requires running API server)
poetry run python examples/trade_repository_example.py  # Only if server already running
```

**Note**: Individual examples require the API server and test database. Use `examples/run_all.py` to manage the test infrastructure automatically. Default port is 9000 and clients connect to 127.0.0.1.

## 📊 API Usage

### HTTP API (Historical Data)
```python
async with aiohttp.ClientSession() as session:
    url = f"{base_url}/api/trades/{exchange}/{symbol}"
    async with session.get(url, params={"limit": 100}) as response:
        data = await response.json()
        trades = data.get("trades", [])
```

### WebSocket (Real-time Streaming)
```python
async with websockets.connect(ws_url) as websocket:
    subscribe_msg = {
        "action": "subscribe",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1m",
        "type": "ohlcv_live"
    }
    await websocket.send(json.dumps(subscribe_msg))
    
    message = await websocket.recv()
    data = json.loads(message)
```

## 🔗 API Endpoints

- `GET /api/trades/{exchange}/{symbol}` - Recent trades
- `GET /api/trades/{exchange}/{symbol}/range` - Historical trades  
- `GET /api/candles/{exchange}/{symbol}/{timeframe}` - Recent candles
- `GET /api/candles/{exchange}/{symbol}/{timeframe}/range` - Historical candles
- `GET /api/timeseries/{exchange}/{symbol}/ohlcv` - OHLCV aggregation
- `WS /ws/ohlcv` - Real-time OHLCV streaming

Examples mirror fullon_ohlcv repository patterns but use HTTP/WebSocket instead of direct database access.
