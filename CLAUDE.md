# 🤖 CLAUDE.md - fullon_ohlcv_api Development Guide

**For LLMs/Claude: Complete development guidelines for the fullon_ohlcv_api project**

## 🎯 Project Mission

**LRRS-Compliant Library**: Create a composable FastAPI gateway that exposes OHLCV market data operations as REST endpoints, designed for integration into a master_api alongside other fullon libraries.

## 🏗️ LRRS Architecture Principles

**This project MUST follow LRRS principles:**

- **Little**: Single purpose - OHLCV market data API gateway only
- **Responsible**: One clear job - secure REST API for OHLCV operations
- **Reusable**: Works with any fullon_ohlcv deployment, composable into master_api
- **Separate**: Zero coupling beyond fullon_ohlcv + fullon_log

### **Critical Design Decision: Library vs Standalone**

```python
# Library usage (PRIMARY use case):
from fullon_ohlcv_api import FullonOhlcvGateway, get_all_routers

# Fullon Master Trading API integration (RECOMMENDED):
from fastapi import FastAPI
from fullon_orm_api import get_all_routers as get_orm_routers
from fullon_cache_api import get_all_routers as get_cache_routers
from fullon_ohlcv_api import get_all_routers as get_ohlcv_routers

app = FastAPI(title="Fullon Master Trading API", version="1.0.0")

# Database operations
for router in get_orm_routers():
    app.include_router(router, prefix="/api/v1/db", tags=["Database"])

# Cache operations  
for router in get_cache_routers():
    app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])

# Market data operations
for router in get_ohlcv_routers():
    app.include_router(router, prefix="/api/v1/market", tags=["Market Data"])

# Standalone usage (TESTING only):
python -m fullon_ohlcv_api.standalone_server
```

## 📚 Examples-Driven Development

**CRITICAL**: Our `examples/` folder defines the API specification. The examples are working demonstrations of what the API must do - they are the authoritative specification for implementation.

### **Living API Specification**
```
examples/
├── trade_repository_example.py       # Defines trade data endpoints
├── candle_repository_example.py      # Defines candle/OHLCV endpoints  
├── timeseries_repository_example.py  # Defines OHLCV aggregation endpoints
├── websocket_live_ohlcv_example.py   # Defines WebSocket streaming
└── run_all.py                        # Integration testing infrastructure
```

**Development Process**: 
1. **Examples First**: Examples show exactly what API must do
2. **TDD Implementation**: Implement endpoints to make examples work  
3. **Integration Testing**: `run_all.py` validates complete workflows
4. **Success Criteria**: All examples must work against implemented API

## 📊 OHLCV Focus Areas

**Core OHLCV Operations** (defined by examples, using fullon_ohlcv dependency):

### **🔍 READ-ONLY DATA API**
**IMPORTANT**: This API **ONLY** exposes read/fetch operations. No updates, inserts, or write operations are in scope.

### **1. Market Data Retrieval**
- Retrieve trade data (OHLCVTrade) - **READ ONLY**
- Retrieve candle data (OHLCVCandle) - **READ ONLY**
- Time-series queries with range filtering
- Historical data export and analysis

### **2. Repository Pattern Integration**
```python
# READ-ONLY TradeRepository operations:
from fullon_ohlcv import TradeRepository, CandleRepository

async with TradeRepository("binance", "BTC/USDT") as repo:
    trades = await repo.get_recent_trades(limit=100)
    historical = await repo.get_trades_in_range(start, end)
    
async with CandleRepository("binance", "ETH/USDT") as repo:
    candles = await repo.get_candles_in_range(start, end)
    recent_candles = await repo.get_recent_candles(limit=24)
```

### **3. Read-Only Time-Series API Endpoints (Defined by Examples)**

**HTTP Endpoints (from examples/)**:
- `GET /api/trades/{exchange}/{symbol}` - Recent trades (`trade_repository_example.py`)
- `GET /api/trades/{exchange}/{symbol}/range` - Historical trades  
- `GET /api/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles (`candle_repository_example.py`)
- `GET /api/candles/{exchange}/{symbol}/{timeframe}/range` - Historical candles
- `GET /api/timeseries/{exchange}/{symbol}/ohlcv` - OHLCV aggregation (`timeseries_repository_example.py`)
- `GET /api/exchanges` - Available exchanges catalog

**WebSocket Endpoints (from examples/)**:
- `WS /ws/ohlcv` - Real-time OHLCV streaming (`websocket_live_ohlcv_example.py`)
  ```python
  # Subscription message format:
  {
    "action": "subscribe",
    "exchange": "binance", 
    "symbol": "BTC/USDT",
    "timeframe": "1m",
    "type": "ohlcv_live"
  }
  ```

**Master API Mode** (production/recommended):
- `GET /api/v1/market/trades/{exchange}/{symbol}` - Historical market trades
- `GET /api/v1/market/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles  
- `GET /api/v1/market/timeseries/{exchange}/{symbol}/ohlcv` - OHLCV aggregation
- `WS /api/v1/market/ws/ohlcv` - Real-time OHLCV streaming
- `GET /api/v1/market/exchanges` - Available exchanges catalog

## 🛠️ Architecture Overview

### **Fullon Ecosystem Integration**
```
┌─────────────────────────────────────────────────────────────────┐
│                 Fullon Master Trading API                      │
│                     /api/v1/* endpoints                        │
├─────────────┬─────────────────┬─────────────────────────────────┤
│📊 /market/  │  🗄️ /db/        │  ⚡ /cache/                     │
│             │                 │                                 │
│fullon_ohlcv │ fullon_orm_api  │ fullon_cache_api                │
│_api         │                 │                                 │
└─────────────┴─────────────────┴─────────────────────────────────┘
      │                   │                       │
      ▼                   ▼                       ▼
┌─────────────┐   ┌─────────────────┐   ┌─────────────────┐
│fullon_ohlcv │   │ Application     │   │ Redis/Cache     │
│(TimescaleDB)│   │ Database        │   │ Real-time Data  │
│Time-series  │   │ Persistent Data │   │ Queues & Events │
└─────────────┘   └─────────────────┘   └─────────────────┘
```

### **Component Responsibilities**
- **fullon_ohlcv_api**: Historical market data, time-series analysis (READ-ONLY)
- **fullon_orm_api**: Application data persistence, user records, trading positions
- **fullon_cache_api**: Real-time feeds, price alerts, temporary data, pub/sub

### **Project Structure**
```
fullon_ohlcv_api/
├── examples/                    # 📚 LIVING API SPECIFICATION
│   ├── trade_repository_example.py      # Trade endpoints specification
│   ├── candle_repository_example.py     # Candle endpoints specification
│   ├── timeseries_repository_example.py # Timeseries endpoints specification
│   ├── websocket_live_ohlcv_example.py  # WebSocket streaming specification
│   ├── run_all.py                       # Integration testing infrastructure
│   └── README.md                        # Examples usage and API overview
├── src/fullon_ohlcv_api/
│   ├── __init__.py              # Library exports: FullonOhlcvGateway, get_all_routers
│   ├── gateway.py               # Main library class (composable)
│   ├── standalone_server.py     # Testing server only
│   ├── main.py                  # Legacy compatibility
│   ├── dependencies/            # FastAPI dependencies
│   │   └── database.py          # OHLCV session management
│   ├── routers/                 # OHLCV endpoints (implement examples)
│   │   ├── trades.py            # Trade endpoints (→ trade_repository_example.py)
│   │   ├── candles.py           # Candle endpoints (→ candle_repository_example.py)
│   │   ├── timeseries.py        # Timeseries endpoints (→ timeseries_repository_example.py)
│   │   ├── websocket.py         # WebSocket streaming (→ websocket_live_ohlcv_example.py)
│   │   ├── exchanges.py         # Exchange catalog endpoints
│   │   └── symbols.py           # Symbol catalog endpoints
│   └── models/                  # Pydantic request/response models
│       ├── requests.py          # OHLCV API request models
│       └── responses.py         # OHLCV API response models
├── tests/                       # Comprehensive test suite
└── docs/                        # Additional documentation
```

## 🚀 Core Development Patterns

### **1. Read-Only OHLCV Repository Endpoint Pattern**
```python
# Standard pattern for all READ-ONLY OHLCV endpoints:
@router.get("/{exchange}/{symbol}/trades", response_model=TradesResponse)
async def get_trades(
    exchange: str,
    symbol: str,
    limit: int = Query(100, ge=1, le=5000),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    # 1. Validate exchange and symbol
    validate_exchange_symbol(exchange, symbol)
    
    # 2. READ-ONLY OHLCV repository operation
    async with TradeRepository(exchange, symbol) as repo:
        if start_time and end_time:
            trades = await repo.get_trades_in_range(start_time, end_time)
        else:
            trades = await repo.get_recent_trades(limit=limit)
    
    # 3. Return formatted response (no modifications to database)
    return TradesResponse(trades=trades, count=len(trades))
```

### **2. Time-Series Data Management**
```python
# Time-series query patterns:
from datetime import datetime, timezone, timedelta

# Recent data queries
async def get_recent_data(repo, limit: int = 100):
    return await repo.get_recent_trades(limit=limit)

# Time range queries
async def get_historical_data(repo, hours: int = 24):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    return await repo.get_trades_in_range(start, end)

# Data aggregation and statistics
async def get_trade_statistics(repo, hours: int = 24):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    trades = await repo.get_trades_in_range(start, end)
    # Compute statistics from retrieved data
    return calculate_stats(trades)
```

### **3. Error Handling Pattern**
```python
from fastapi import HTTPException

# OHLCV-specific HTTP errors:
raise HTTPException(status_code=404, detail="Exchange not found")
raise HTTPException(status_code=404, detail="Symbol not available")
raise HTTPException(status_code=422, detail="Invalid timeframe")
raise HTTPException(status_code=400, detail="Invalid time range")
```

### **4. Logging Pattern**
```python
from fullon_log import get_component_logger

# Component-specific logging:
logger = get_component_logger("fullon.api.ohlcv")

# Structured logging:
logger.info("Trade data retrieved", exchange="binance", symbol="BTC/USDT", count=150)
logger.error("Database error", error=str(e), exchange="coinbase", symbol="ETH/USD")
```

## 🔑 Environment Configuration

### **Required Environment Variables**
```bash
# Database (handled by fullon_ohlcv) — use DB_* variables
DB_HOST=10.206.35.109
DB_PORT=5432
DB_USER=fullon
DB_PASSWORD=fullon
DB_OHLCV_NAME=fullon_ohlcv2
DB_TEST_NAME=fullon_ohlcv2_test

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Logging (fullon-log)
LOG_LEVEL=DEBUG              # For development
LOG_FORMAT=development       # For development  
LOG_CONSOLE=true
LOG_COLORS=true
LOG_FILE_PATH=/tmp/fullon/ohlcv_api.log
```

## 📋 OHLCV Endpoint Coverage Requirements

**Every READ-ONLY fullon_ohlcv operation MUST have an API endpoint:**

### **TradeRepository Endpoints (READ-ONLY)** 
- Trade data retrieval with time filtering
- Recent trades queries
- Trade statistics and aggregation
- Historical trade data export

### **CandleRepository Endpoints (READ-ONLY)**
- Candle data retrieval by timeframe
- Historical candle queries
- OHLCV aggregation operations
- Time-series candle analysis

### **Exchange & Symbol Management**
- Available exchanges catalog
- Symbols per exchange listing
- Exchange validation
- Symbol normalization

### **Time-Series Operations (READ-ONLY)**
- Time range validation
- Timezone handling (UTC only)  
- Pagination for large datasets
- Data export and analysis endpoints

## 🧪 Examples-Driven Testing Strategy

### **Primary Testing Strategy: Examples as Integration Tests**

**`run_all.py` - Complete Testing Infrastructure**:
1. **Setup test database** with sample OHLCV data
2. **Start API server** in test mode  
3. **Run examples** as integration tests against live API
4. **Validate results** - all examples must pass
5. **Cleanup** - stop server, cleanup test data

```bash
# Complete integration testing
python examples/run_all.py                          # All examples
python examples/run_all.py --example trade_repository_example.py  # Individual
python examples/run_all.py --setup-only            # Development mode
```

### **Test Categories**
```bash
# Examples-driven integration tests (PRIMARY)
examples/run_all.py                    # Complete API validation

# Traditional unit tests (SECONDARY)  
tests/unit/test_models.py              # Pydantic model validation
tests/unit/test_dependencies.py        # Database dependency injection
tests/unit/test_routers.py             # Individual endpoint logic

# End-to-end validation (TERTIARY)
tests/integration/test_complete_api.py # Full workflow validation
```

### **Success Criteria Hierarchy**
1. **Examples work**: All examples run successfully against implemented API
2. **Unit tests pass**: Traditional test suite passes  
3. **Performance acceptable**: Response times within limits

### **Required Test Coverage**
- **Examples Validation**: All 4 examples + WebSocket work against API
- **Integration Testing**: `run_all.py` manages complete test lifecycle
- **Repository Integration**: All READ operations through fullon_ohlcv
- **WebSocket Functionality**: Real-time OHLCV streaming working
- **Timeseries Aggregation**: OHLCV generation from trade data

## 🚀 Quick Start Commands

```bash
# Initial setup
make setup      # Install dependencies, setup pre-commit

# Examples-Driven Development (PRIMARY workflow)
python examples/run_all.py                          # Test all implemented endpoints
python examples/run_all.py --example trade_repository_example.py   # Test specific endpoint
python examples/run_all.py --setup-only            # Setup test environment for development
python examples/run_all.py --list                  # Show available examples

# Development & Implementation
make dev        # Start development server  
make test       # Run traditional test suite
./run_test.py   # Comprehensive test runner (REQUIRED before commits)

# Code Quality
make format     # Format code with Black + Ruff
make lint       # Check code quality
make check      # Full quality check

# API Exploration (after implementation)
open http://localhost:8000/docs    # Swagger UI
open http://localhost:8000/redoc   # ReDoc interface

# Examples-First Development Process
# 1. Run examples to see what API needs to do
# 2. Implement endpoints to make examples work
# 3. Validate with run_all.py - all examples must pass
```

## 📖 Key References

### **fullon_ohlcv Library Core Documentation**
- **Installation**: `poetry add git+ssh://git@github.com/ingmarAvocado/fullon_ohlcv.git`
- **LLM Quickstart**: `docs/FULLON_OHLCV_LLM_QUICKSTART.md` - Complete usage examples
- **Method Reference**: `docs/FULLON_OHLCV_METHOD_REFERENCE.md` - All available repository methods

### **fullon_ohlcv Repository Methods (READ-ONLY)**
```python
# TradeRepository - Core time-series trade operations
from fullon_ohlcv.repositories.ohlcv import TradeRepository

async with TradeRepository("binance", "BTC/USDT", test=True) as repo:
    # Data retrieval (READ-ONLY)
    trades = await repo.get_recent_trades(limit=100)
    historical = await repo.get_trades_in_range(start_time, end_time, limit=10)
    
    # Timestamp queries
    oldest = await repo.get_oldest_timestamp()
    latest = await repo.get_latest_timestamp()

# CandleRepository - OHLCV candle data operations  
from fullon_ohlcv.repositories.ohlcv import CandleRepository

async with CandleRepository("binance", "ETH/USDT", test=True) as repo:
    # Candle data retrieval (READ-ONLY)
    candles = await repo.get_candles_in_range(start_time, end_time)
    
    # Timestamp queries
    oldest = await repo.get_oldest_timestamp()
    latest = await repo.get_latest_timestamp()

# TimeseriesRepository - OHLCV aggregation from trade data
from fullon_ohlcv.repositories.ohlcv import TimeseriesRepository

async with TimeseriesRepository("binance", "BTC/USDT", test=True) as repo:
    # Generate OHLCV from existing trades (READ-ONLY)
    ohlcv_data = await repo.fetch_ohlcv(
        start_time=start_time,
        end_time=end_time,
        timeframe="1m",  # "1m", "5m", "1h", "1d", etc.
        limit=10
    )
    
    # Timestamp queries
    oldest = await repo.get_oldest_timestamp()
    latest = await repo.get_latest_timestamp()
```

### **fullon_ohlcv Data Models**
```python
from fullon_ohlcv.models import Trade, Candle

# Trade model structure
Trade(
    timestamp=datetime.now(timezone.utc),  # Always UTC
    price=50000.0,
    volume=0.1,
    side="BUY",      # "BUY" or "SELL"
    type="MARKET"    # "MARKET" or "LIMIT"
)

# Candle model structure  
Candle(
    timestamp=datetime.now(timezone.utc),  # Always UTC
    open=3000.0,
    high=3010.0,
    low=2995.0,
    close=3005.0,
    vol=150.5
)
```

### **fullon_ohlcv Performance Optimization**
```python
# Always use uvloop for better async performance
from fullon_ohlcv.utils import install_uvloop

def main():
    install_uvloop()  # Call before asyncio.run() for performance boost
    asyncio.run(your_async_function())
```

### **Database Schema Pattern (fullon_ohlcv)**
- **TradeRepository("binance", "BTC/USDT")** creates:
  - Schema: `binance`
  - Table: `binance.BTC_USDT_trades` 
  - TimescaleDB hypertable for time-series performance
- **CandleRepository("binance", "ETH/USDT")** creates:
  - Schema: `binance`
  - Table: `binance.ETH_USDT_candles`
  - TimescaleDB hypertable optimization

### **Critical fullon_ohlcv Integration Points**
1. **Context Manager Pattern**: Always use `async with Repository(...) as repo:` 
2. **Test Mode**: Use `test=True` parameter to avoid production data contamination
3. **UTC Timestamps**: All datetime objects must be timezone-aware UTC
4. **Async Operations**: Every repository operation is asynchronous
5. **Performance**: Call `install_uvloop()` before `asyncio.run()` for optimal performance

### **Project References**
- **Examples**: Working code in `examples/` directory
- **Tests**: Pattern examples in `tests/conftest.py`
- **Project Structure**: `docs/PROJECT_STRUCTURE.md` - Complete architecture guide

## ⚠️ Critical Rules

1. **LRRS Compliance**: Never violate Little, Responsible, Reusable, Separate
2. **TDD Only**: Tests first, implementation second, `./run_test.py` must pass
3. **Library First**: Design for master_api composition, standalone is secondary
4. **UTC Only**: All timestamps must be timezone-aware UTC
5. **Async Only**: Every operation must be asynchronous
6. **Time-Series Focus**: Optimize for time-series data patterns

## 🕐 Time-Series Best Practices

### **1. Always Use UTC**
```python
from datetime import datetime, timezone

# Correct:
timestamp = datetime.now(timezone.utc)

# Wrong:
timestamp = datetime.now()  # Naive datetime
```

### **2. Efficient Range Queries**
```python
# Optimize for time ranges:
async def get_hourly_data(exchange: str, symbol: str, hours: int = 24):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    
    async with TradeRepository(exchange, symbol) as repo:
        return await repo.get_trades_in_range(start, end)
```

### **3. Pagination for Large Datasets**
```python
# Handle large time-series data:
@router.get("/trades")
async def get_paginated_trades(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0)
):
    # Implement pagination logic
```

---

**Remember**: This is a composable library that will integrate with 3-4 other similar libraries in a master_api. Design every decision with composition and reusability in mind! 🚀
