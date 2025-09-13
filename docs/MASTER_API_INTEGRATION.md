# 🚀 Master API Integration Guide

**How to integrate fullon_ohlcv_api into the Fullon Master Trading API**

## 📋 Overview

This guide explains how to integrate the `fullon_ohlcv_api` library into a master trading API that combines multiple fullon components. The integration follows LRRS principles, making each component composable and focused on its specific responsibility.

## 🏗️ Architecture Integration

The fullon_ohlcv_api is designed as a **composable library** that provides market data endpoints alongside other fullon services:

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
```

## 🔧 Installation & Dependencies

### 1. Add to Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
fullon-ohlcv-api = {git = "https://github.com/ingmarAvocado/fullon_ohlcv_api.git", branch = "main"}
fullon-orm-api = {git = "https://github.com/ingmarAvocado/fullon_orm_api.git", branch = "main"}  
fullon-cache-api = {git = "https://github.com/ingmarAvocado/fullon_cache_api.git", branch = "main"}
```

### 2. Environment Configuration

```bash
# Market Data (OHLCV) - TimescaleDB
DB_HOST=10.206.35.109
DB_PORT=5432
DB_USER=fullon
DB_PASSWORD=fullon
DB_OHLCV_NAME=fullon_ohlcv2
DB_TEST_NAME=fullon_ohlcv2_test

# Application Data (ORM)
DB_APP_NAME=fullon_app

# Cache/Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="Fullon Master Trading API"
API_VERSION="1.0.0"

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=production
LOG_CONSOLE=true
```

## 🎯 Master API Implementation

### Complete Integration Example

```python
# main.py - Master API Server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import all fullon API components
from fullon_ohlcv_api import get_all_routers as get_ohlcv_routers
from fullon_orm_api import get_all_routers as get_orm_routers  
from fullon_cache_api import get_all_routers as get_cache_routers

# Logging
from fullon_log import get_component_logger
logger = get_component_logger("fullon.master_api")

def create_master_app() -> FastAPI:
    """Create the complete Fullon Master Trading API"""
    
    app = FastAPI(
        title="Fullon Master Trading API",
        version="1.0.0",
        description="Comprehensive trading API with market data, persistence, and caching",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc"
    )
    
    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Market Data Operations (OHLCV)
    logger.info("Loading market data routers...")
    for router in get_ohlcv_routers():
        app.include_router(
            router, 
            prefix="/api/v1/market", 
            tags=["Market Data"]
        )
    
    # Database Operations (ORM)  
    logger.info("Loading database routers...")
    for router in get_orm_routers():
        app.include_router(
            router, 
            prefix="/api/v1/db", 
            tags=["Database"]
        )
    
    # Cache Operations (Redis/Real-time)
    logger.info("Loading cache routers...")
    for router in get_cache_routers():
        app.include_router(
            router, 
            prefix="/api/v1/cache", 
            tags=["Cache"]
        )
    
    # Health Check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "fullon_master_api"}
    
    logger.info("Master API initialized successfully")
    return app

# Create the app
app = create_master_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

## 📊 Available Endpoints

### Market Data Endpoints (`/api/v1/market/`)

**Trade Data**:
- `GET /api/v1/market/trades/{exchange}/{symbol}` - Recent trades
- `GET /api/v1/market/trades/{exchange}/{symbol}/range` - Historical trades

**OHLCV Candles**:
- `GET /api/v1/market/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles  
- `GET /api/v1/market/candles/{exchange}/{symbol}/{timeframe}/range` - Historical candles

**Time-Series Aggregation**:
- `GET /api/v1/market/timeseries/{exchange}/{symbol}/ohlcv` - OHLCV from trades

**Real-Time Streaming**:
- `WS /api/v1/market/ws/ohlcv` - Live OHLCV WebSocket feed

**Metadata**:
- `GET /api/v1/market/exchanges` - Available exchanges
- `GET /api/v1/market/symbols/{exchange}` - Available symbols

### Database Endpoints (`/api/v1/db/`)
*Provided by fullon_orm_api - user data, positions, orders, etc.*

### Cache Endpoints (`/api/v1/cache/`)
*Provided by fullon_cache_api - real-time feeds, alerts, temporary data*

## 🔍 Usage Examples

### Market Data Integration

```python
# Example: Complete trading dashboard data fetching
import httpx
import asyncio

async def fetch_dashboard_data():
    async with httpx.AsyncClient() as client:
        # Market data (OHLCV API)
        btc_candles = await client.get("/api/v1/market/candles/binance/BTC/USDT/1h")
        eth_trades = await client.get("/api/v1/market/trades/coinbase/ETH/USD?limit=100")
        
        # User data (ORM API)  
        user_positions = await client.get("/api/v1/db/positions/user123")
        open_orders = await client.get("/api/v1/db/orders/user123?status=open")
        
        # Real-time data (Cache API)
        price_alerts = await client.get("/api/v1/cache/alerts/user123")
        live_prices = await client.get("/api/v1/cache/prices/live")
        
    return {
        "market_data": {
            "btc_candles": btc_candles.json(),
            "eth_trades": eth_trades.json()
        },
        "user_data": {
            "positions": user_positions.json(),
            "orders": open_orders.json()
        },
        "real_time": {
            "alerts": price_alerts.json(),
            "prices": live_prices.json()
        }
    }
```

### WebSocket Integration

```python
# Example: Real-time market data subscription
import asyncio
import websockets
import json

async def subscribe_to_market_data():
    uri = "ws://localhost:8000/api/v1/market/ws/ohlcv"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to BTC/USDT 1-minute OHLCV
        subscription = {
            "action": "subscribe",
            "exchange": "binance",
            "symbol": "BTC/USDT", 
            "timeframe": "1m",
            "type": "ohlcv_live"
        }
        
        await websocket.send(json.dumps(subscription))
        
        # Listen for real-time OHLCV updates
        async for message in websocket:
            data = json.loads(message)
            print(f"Live OHLCV: {data}")

# Run the subscription
asyncio.run(subscribe_to_market_data())
```

## 🚀 Deployment Configuration

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  fullon-master-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Database connections
      - DB_HOST=timescaledb
      - DB_OHLCV_NAME=fullon_ohlcv2
      - DB_APP_NAME=fullon_app
      
      # Redis connection  
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      
      # API configuration
      - API_HOST=0.0.0.0
      - API_PORT=8000
    depends_on:
      - timescaledb
      - redis
      - postgres
    
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      - POSTGRES_DB=fullon_ohlcv2
      - POSTGRES_USER=fullon
      - POSTGRES_PASSWORD=fullon
    volumes:
      - timescale_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=fullon_app  
      - POSTGRES_USER=fullon
      - POSTGRES_PASSWORD=fullon
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5434:5432"
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  timescale_data:
  postgres_data: 
  redis_data:
```

### Production Environment

```python
# production.py - Production configuration
import os
from main import create_master_app
import uvicorn

app = create_master_app()

if __name__ == "__main__":
    uvicorn.run(
        "production:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=4,
        loop="uvloop",
        http="httptools"
    )
```

## 🧪 Testing the Integration

### Complete Integration Test

```python
# test_master_api.py
import pytest
import httpx
from main import create_master_app

@pytest.fixture
def app():
    return create_master_app()

@pytest.mark.asyncio
async def test_complete_api_integration(app):
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Test market data endpoints
        market_response = await client.get("/api/v1/market/exchanges")
        assert market_response.status_code == 200
        
        # Test database endpoints
        db_response = await client.get("/api/v1/db/health")
        assert db_response.status_code == 200
        
        # Test cache endpoints  
        cache_response = await client.get("/api/v1/cache/health")
        assert cache_response.status_code == 200
        
        # Test health check
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["service"] == "fullon_master_api"
```

### Run Integration Tests

```bash
# Start test databases
docker-compose up timescaledb postgres redis -d

# Run complete test suite
python -m pytest test_master_api.py -v

# Test with examples
cd fullon_ohlcv_api && python examples/run_all.py --base-url http://localhost:8000/api/v1/market
```

## 🔄 Development Workflow

### 1. Local Development

```bash
# Start all dependencies
docker-compose up -d

# Start master API in development mode
python main.py

# API available at:
# - Swagger UI: http://localhost:8000/api/v1/docs
# - ReDoc: http://localhost:8000/api/v1/redoc
# - Health: http://localhost:8000/health
```

### 2. Component Development

```bash
# Work on individual components in isolation
cd fullon_ohlcv_api && make dev    # Market data API
cd fullon_orm_api && make dev      # Database API  
cd fullon_cache_api && make dev    # Cache API

# Then integrate into master API
```

### 3. Testing Strategy

```bash
# Test individual components
python examples/run_all.py                    # OHLCV API tests
python fullon_orm_api/examples/run_all.py     # ORM API tests
python fullon_cache_api/examples/run_all.py   # Cache API tests

# Test complete integration
python -m pytest test_master_api.py -v       # Master API tests
```

## 🎯 Best Practices

### 1. Component Boundaries
- **Market Data** (`/market/`): Historical OHLCV, trades, time-series analysis
- **Database** (`/db/`): User data, positions, orders, application state  
- **Cache** (`/cache/`): Real-time feeds, alerts, temporary data, pub/sub

### 2. Error Handling
```python
# Consistent error handling across components
from fastapi import HTTPException

# Component-specific errors with clear prefixes
raise HTTPException(status_code=404, detail="MARKET: Exchange not found")
raise HTTPException(status_code=404, detail="DB: User not found") 
raise HTTPException(status_code=404, detail="CACHE: Alert not found")
```

### 3. Logging Strategy
```python
# Component-specific loggers
from fullon_log import get_component_logger

market_logger = get_component_logger("fullon.master_api.market")
db_logger = get_component_logger("fullon.master_api.db") 
cache_logger = get_component_logger("fullon.master_api.cache")
```

### 4. Performance Optimization
```python
# Use uvloop for better async performance
from fullon_ohlcv.utils import install_uvloop

def main():
    install_uvloop()  # Call before uvicorn.run()
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

## 🔒 Security Considerations

### 1. API Authentication
```python
# Add authentication middleware to master API
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Implement your authentication logic
    if not validate_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Apply to protected endpoints
@app.get("/api/v1/market/trades/{exchange}/{symbol}")
async def get_trades(token: str = Depends(verify_token)):
    # Protected endpoint logic
    pass
```

### 2. Rate Limiting
```python
# Add rate limiting for API protection
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/market/trades/{exchange}/{symbol}")
@limiter.limit("100/minute")
async def get_trades(request: Request):
    # Rate-limited endpoint
    pass
```

## 📚 Additional Resources

- **OHLCV API Examples**: `fullon_ohlcv_api/examples/` - Working API usage examples
- **Component Documentation**: Each component has detailed documentation in its repository
- **Deployment Examples**: Docker and Kubernetes configurations available
- **Performance Tuning**: Database optimization and caching strategies

---

**The master API provides a unified interface to all fullon trading components, enabling comprehensive trading applications with market data, persistence, and real-time capabilities.** 🚀