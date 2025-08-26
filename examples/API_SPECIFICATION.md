# 📋 API Specification - fullon_ohlcv_api

**Living Specification: This document is generated from our working examples**

## 🎯 Overview

The fullon_ohlcv_api provides READ-ONLY access to OHLCV (Open, High, Low, Close, Volume) market data through both HTTP REST endpoints and WebSocket streaming. The API specification is **defined by working examples** in this directory.

**CRITICAL**: The examples are the authoritative specification - they show exactly what the API must do and how it should behave.

## 📚 Examples as Specification

| Example File | API Component | Endpoints Defined |
|--------------|---------------|-------------------|
| `trade_repository_example.py` | Trade Data | `GET /api/trades/{exchange}/{symbol}*` |
| `candle_repository_example.py` | OHLCV Candles | `GET /api/candles/{exchange}/{symbol}/{timeframe}*` |
| `timeseries_repository_example.py` | OHLCV Aggregation | `GET /api/timeseries/{exchange}/{symbol}/ohlcv` |
| `websocket_live_ohlcv_example.py` | Real-time Streaming | `WS /ws/ohlcv` |
| `run_all.py` | Integration Testing | Complete test infrastructure |

## 🛣️ API Endpoints

### Trade Data Endpoints

**Defined by: `trade_repository_example.py`**

#### Recent Trades
```
GET /api/trades/{exchange}/{symbol}
```

**Parameters** (from example):
```python
params = {"limit": 10}
```

**Response Format** (from example):
```json
{
  "trades": [
    {
      "timestamp": "2025-08-26T10:30:00Z",
      "price": 50000.0,
      "volume": 0.1,
      "side": "BUY",
      "type": "MARKET"
    }
  ],
  "count": 1,
  "exchange": "binance",
  "symbol": "BTC/USDT"
}
```

#### Historical Trades
```
GET /api/trades/{exchange}/{symbol}/range
```

**Parameters** (from example):
```python
params = {
    "start_time": start_time.isoformat(),  # ISO format datetime
    "end_time": end_time.isoformat()       # ISO format datetime
}
```

### OHLCV Candle Endpoints

**Defined by: `candle_repository_example.py`**

#### Recent Candles
```
GET /api/candles/{exchange}/{symbol}/{timeframe}
```

**Parameters** (from example):
```python
params = {"limit": 10}
```

**Response Format** (from example):
```json
{
  "candles": [
    {
      "timestamp": "2025-08-26T10:30:00Z",
      "open": 50000.0,
      "high": 50100.0,
      "low": 49900.0,
      "close": 50050.0,
      "vol": 10.5
    }
  ],
  "timeframe": "1h",
  "count": 1
}
```

#### Historical Candles
```
GET /api/candles/{exchange}/{symbol}/{timeframe}/range
```

**Parameters** (from example):
```python
params = {
    "start_time": start_time.isoformat(),
    "end_time": end_time.isoformat()
}
```

### OHLCV Aggregation Endpoint

**Defined by: `timeseries_repository_example.py`**

#### OHLCV from Trade Data
```
GET /api/timeseries/{exchange}/{symbol}/ohlcv
```

**Parameters** (from example):
```python
params = {
    "timeframe": "1m",                    # "1m", "5m", "15m", "1h", etc.
    "start_time": start_time.isoformat(), # ISO format datetime
    "end_time": end_time.isoformat(),     # ISO format datetime
    "limit": 10                           # Maximum number of candles
}
```

**Response Format** (from example):
```json
{
  "ohlcv": [
    {
      "timestamp": "2025-08-26T10:30:00Z",
      "open": 50000.0,
      "high": 50100.0,
      "low": 49900.0,
      "close": 50050.0,
      "vol": 10.5
    }
  ],
  "timeframe": "1m",
  "count": 1,
  "exchange": "binance",
  "symbol": "BTC/USDT"
}
```

### Real-time WebSocket Streaming

**Defined by: `websocket_live_ohlcv_example.py`**

#### WebSocket Connection
```
WS /ws/ohlcv
```

#### Subscription Message (from example)
```json
{
  "action": "subscribe",
  "exchange": "binance", 
  "symbol": "BTC/USDT",
  "timeframe": "1m",
  "type": "ohlcv_live"
}
```

#### OHLCV Update Message (from example)
```json
{
  "type": "ohlcv_update",
  "data": {
    "timestamp": "2025-08-26T10:30:00Z",
    "open": 50000.0,
    "high": 50100.0,
    "low": 49900.0,
    "close": 50050.0,
    "volume": 10.5,
    "is_final": false
  }
}
```

#### Unsubscription Message (from example)
```json
{
  "action": "unsubscribe",
  "exchange": "binance",
  "symbol": "BTC/USDT", 
  "timeframe": "1m",
  "type": "ohlcv_live"
}
```

## 🔧 Common Parameters

### Standard Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `limit` | integer | Maximum number of results (1-5000) | `10` |
| `start_time` | string | ISO format datetime (UTC) | `"2025-08-26T10:00:00Z"` |
| `end_time` | string | ISO format datetime (UTC) | `"2025-08-26T11:00:00Z"` |
| `timeframe` | string | Time interval | `"1m"`, `"5m"`, `"1h"`, `"1d"` |

### Path Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `exchange` | string | Exchange identifier | `"binance"` |
| `symbol` | string | Trading pair symbol | `"BTC/USDT"` |
| `timeframe` | string | Candle timeframe | `"1h"` |

## 📊 Response Formats

### Standard Response Structure

All HTTP responses follow this pattern (from examples):

```json
{
  "data_array": [...],    // "trades", "candles", or "ohlcv" 
  "count": 10,           // Number of items returned
  "exchange": "binance", // Echo request parameter
  "symbol": "BTC/USDT"  // Echo request parameter
}
```

### Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 404
}
```

## 🧪 Integration Testing

**Defined by: `run_all.py`**

### Test Infrastructure Requirements

The API implementation must support the complete integration testing workflow:

1. **Test Database Setup**: Create test OHLCV data using fullon_ohlcv repositories
2. **API Server Management**: Start/stop API server with test database
3. **Example Execution**: Run all examples against live API endpoints
4. **Result Validation**: All examples must complete successfully
5. **Cleanup**: Proper resource cleanup after testing

### Test Commands (from run_all.py)

```bash
# Complete integration testing
python examples/run_all.py

# Individual endpoint testing  
python examples/run_all.py --example trade_repository_example.py
python examples/run_all.py --example candle_repository_example.py
python examples/run_all.py --example timeseries_repository_example.py
python examples/run_all.py --example websocket_live_ohlcv_example.py

# Development testing environment
python examples/run_all.py --setup-only
python examples/run_all.py --cleanup-only
python examples/run_all.py --list
```

## 🎯 Success Criteria

**The API implementation is complete when:**

1. **All Examples Work**: Every example runs successfully against the implemented API
2. **Integration Testing Passes**: `python examples/run_all.py` completes without errors
3. **Response Formats Match**: API responses match exactly what examples expect
4. **Parameters Function**: All query/path parameters work as examples demonstrate
5. **WebSocket Protocol**: Real-time streaming works as websocket example shows

## 🔄 Development Workflow

### Examples-First Development Process

1. **Understand Examples**: Study what each example does and expects
2. **Implement Endpoints**: Create API endpoints that make examples work
3. **Test Integration**: Run examples against implementation
4. **Fix Issues**: Adjust implementation until all examples pass
5. **Validate Complete**: Ensure `run_all.py` passes fully

### Validation Commands

```bash
# Primary validation - all examples must work
python examples/run_all.py

# Secondary validation - traditional tests  
./run_test.py

# Development server for testing
python examples/run_all.py --setup-only
# Then manually run individual examples for debugging
```

---

**This specification is derived from working examples and represents the exact behavior required for a successful API implementation.**