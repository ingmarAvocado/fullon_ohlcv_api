# 🚀 fullon_ohlcv_api

[![Tests](https://github.com/ingmarAvocado/fullon_ohlcv_api/workflows/Tests/badge.svg)](https://github.com/ingmarAvocado/fullon_ohlcv_api/actions)
[![Coverage](https://codecov.io/gh/ingmarAvocado/fullon_ohlcv_api/branch/main/graph/badge.svg)](https://codecov.io/gh/ingmarAvocado/fullon_ohlcv_api)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

**FastAPI Gateway for fullon_ohlcv with LRRS-compliant architecture for read-only market data operations**

A focused, LRRS-compliant (Little, Responsible, Reusable, Separate) library that provides a complete **read-only** REST API gateway for OHLCV (Open, High, Low, Close, Volume) market data operations. Every fullon_ohlcv **read operation** is exposed via secure, high-performance HTTP endpoints.

**🔍 READ-ONLY API**: This library **only** exposes data retrieval operations. No updates, inserts, or write operations are in scope.

## ✨ Features

- **📊 Complete OHLCV Read Coverage** - Every fullon_ohlcv read operation exposed via REST API
- **⏰ Time-Series Optimized** - Built for efficient historical and real-time market data retrieval
- **⚡ High Performance** - uvloop optimization, async throughout, TimescaleDB read integration
- **🧪 100% Test Coverage** - TDD-driven development with comprehensive tests
- **📚 Auto-Generated Docs** - Interactive OpenAPI/Swagger documentation
- **🐳 Docker Ready** - Production-ready containerization
- **🔄 CI/CD Pipeline** - Automated testing, linting, and deployment

## 🏗️ Architecture

### LRRS Compliance

Following LRRS principles for maximum ecosystem integration:

- **Little**: Single purpose - READ-ONLY OHLCV market data API gateway
- **Responsible**: Clear separation between routing, validation, and read-only data operations  
- **Reusable**: Works with any fullon_ohlcv deployment, composable into master_api
- **Separate**: Zero coupling to other systems beyond fullon_ohlcv + fullon_log

### Fullon Ecosystem Integration

This library is designed to integrate seamlessly with the broader fullon trading ecosystem:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fullon Master Trading API                   │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  📊 Market Data │  🗄️ Database    │  ⚡ Cache & Real-time       │
│                 │                 │                             │
│ fullon_ohlcv_api│ fullon_orm_api  │ fullon_cache_api            │
│                 │                 │                             │
│ Historical data │ Persistent      │ Live feeds &                │
│ Time-series     │ Trade records   │ Real-time queues            │
│ OHLCV analysis  │ Positions       │ Price alerts                │
│                 │ Portfolio data  │ Event streaming             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### API Structure Benefits

**🎯 Clear Separation of Concerns**
- `/api/v1/market/` - Historical & analytical data (READ-ONLY)
- `/api/v1/db/` - Persistent application data (CRUD operations)  
- `/api/v1/cache/` - Real-time & temporary data (pub/sub, queues)

**📚 Documentation Benefits**
- Combined Swagger/OpenAPI docs with organized tags
- Clear endpoint categorization
- Consistent versioning across all modules

```
fullon_ohlcv_api/
├── src/fullon_ohlcv_api/
│   ├── dependencies/         # Read-only database session management
│   ├── routers/             # Read-only OHLCV endpoints (trades, candles, exchanges)
│   ├── models/              # Pydantic request/response models
│   └── gateway.py           # Main FastAPI application
├── examples/                # Working code examples
├── tests/                   # Comprehensive test suite
└── docs/                    # Additional documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Poetry for dependency management
- PostgreSQL + TimescaleDB for OHLCV data storage
- Access to fullon_ohlcv package

### Installation

```bash
# Clone the repository
git clone https://github.com/ingmarAvocado/fullon_ohlcv_api.git
cd fullon_ohlcv_api

# Setup development environment
make setup

# Configure database connection
cp .env.example .env
# Edit .env with your database settings
```

### Configuration (.env)

This project (and fullon_ohlcv) uses individual DB_* environment variables.

```bash
# Database Configuration
DB_HOST=10.206.35.109
DB_PORT=5432
DB_USER=fullon
DB_PASSWORD=fullon
DB_OHLCV_NAME=fullon_ohlcv2
DB_TEST_NAME=fullon_ohlcv2_test

# API Server
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Run the API

```bash
# Development server
make dev

# Production server  
make prod

# View API documentation
# Open http://localhost:8000/docs
```

## 📖 Usage Examples

### Trade Data Operations

```python
import httpx
from datetime import datetime, timezone, timedelta

# Get recent trades
response = httpx.get("http://localhost:8000/api/trades/binance/BTC-USDT?limit=100")
trades = response.json()

# Get historical trades
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=24)

response = httpx.get(
    f"http://localhost:8000/api/trades/binance/BTC-USDT/range"
    f"?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
)
historical_trades = response.json()
```

### Candle/OHLCV Data Operations

```python
# Get 1-hour candles
response = httpx.get("http://localhost:8000/api/candles/binance/ETH-USDT/1h?limit=24")
hourly_candles = response.json()

# Get daily OHLCV for last month
response = httpx.get("http://localhost:8000/api/candles/binance/BTC-USDT/1d/range"
                    f"?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}")
daily_ohlcv = response.json()
```

### Exchange and Symbol Information

```python
# Get available exchanges
response = httpx.get("http://localhost:8000/api/exchanges")
exchanges = response.json()

# Get symbols for an exchange  
response = httpx.get("http://localhost:8000/api/exchanges/binance/symbols")
symbols = response.json()
```

### Trade Statistics and Analysis

```python
# Get trade statistics
response = httpx.get("http://localhost:8000/api/trades/binance/BTC-USDT/stats?hours=24")
stats = response.json()

# Get trade data export
response = httpx.get("http://localhost:8000/api/trades/binance/BTC-USDT/export?format=csv")
csv_data = response.text

# Analyze candle patterns
response = httpx.get("http://localhost:8000/api/candles/binance/BTC-USDT/1h/analysis")
analysis = response.json()
```

## 🔌 Library Usage (Master API Integration)

### Direct Gateway Usage

```python
from fullon_ohlcv_api import FullonOhlcvGateway

# Create gateway instance
gateway = FullonOhlcvGateway(
    title="Master API - OHLCV Module",
    prefix="/ohlcv"  # All routes prefixed with /ohlcv
)

# Get the FastAPI app
app = gateway.get_app()
```

### Router Composition for Master API

```python
from fastapi import FastAPI
from fullon_ohlcv_api import get_all_routers

# Create main FastAPI app
app = FastAPI(title="Fullon Master API", version="1.0.0")

# Mount OHLCV routers
for router in get_all_routers():
    app.include_router(router, prefix="/ohlcv", tags=["OHLCV"])
    
# Routes available under /ohlcv/ prefix
# /ohlcv/trades/{exchange}/{symbol}
# /ohlcv/candles/{exchange}/{symbol}/{timeframe}
# /ohlcv/exchanges
# etc.
```

### Multiple Library Composition

```python
from fastapi import FastAPI

# Fullon Master Trading API with complete ecosystem
app = FastAPI(title="Fullon Master Trading API", version="1.0.0")

# Database operations
from fullon_orm_api import get_all_routers as get_orm_routers
for router in get_orm_routers():
    app.include_router(router, prefix="/api/v1/db", tags=["Database"])

# Cache operations  
from fullon_cache_api import get_all_routers as get_cache_routers
for router in get_cache_routers():
    app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])

# Market data operations
from fullon_ohlcv_api import get_all_routers as get_ohlcv_routers
for router in get_ohlcv_routers():
    app.include_router(router, prefix="/api/v1/market", tags=["Market Data"])

# Results in clean API separation:
# /api/v1/db/trades/              - Persistent trade records
# /api/v1/cache/trades/queue      - Real-time trade queue
# /api/v1/market/trades/          - Historical market data
# /docs                           - Combined documentation
```

## 📊 API Endpoints (READ-ONLY)

### Market Data Endpoints (Standalone)

When used standalone, endpoints are accessible directly:
- **GET** `/api/trades/{exchange}/{symbol}` - Get recent trades
- **GET** `/api/trades/{exchange}/{symbol}/range` - Get trades in time range  
- **GET** `/api/candles/{exchange}/{symbol}/{timeframe}` - Get recent candles
- **GET** `/api/exchanges` - List available exchanges

### Master API Integration (Recommended)

When integrated into the master API, endpoints are prefixed with `/api/v1/market`:

**🏢 Market Data Operations** (`/api/v1/market/`)
- **GET** `/api/v1/market/trades/{exchange}/{symbol}` - Historical trade data
- **GET** `/api/v1/market/trades/{exchange}/{symbol}/range` - Time-range trade queries
- **GET** `/api/v1/market/trades/{exchange}/{symbol}/stats` - Trade statistics
- **GET** `/api/v1/market/trades/{exchange}/{symbol}/export` - Export trade data
- **GET** `/api/v1/market/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles
- **GET** `/api/v1/market/candles/{exchange}/{symbol}/{timeframe}/range` - Historical candles
- **GET** `/api/v1/market/exchanges` - Available exchanges catalog
- **GET** `/api/v1/market/exchanges/{exchange}/symbols` - Exchange symbols

**🗄️ Database Operations** (`/api/v1/db/`) - *via fullon_orm_api*
- **GET** `/api/v1/db/trades/` - Persistent trade records  
- **POST** `/api/v1/db/trades/` - Store trade records
- **GET** `/api/v1/db/positions/` - Trading positions

**⚡ Cache Operations** (`/api/v1/cache/`) - *via fullon_cache_api*  
- **GET** `/api/v1/cache/trades/queue` - Real-time trade queue
- **GET** `/api/v1/cache/prices/live` - Live price feeds
- **POST** `/api/v1/cache/alerts/` - Price alert management

### System Endpoints

- **GET** `/health` - Health check endpoint
- **GET** `/` - API information and links  
- **GET** `/docs` - Interactive Swagger documentation (combined when using master API)
- **GET** `/redoc` - ReDoc documentation

## 🧪 Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run comprehensive test suite (required before PR)
./run_test.py

# Run specific test category
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
```

## 🛠️ Development

```bash
# Install dependencies
make install

# Format code
make format

# Run linting
make lint

# Run all checks
make check

# Start development server with auto-reload
make dev
```

## 📈 Performance Features

### Time-Series Optimizations (READ-ONLY)
- **TimescaleDB Integration**: Optimized read queries for time-series data
- **Data Export**: Efficient bulk data export and analysis operations
- **Pagination**: Configurable limits for large result sets
- **Range Queries**: Efficient time-based data retrieval

### Async Architecture (READ-ONLY)
- **Async Throughout**: All read operations are non-blocking
- **Connection Pooling**: Optimized database connections for reads
- **Concurrent Processing**: Multiple read requests handled simultaneously
- **Memory Efficient**: Streaming for large datasets retrieval

## 📊 Data Models

### OHLCV Trade Model
```python
{
    "timestamp": "2024-01-01T12:00:00Z",
    "price": 45000.50,
    "volume": 0.1,
    "side": "buy"
}
```

### OHLCV Candle Model
```python
{
    "timestamp": "2024-01-01T12:00:00Z",
    "open": 45000.00,
    "high": 45100.00,
    "low": 44900.00,
    "close": 45050.00,
    "volume": 10.5,
    "closed": true,
    "timeframe": "1h"
}
```

## 🐳 Deployment

### Docker

```bash
# Build image
make docker-build

# Run container
make docker-run
```

### Production Deployment

```bash
# Install production dependencies only
poetry install --no-dev

# Ensure DB_* variables are set in the environment
# Then run with a production ASGI server
poetry run uvicorn src.fullon_ohlcv_api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following TDD principles
4. Ensure all tests pass: `./run_test.py`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow TDD - write tests first
- Maintain 100% test coverage
- Use `./run_test.py` before any commit
- Follow existing code style (Black + Ruff)
- Update documentation for new features
- All timestamps must be UTC timezone-aware

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [fullon_ohlcv](https://github.com/ingmarAvocado/fullon_ohlcv) market data library
- Uses [FastAPI](https://fastapi.tiangolo.com/) for high-performance async API
- Follows LRRS architectural principles for maximum reusability
- Optimized for [TimescaleDB](https://www.timescale.com/) time-series performance

## 📞 Support

- 📚 Check the [CLAUDE.md](CLAUDE.md) for development assistance  
- 📋 See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for architecture details
- 🐛 Report issues on [GitHub Issues](https://github.com/ingmarAvocado/fullon_ohlcv_api/issues)
- 💬 Discussion on [GitHub Discussions](https://github.com/ingmarAvocado/fullon_ohlcv_api/discussions)

---

**Built with ❤️ using LRRS principles for maximum reusability and time-series performance** 📊🚀
