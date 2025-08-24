# 🏗️ fullon_ohlcv_api Project Structure

**LRRS-Compliant OHLCV Market Data API Gateway Architecture**

## 📋 Project Overview

fullon_ohlcv_api is a composable FastAPI gateway library that exposes **read-only** OHLCV (Open, High, Low, Close, Volume) market data operations as secure REST endpoints. It follows LRRS (Little, Responsible, Reusable, Separate) principles and integrates seamlessly into master_api alongside other fullon libraries.

**🔍 READ-ONLY API**: This library **only** exposes data retrieval operations. No updates, inserts, or write operations are in scope.

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
│       │   ├── requests.py     # 📥 API request models
│       │   └── responses.py    # 📤 API response models
│       │
│       └── routers/           # 🛣️ FastAPI endpoint routers
│           ├── __init__.py
│           ├── trades.py       # 💹 Trade data endpoints
│           ├── candles.py      # 🕯️ Candle/OHLCV data endpoints
│           ├── exchanges.py    # 🏢 Exchange catalog endpoints
│           └── symbols.py      # 🔤 Symbol catalog endpoints
│
├── examples/                  # 📚 Working code examples
│   ├── basic_usage.py         # 🚀 Simple OHLCV API usage
│   └── library_usage.py       # 🏗️ Master API composition patterns
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
    └── (additional docs)
```

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

### 2. Router Architecture (`routers/`)
**Modular endpoint organization by OHLCV operation type.**

#### Trade Data Router (`trades.py`) - **READ-ONLY**
- `GET /{exchange}/{symbol}/trades` - Recent trade data
- `GET /{exchange}/{symbol}/trades/range` - Historical trade data
- `GET /{exchange}/{symbol}/trades/stats` - Trade statistics
- `GET /{exchange}/{symbol}/trades/export` - Data export functionality

#### Candle Data Router (`candles.py`) - **READ-ONLY**
- `GET /{exchange}/{symbol}/candles/{timeframe}` - OHLCV candle data
- `GET /{exchange}/{symbol}/candles/{timeframe}/range` - Historical candles
- `GET /{exchange}/{symbol}/ohlcv` - Latest OHLCV summary
- `GET /{exchange}/{symbol}/candles/analysis` - Candle analysis

#### Exchange Catalog Router (`exchanges.py`)
- `GET /exchanges` - Available exchanges list
- `GET /exchanges/{exchange}/info` - Exchange information
- `GET /exchanges/{exchange}/status` - Exchange connectivity status

#### Symbol Catalog Router (`symbols.py`)
- `GET /{exchange}/symbols` - Available symbols for exchange  
- `GET /{exchange}/{symbol}/info` - Symbol metadata
- `GET /symbols/search` - Symbol search functionality

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
1. Master API Startup
2. Import fullon_ohlcv_api.get_all_routers()
3. Mount Routers with /ohlcv prefix
4. Compose with other fullon APIs
5. Single unified API documentation
6. Centralized logging and monitoring
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

## 🧪 Testing Architecture

### Test Organization
```
tests/
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

### Test-Driven Development (TDD)
- **Tests First**: Write tests before implementation
- **100% Coverage**: All code must have test coverage
- **`./run_test.py`**: Comprehensive test runner (must pass before commits)
- **Async Testing**: All tests use pytest-asyncio for async operations

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
# master_api/main.py
from fastapi import FastAPI
from fullon_ohlcv_api import get_all_routers as ohlcv_routers
from fullon_orm_api import get_all_routers as orm_routers

app = FastAPI(title="Fullon Master API")

# Compose OHLCV API
for router in ohlcv_routers():
    app.include_router(router, prefix="/ohlcv", tags=["OHLCV"])

# Compose ORM API  
for router in orm_routers():
    app.include_router(router, prefix="/orm", tags=["ORM"])

# Result: Unified API with /ohlcv/* and /orm/* endpoints
```

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