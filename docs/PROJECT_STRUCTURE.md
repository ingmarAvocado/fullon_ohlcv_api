# 🏗️ fullon_ohlcv_api Project Structure

**LRRS-Compliant OHLCV Market Data API Gateway Architecture**

## 📋 Project Overview

fullon_ohlcv_api is a composable FastAPI gateway library that exposes **read-only** OHLCV (Open, High, Low, Close, Volume) market data operations as secure REST endpoints. It follows LRRS (Little, Responsible, Reusable, Separate) principles and integrates seamlessly into master_api alongside other fullon libraries.

**🔍 READ-ONLY API**: This library **only** exposes data retrieval operations. No updates, inserts, or write operations are in scope.

**📚 EXAMPLES-DRIVEN**: Our `examples/` folder defines the API specification. The examples are working demonstrations that show exactly what endpoints the API must implement and how they should behave.

## 🏗️ Architecture Principles

### LRRS Compliance
- **Little**: Single purpose - READ-ONLY OHLCV market data API gateway
- **Responsible**: Secure REST API for read-only time-series market data operations  
- **Reusable**: Composable into master_api, works with any fullon_ohlcv deployment
- **Separate**: Zero coupling beyond fullon_ohlcv + fullon_log dependencies

### Design Philosophy
- **Library First**: Primary use case is composition into master_api
- **Standalone Secondary**: Testing and development server mode
- **Time-Series Focused**: Optimized for read-only OHLCV time-series data patterns
- **Read-Only Operations**: No write/update/insert operations in scope
- **Async Throughout**: All operations are asynchronous
- **UTC Only**: All timestamps are timezone-aware UTC

## 📁 Directory Structure

```
fullon_ohlcv_api/
├── examples/                   # 📚 LIVING API SPECIFICATION
│   ├── trade_repository_example.py      # 💹 Trade endpoints specification
│   ├── candle_repository_example.py     # 🕯️ Candle/OHLCV endpoints specification
│   ├── timeseries_repository_example.py # ⏰ Timeseries OHLCV aggregation specification
│   ├── websocket_live_ohlcv_example.py  # 📡 Real-time WebSocket streaming specification
│   ├── run_all.py                       # 🧪 Integration testing infrastructure
│   ├── README.md                        # 📖 Examples usage and API overview
│   └── API_SPECIFICATION.md             # 📋 Formal API specification from examples
│
├── CLAUDE.md                    # 🤖 Development guidelines for LLMs
├── PROJECT_STRUCTURE.md         # 📋 This architecture documentation
├── README.md                    # 📖 Project overview and usage guide
├── Makefile                     # 🔧 Development automation commands
├── pyproject.toml              # 📦 Poetry configuration and dependencies
├── run_test.py                 # 🧪 Comprehensive test runner script
│
├── src/                        # 📂 Source code directory
│   └── fullon_ohlcv_api/      # 📦 Main package
│       ├── __init__.py         # 🔌 Library exports and public API
│       ├── main.py             # 🔄 Legacy compatibility module
│       ├── gateway.py          # 🏗️ Main FullonOhlcvGateway class
│       ├── standalone_server.py # 🖥️ Development/testing server
│       │
│       ├── dependencies/       # 🔗 FastAPI dependency injection
│       │   ├── __init__.py
│       │   └── database.py     # 📊 OHLCV database session management
│       │
│       ├── models/            # 📋 Pydantic data models
│       │   ├── __init__.py
│       │   ├── requests.py     # 📥 API request models (from examples)
│       │   └── responses.py    # 📤 API response models (from examples)
│       │
│       └── routers/           # 🛣️ FastAPI endpoint routers (implement examples)
│           ├── __init__.py
│           ├── trades.py       # 💹 Trade endpoints (→ trade_repository_example.py)
│           ├── candles.py      # 🕯️ Candle endpoints (→ candle_repository_example.py)
│           ├── timeseries.py   # ⏰ Timeseries endpoints (→ timeseries_repository_example.py)
│           ├── websocket.py    # 📡 WebSocket streaming (→ websocket_live_ohlcv_example.py)
│           ├── exchanges.py    # 🏢 Exchange catalog endpoints
│           └── symbols.py      # 🔤 Symbol catalog endpoints
│
├── tests/                     # 🧪 Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py            # ⚙️ Pytest configuration and fixtures
│   ├── test_main.py           # 🔬 Main module tests
│   ├── unit/                  # 🔬 Unit tests directory
│   │   └── __init__.py
│   └── integration/           # 🔗 Integration tests directory
│       └── __init__.py
│
└── docs/                      # 📖 Additional documentation
    ├── PROJECT_STRUCTURE.md   # 📋 This file - architecture overview
    ├── FULLON_OHLCV_LLM_QUICKSTART.md    # 🚀 fullon_ohlcv usage guide
    └── FULLON_OHLCV_METHOD_REFERENCE.md  # 📚 fullon_ohlcv method reference
```

## 📚 Examples as API Specification

**CRITICAL CONCEPT**: The `examples/` directory is not just documentation - it's the authoritative specification for what the API must do.

### **Examples Define Implementation Requirements**
- `trade_repository_example.py` → Must implement trade endpoints
- `candle_repository_example.py` → Must implement candle endpoints  
- `timeseries_repository_example.py` → Must implement timeseries aggregation endpoints
- `websocket_live_ohlcv_example.py` → Must implement WebSocket streaming
- `run_all.py` → Defines integration testing infrastructure requirements

## 🔌 Library Interface

### Public API Exports (`__init__.py`)
```python
from .gateway import FullonOhlcvGateway

def get_all_routers():
    """Return all routers for master_api composition."""
    pass

# Public exports
__all__ = ["FullonOhlcvGateway", "get_all_routers"]
```

### Primary Usage Patterns
```python
# Library usage in master_api:
from fullon_ohlcv_api import FullonOhlcvGateway, get_all_routers

# Standalone usage for testing:
python -m fullon_ohlcv_api.standalone_server
```

## 🏗️ Core Components

### 1. FullonOhlcvGateway (`gateway.py`)
**Main library class providing composable FastAPI gateway functionality.**

```python
class FullonOhlcvGateway:
    """
    Configurable OHLCV API gateway for master_api integration.
    
    Features:
    - Configurable URL prefix for composition
    - Auto-generated OpenAPI documentation  
    - Built-in health and info endpoints
    - Router composition for modular design
    """
    
    def __init__(self, prefix: str = "", title: str = "fullon_ohlcv_api"):
        pass
    
    def get_app(self) -> FastAPI:
        """Return configured FastAPI application."""
        pass
        
    def get_routers(self) -> List[APIRouter]:
        """Return all routers for external composition."""
        pass
```

### 2. Router Architecture (`routers/`) - **Implements Examples**
**Modular endpoint organization defined by examples specifications.**

#### Trade Data Router (`trades.py`) - **Implements `trade_repository_example.py`**
- `GET /{exchange}/{symbol}/trades` - Recent trade data
- `GET /{exchange}/{symbol}/trades/range` - Historical trade data  
- Parameters: `limit`, `start_time`, `end_time` (from example)
- Response: JSON with trades array and metadata

#### Candle Data Router (`candles.py`) - **Implements `candle_repository_example.py`**
- `GET /{exchange}/{symbol}/candles/{timeframe}` - OHLCV candle data
- `GET /{exchange}/{symbol}/candles/{timeframe}/range` - Historical candles
- Parameters: `limit`, `start_time`, `end_time` (from example)
- Response: JSON with candles array and metadata

#### Timeseries Router (`timeseries.py`) - **Implements `timeseries_repository_example.py`**
- `GET /{exchange}/{symbol}/ohlcv` - OHLCV aggregation from trade data
- Parameters: `timeframe`, `start_time`, `end_time`, `limit` (from example)
- Response: JSON with aggregated OHLCV data

#### WebSocket Router (`websocket.py`) - **Implements `websocket_live_ohlcv_example.py`**
- `WS /ws/ohlcv` - Real-time OHLCV streaming
- Subscription format: `{"action": "subscribe", "exchange": "...", "symbol": "...", "timeframe": "...", "type": "ohlcv_live"}`
- Updates: Real-time OHLCV data with `is_final` flag

#### Exchange Catalog Router (`exchanges.py`)
- `GET /exchanges` - Available exchanges list
- `GET /exchanges/{exchange}/info` - Exchange information

#### Symbol Catalog Router (`symbols.py`) 
- `GET /{exchange}/symbols` - Available symbols for exchange
- `GET /{exchange}/{symbol}/info` - Symbol metadata

### 3. Data Models (`models/`)
**Pydantic models for request/response validation and OpenAPI documentation.**

#### Request Models (`requests.py`)
```python
class TimeRangeRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    limit: Optional[int] = 1000

class TradeQueryRequest(BaseModel):
    exchange: str
    symbol: str
    limit: Optional[int] = 100
    # READ-ONLY: No write operation models
```

#### Response Models (`responses.py`) 
```python
class TradesResponse(BaseModel):
    trades: List[OHLCVTrade]
    count: int
    exchange: str
    symbol: str

class CandlesResponse(BaseModel):
    candles: List[OHLCVCandle] 
    timeframe: str
    count: int
```

### 4. Dependencies (`dependencies/`)
**FastAPI dependency injection for database sessions and validation.**

#### Database Dependencies (`database.py`)
```python
async def get_read_only_trade_repository(exchange: str, symbol: str) -> TradeRepository:
    """Provide configured TradeRepository instance for READ-ONLY operations."""
    pass

async def get_read_only_candle_repository(exchange: str, symbol: str) -> CandleRepository:
    """Provide configured CandleRepository instance for READ-ONLY operations."""
    pass
```

## 🔄 Data Flow Architecture

### Read-Only Request Processing Flow
```
1. HTTP GET Request → FastAPI Router
2. Router → Pydantic Request Validation
3. Dependencies → fullon_ohlcv Repository Creation (READ-ONLY)
4. Repository → Database/TimescaleDB Query (READ-ONLY)
5. Database → Raw OHLCV Data Return (NO MODIFICATIONS)
6. Repository → Data Processing & Formatting
7. Router → Pydantic Response Validation
8. FastAPI → JSON HTTP Response
```

### Master API Integration Flow
```
1. Fullon Master Trading API Startup
2. Import get_all_routers from each fullon library
3. Mount routers with versioned, semantic prefixes:
   - /api/v1/market/ (fullon_ohlcv_api) - Historical market data
   - /api/v1/db/ (fullon_orm_api) - Persistent application data
   - /api/v1/cache/ (fullon_cache_api) - Real-time & temporary data
4. Generate unified OpenAPI documentation with organized tags
5. Centralized logging, monitoring, and error handling
```

## 📊 Database Integration

### fullon_ohlcv Dependency Pattern
```python
# Standard repository usage pattern:
from fullon_ohlcv import TradeRepository, CandleRepository

async with TradeRepository("binance", "BTC/USDT") as repo:
    trades = await repo.get_recent_trades(limit=100)
    
async with CandleRepository("binance", "ETH/USDT") as repo:
    candles = await repo.get_candles_in_range(start, end)
```

### Time-Series Optimization
- **TimescaleDB Integration**: Automatic hypertable creation for time-series data
- **UTC Timestamps**: All data stored and queried in UTC timezone
- **Efficient Range Queries**: Optimized for time-based data retrieval
- **Bulk Operations**: Batch processing for high-volume data import

## 🧪 Examples-Driven Testing Architecture

### **Primary Testing Strategy: Examples as Integration Tests**

**`examples/run_all.py` - Complete Testing Infrastructure**:
1. **Setup test database** with sample OHLCV data using fullon_ohlcv repositories
2. **Start API server** in test mode with isolated test database
3. **Run examples** as integration tests against live API endpoints
4. **Validate results** - all examples must work successfully
5. **Cleanup** - stop server, cleanup test data

```bash
# Examples-driven testing commands
python examples/run_all.py                          # All examples integration test
python examples/run_all.py --example trade_repository_example.py  # Individual endpoint test
python examples/run_all.py --setup-only            # Development testing environment
python examples/run_all.py --list                  # Show available example tests
```

### Test Organization
```
examples/                    # 📚 PRIMARY TESTING - Living API specification
├── run_all.py              # Complete integration testing infrastructure
├── trade_repository_example.py    # Trade endpoints integration test
├── candle_repository_example.py   # Candle endpoints integration test
├── timeseries_repository_example.py # Timeseries endpoints integration test
└── websocket_live_ohlcv_example.py  # WebSocket streaming integration test

tests/                       # 🔬 SECONDARY TESTING - Traditional unit tests
├── conftest.py              # Shared fixtures and configuration
├── test_main.py             # Integration tests for main components
├── unit/                    # Isolated component testing
│   ├── test_gateway.py      # Gateway class unit tests
│   ├── test_routers.py      # Router endpoint unit tests
│   └── test_models.py       # Pydantic model validation tests
└── integration/             # End-to-end workflow testing  
    ├── test_api_workflows.py # Complete API operation flows
    └── test_repository_integration.py # fullon_ohlcv integration tests
```

### Examples-Driven Development (EDD)
- **Examples First**: Examples define what API must implement
- **Examples as Tests**: Examples validate that implementation works
- **Integration Focus**: Complete workflows tested through examples
- **`examples/run_all.py`**: Primary test runner (must pass before commits)
- **Traditional TDD**: Secondary validation through unit tests

## 🚀 Development Workflow

### Setup and Development
```bash
# Project setup
make setup          # Install dependencies, setup pre-commit hooks

# Development server  
make dev           # Start development server with auto-reload

# Code quality
make format        # Format code with Black + Ruff
make lint         # Run linting checks
make test         # Run test suite
make check        # Run all quality checks

# Comprehensive validation
./run_test.py     # Full test suite (required before commits)
```

### Master API Integration Example
```python
# fullon_master_api/main.py
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

# Clear API structure:
# /api/v1/db/trades/           - Persistent trade records
# /api/v1/cache/trades/queue   - Real-time trade queue
# /api/v1/market/trades/       - Market trade data
# /docs                        - Combined documentation
```

### Ecosystem Architecture Benefits

**🎯 Semantic URL Structure**
- Clear separation between data types and operations
- Intuitive API discovery for developers
- Consistent versioning across all components

**📚 OpenAPI Documentation Organization**
```yaml
# Generated OpenAPI structure
paths:
  /api/v1/db/trades/:
    get:
      tags: ["Database"] 
      summary: "Get trade records from database"
      
  /api/v1/cache/trades/queue:
    get:
      tags: ["Cache"]
      summary: "Get trade queue status from Redis"
      
  /api/v1/market/trades/{exchange}/{symbol}:
    get:
      tags: ["Market Data"]
      summary: "Get historical trade data"
```

**🔄 Clean Component Integration**
- Each fullon library maintains independence
- No cross-dependencies between API components
- Easy to add/remove components from master API
- Simplified testing and deployment strategies

## 📈 Performance Considerations

### Time-Series Optimizations (READ-ONLY)
- **Pagination**: Large datasets split into manageable chunks for retrieval
- **Efficient Queries**: TimescaleDB-optimized time range read queries
- **Caching Strategy**: Configurable caching for frequently accessed read data
- **Async Operations**: Non-blocking I/O for high concurrency reads

### Scaling Patterns (READ-ONLY)
- **Connection Pooling**: Database connection optimization for read operations
- **Data Export**: Efficient bulk data export and analysis operations
- **Index Strategy**: Read-optimized database indexes for time-series queries
- **Memory Management**: Efficient handling of large time-series datasets for read operations

---

**This project structure enables a composable, high-performance OHLCV API gateway that integrates seamlessly into the broader fullon ecosystem while maintaining independence and reusability.** 🚀