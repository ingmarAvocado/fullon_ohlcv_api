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

## 📊 OHLCV Focus Areas

**Core OHLCV Operations** (using fullon_ohlcv dependency):

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

### **3. Read-Only Time-Series API Endpoints**

**Standalone Mode** (testing/development):
- `GET /api/trades/{exchange}/{symbol}` - Retrieve recent trades
- `GET /api/trades/{exchange}/{symbol}/range` - Historical trade data
- `GET /api/candles/{exchange}/{symbol}/{timeframe}` - Retrieve candle data  
- `GET /api/exchanges` - Available exchanges catalog

**Master API Mode** (production/recommended):
- `GET /api/v1/market/trades/{exchange}/{symbol}` - Historical market trades
- `GET /api/v1/market/trades/{exchange}/{symbol}/range` - Time-range trade queries  
- `GET /api/v1/market/trades/{exchange}/{symbol}/stats` - Trade statistics
- `GET /api/v1/market/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles
- `GET /api/v1/market/candles/{exchange}/{symbol}/{timeframe}/range` - Historical candles
- `GET /api/v1/market/exchanges` - Available exchanges catalog
- `GET /api/v1/market/exchanges/{exchange}/symbols` - Exchange symbols

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
├── src/fullon_ohlcv_api/
│   ├── __init__.py              # Library exports: FullonOhlcvGateway, get_all_routers
│   ├── gateway.py               # Main library class (composable)
│   ├── standalone_server.py     # Testing server only
│   ├── main.py                  # Legacy compatibility
│   ├── dependencies/            # FastAPI dependencies
│   │   └── database.py          # OHLCV session management
│   ├── routers/                 # OHLCV endpoints
│   │   ├── trades.py            # Trade data endpoints
│   │   ├── candles.py           # Candle data endpoints
│   │   ├── exchanges.py         # Exchange catalog endpoints
│   │   └── symbols.py           # Symbol catalog endpoints
│   └── models/                  # Pydantic request/response models
│       ├── requests.py          # OHLCV API request models
│       └── responses.py         # OHLCV API response models
├── examples/                    # Working code examples
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
# Database (handled by fullon_ohlcv)
DATABASE_URL=postgresql://user:pass@localhost/fullon_ohlcv

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

## 🧪 Testing Strategy

### **Test Categories**
```bash
# Unit tests - Individual components
tests/test_gateways.py
tests/test_repositories.py  
tests/test_models.py

# Integration tests - End-to-end workflows
tests/integration/test_trade_lifecycle.py
tests/integration/test_bulk_operations.py

# Performance tests - Time-series load testing
tests/performance/test_endpoints.py
```

### **Required Test Coverage**
- **Time-Series Operations**: Data retrieval, range queries, pagination
- **Repository Integration**: All READ operations, data aggregation
- **Data Validation**: OHLCV model validation, exchange/symbol validation
- **Integration**: Complete read workflows, multi-repository operations
- **Performance**: Response times, large dataset handling, concurrent requests

## 🚀 Quick Start Commands

```bash
# Initial setup
make setup      # Install dependencies, setup pre-commit

# Development
make dev        # Start development server
make test       # Run test suite
make check      # Full quality check

# Testing & Quality  
./run_test.py   # Comprehensive test runner (REQUIRED before commits)
make format     # Format code with Black + Ruff
make lint       # Check code quality

# OHLCV API Exploration
open http://localhost:8000/docs    # Swagger UI
open http://localhost:8000/redoc   # ReDoc interface
```

## 📖 Key References

- **OHLCV Operations**: See fullon_ohlcv documentation for all available methods
- **Examples**: Working code in `examples/` directory
- **Tests**: Pattern examples in `tests/conftest.py`
- **fullon_ohlcv Guide**: Refer to dependency documentation

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