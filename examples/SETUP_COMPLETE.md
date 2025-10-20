# ✅ Setup Complete - fullon_ohlcv_api Examples

## What's Fixed

All data filling now works correctly with the proper fullon pattern!

### Key Changes:

1. **Removed Binance** - Now uses kraken, bitmex, hyperliquid (matching fullon_ohlcv_service)
2. **Fixed Environment Loading** - Loads .env BEFORE any imports (critical!)
3. **Dual Database Pattern** - Creates both ORM and OHLCV test databases
4. **Proper Integration** - Uses demo_data.py for all database setup

## Usage

### Option 1: Run All Examples (Recommended)

```bash
cd /home/ingmar/code/fullon_ohlcv_api
poetry run python examples/run_all.py
```

This will:
1. ✅ Create test databases (ORM + OHLCV)
2. ✅ Install demo ORM data (exchanges, symbols, users)
3. ✅ Fill OHLCV data (trades, candles)
4. ✅ Start API server
5. ✅ Run all examples
6. ✅ Cleanup (drop test databases)

### Option 2: Manual Setup + Examples

```bash
# Setup (creates databases and fills data)
poetry run python examples/demo_data.py --setup

# Run individual examples
poetry run python examples/trade_repository_example.py
poetry run python examples/candle_repository_example.py

# Cleanup when done
poetry run python examples/demo_data.py --cleanup {base_name}
```

### Option 3: Setup and Keep Running

```bash
# Setup and start server (stays running)
poetry run python examples/run_all.py --setup-only

# In another terminal, run examples manually
poetry run python examples/trade_repository_example.py

# Cleanup when done
poetry run python examples/run_all.py --cleanup-only
```

## What Data Gets Created

### ORM Database (`*_test_orm`)
- **Exchanges**: kraken1, bitmex1, hyperliquid1
- **Symbols**:
  - kraken: BTC/USDC
  - bitmex: BTC/USD:BTC
  - hyperliquid: BTC/USDC:USDC
- **User**: admin@fullon (admin user)

### OHLCV Database (`*_test_ohlcv`)
- **Schemas**: kraken, bitmex, hyperliquid
- **Data per symbol**:
  - 150 trades (realistic price movements)
  - 72 candles (3 days of hourly OHLCV data)

## Architecture

```
run_all.py
    ↓
demo_data.py
    ├── create_dual_test_databases()
    │   ├── Create ORM database
    │   └── Create OHLCV database
    │
    ├── install_orm_schema()
    │   └── Initialize fullon_orm tables
    │
    ├── install_demo_orm_data()
    │   ├── Create exchanges (kraken, bitmex, hyperliquid)
    │   ├── Create symbols
    │   └── Create admin user
    │
    └── install_demo_ohlcv_data()
        └── fill_data_examples.py
            ├── Generate realistic trades
            ├── Generate realistic candles
            └── Save to OHLCV database
```

## Critical Pattern: Environment Loading Order

```python
# 1. Load .env FIRST (before ANY imports!)
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# 2. Set test database environment variables
import os
os.environ["DB_NAME"] = "test_orm_db"
os.environ["DB_OHLCV_NAME"] = "test_ohlcv_db"

# 3. NOW safe to import fullon modules
from fullon_ohlcv.repositories.ohlcv import TradeRepository
from fullon_orm import DatabaseContext
```

This order is **critical** - importing fullon modules before setting environment variables will cause connection errors!

## Troubleshooting

### "Connection refused" error

This usually means the test database doesn't exist. Solution:

```bash
# Use demo_data.py or run_all.py - they create databases first
poetry run python examples/demo_data.py --setup
```

### "Database already exists" error

Cleanup old test databases:

```bash
# List test databases
psql -h 10.237.48.188 -U fullon -d postgres -c "SELECT datname FROM pg_database WHERE datname LIKE '%test%'"

# Cleanup with demo_data.py
poetry run python examples/demo_data.py --cleanup {base_name}
```

### Examples fail to run

Make sure test databases exist:

```bash
# Check if databases exist
psql -h 10.237.48.188 -U fullon -d postgres -c "SELECT datname FROM pg_database WHERE datname LIKE '%test%'"

# If not, create them
poetry run python examples/demo_data.py --setup
```

## Files Overview

- **`demo_data.py`** - Main setup script (creates databases, installs data)
- **`fill_data_examples.py`** - Fills OHLCV data (called by demo_data.py)
- **`run_all.py`** - Complete test suite (setup + run examples + cleanup)
- **`README_DEMO_DATA.md`** - Detailed documentation
- **`SETUP_COMPLETE.md`** - This file

## Quick Test

Verify everything works:

```bash
cd /home/ingmar/code/fullon_ohlcv_api

# List available examples
poetry run python examples/run_all.py --list

# Run all examples (full integration test)
poetry run python examples/run_all.py
```

Expected output:
```
🧪 fullon_ohlcv_api Examples Test Suite
==================================================
🗄️  Setting up test databases with demo data...
📊 Creating dual test databases...
   - ORM: fullon_ohlcv_test_orm
   - OHLCV: fullon_ohlcv_test_ohlcv
✅ Test databases setup complete with demo data
🚀 Starting API server...
✅ API server started on 127.0.0.1:9000

📚 Running 4 example(s)...
🧪 Running trade_repository_example.py...
✅ trade_repository_example.py completed successfully
...
📊 Results: 4/4 example(s) passed
🎉 All examples passed!
```

## Next Steps

1. **Run examples**: `poetry run python examples/run_all.py`
2. **Develop features**: Use `--setup-only` to keep server running
3. **Integration testing**: Use in CI/CD pipelines

## Matching fullon_ohlcv_service

This implementation **exactly matches** `fullon_ohlcv_service/examples/demo_data.py`:

✅ Same exchanges (kraken, bitmex, hyperliquid)
✅ Same symbols (BTC/USDC, BTC/USD:BTC, BTC/USDC:USDC)
✅ Same dual database pattern (ORM + OHLCV)
✅ Same environment loading pattern
✅ Same demo data installation flow

No binance! 🎉
