# Demo Data Setup for fullon_ohlcv_api

This guide explains how to set up and use demo data for fullon_ohlcv_api examples.

## Overview

The demo data setup creates an isolated test environment with:
- **ORM Database**: Contains exchanges, symbols, and user data (from fullon_orm)
- **OHLCV Database**: Contains trade and candle market data (from fullon_ohlcv)

This follows the same pattern as `fullon_ohlcv_service/examples/demo_data.py`.

## Quick Start

### 1. Setup Demo Environment

```bash
# Create test databases and install demo data
cd /home/ingmar/code/fullon_ohlcv_api
poetry run python examples/demo_data.py --setup
```

This will:
1. Create two test databases: `{base_name}_orm` and `{base_name}_ohlcv`
2. Install fullon_orm schema (exchanges, symbols, users)
3. Install demo ORM data (binance, kraken, bitmex exchanges with BTC/USDT, ETH/USDT, BTC/USD symbols)
4. Fill OHLCV data (realistic trades and candles for testing)

### 2. Run Examples

After setup, you can run the API examples against the demo data:

```bash
# Run individual examples
poetry run python examples/trade_repository_example.py
poetry run python examples/candle_repository_example.py
poetry run python examples/timeseries_repository_example.py

# Or run all examples
poetry run python examples/demo_data.py --examples-only
```

### 3. Cleanup

```bash
# Cleanup test databases when done
poetry run python examples/demo_data.py --cleanup {base_name}

# The base_name will be shown in the setup output
# Example: fullon_ohlcv_test_abc123de
```

## All-in-One Workflow

Run setup, examples, and cleanup in one command:

```bash
poetry run python examples/demo_data.py --run-all
```

This is useful for CI/CD and quick validation.

## Database Structure

### ORM Database (`{base_name}_orm`)
- **Tables**: users, exchanges, cat_exchanges, symbols, feeds, bots, strategies
- **Demo Data**:
  - User: admin@fullon (UID: 1)
  - Exchanges: kraken1, bitmex1, hyperliquid1
  - Symbols (matching fullon_ohlcv_service):
    - kraken: BTC/USDC
    - bitmex: BTC/USD:BTC
    - hyperliquid: BTC/USDC:USDC

### OHLCV Database (`{base_name}_ohlcv`)
- **Schemas**: kraken, bitmex, hyperliquid
- **Tables** (per symbol):
  - `{exchange}.{symbol}_trades` - Trade data (TimescaleDB hypertable)
  - `{exchange}.{symbol}_candles` - Candle data (TimescaleDB hypertable)
- **Demo Data** (matching fullon_ohlcv_service):
  - 150 trades per symbol (BTC/USDC, BTC/USD:BTC, BTC/USDC:USDC)
  - 72 candles per symbol (3 days of hourly candles)

## Environment Variables

The demo data setup uses the following environment variables from `.env`:

```bash
# Database Connection
DB_HOST=10.237.48.188
DB_PORT=5432
DB_USER=fullon
DB_PASSWORD=fullon

# Database Names (will be modified for test)
DB_NAME=fullon_orm2              # Base ORM database name
DB_OHLCV_NAME=fullon_ohlcv2      # Base OHLCV database name
DB_TEST_NAME=fullon_ohlcv_test   # Test database prefix

# Admin User
ADMIN_MAIL=admin@fullon

# Redis (optional, for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Files

- `demo_data.py` - Main demo data setup script
- `fill_data_examples.py` - OHLCV data filler (generates realistic trades/candles)
- `README_DEMO_DATA.md` - This file

## Architecture

```
┌─────────────────────────────────────────┐
│       demo_data.py (Main Script)        │
├─────────────────────────────────────────┤
│                                         │
│  1. Create dual test databases          │
│     - {base}_orm                        │
│     - {base}_ohlcv                      │
│                                         │
│  2. Install fullon_orm schema           │
│     - Tables: users, exchanges, symbols │
│                                         │
│  3. Install demo ORM data               │
│     - Admin user (admin@fullon)         │
│     - 3 exchanges (binance, kraken,     │
│       bitmex)                           │
│     - 4 symbols across exchanges        │
│                                         │
│  4. Fill OHLCV data                     │
│     (via fill_data_examples.py)         │
│     - Generate realistic trades         │
│     - Generate realistic candles        │
│     - Save to OHLCV database            │
│                                         │
└─────────────────────────────────────────┘
```

## Comparison with fullon_ohlcv_service

This implementation follows the same pattern as `fullon_ohlcv_service/examples/demo_data.py`:

**Similarities:**
- Dual database setup (ORM + OHLCV)
- Demo ORM data installation (exchanges, symbols, users)
- Isolated test environment
- CLI interface (--setup, --cleanup, --run-all)

**Differences:**
- `fullon_ohlcv_service`: Focuses on service daemon testing
- `fullon_ohlcv_api`: Focuses on REST API endpoint testing
- Data filling uses `fill_data_examples.py` instead of service collectors

## Troubleshooting

### Connection Refused Error

If you see "Connection refused" when running the data filler:

1. Check database connection:
   ```bash
   psql -h 10.237.48.188 -U fullon -d postgres -c "SELECT 1"
   ```

2. Verify environment variables in `.env`:
   ```bash
   grep DB_ .env
   ```

3. Make sure the database host is accessible:
   ```bash
   ping 10.237.48.188
   ```

### Schema Already Exists

If you get "schema already exists" errors, cleanup the test databases:

```bash
poetry run python examples/demo_data.py --cleanup {base_name}
```

### Import Errors

Make sure you're running within the poetry environment:

```bash
poetry install
poetry run python examples/demo_data.py --setup
```

## Next Steps

After setting up demo data, you can:

1. **Test API Endpoints**: Start the API server and test endpoints with demo data
2. **Run Examples**: Execute the example scripts to see working code
3. **Develop Features**: Use demo data for developing new API features
4. **Integration Testing**: Use `--run-all` for CI/CD pipelines

## Related Documentation

- `CLAUDE.md` - Project development guidelines
- `examples/fill_data_examples.py` - Data generation implementation
- `fullon_ohlcv_service/examples/demo_data.py` - Reference implementation
