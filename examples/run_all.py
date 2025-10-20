#!/usr/bin/env python3
"""
Run All Examples - fullon_ohlcv_api

Sets up test database, starts API server, runs all examples, then cleans up.
Mirrors the fullon_ohlcv examples pattern.

CRITICAL: This script sets environment variables BEFORE importing fullon modules.
"""

import argparse
import asyncio
import os
import signal
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# CRITICAL: Load .env FIRST, before ANY fullon imports
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not available")
except Exception as e:
    print(f"⚠️  Could not load .env: {e}")

# CRITICAL: Set test database names BEFORE importing fullon modules
# This is done in __init__ of ExampleTestRunner, but we need to ensure
# the pattern is followed throughout

# NOW safe to import fullon modules (but we'll delay until after env setup)
# Note: install_uvloop will be called at the end of main()

logger = None  # Will be initialized after environment is set


class ExampleTestRunner:
    """
    Example test runner that sets up test environment and runs examples.

    Follows fullon_ohlcv pattern:
    1. Setup test database
    2. Populate with test data
    3. Start API server
    4. Run examples
    5. Cleanup
    """

    def __init__(self):
        # Environment already loaded at module level
        self.api_process = None

        # Database names (dual database pattern) - SET THESE FIRST!
        self.test_db_base = os.getenv("DB_TEST_NAME", "fullon_ohlcv_test").replace("_test", "")
        self.test_db_orm = f"{self.test_db_base}_test_orm"
        self.test_db_ohlcv = f"{self.test_db_base}_test_ohlcv"

        # CRITICAL: Set environment variables BEFORE any fullon imports
        os.environ["DB_NAME"] = self.test_db_orm
        os.environ["DB_OHLCV_NAME"] = self.test_db_ohlcv
        # fullon_ohlcv uses DB_TEST_NAME for test mode
        os.environ["DB_TEST_NAME"] = self.test_db_ohlcv

        # Now safe to import and initialize logger
        global logger
        if logger is None:
            from fullon_log import get_component_logger
            logger = get_component_logger("fullon.examples.run_all")
        self.logger = logger

        self.api_process = None
        # Examples configuration
        self.examples = [
            "trade_repository_example.py",
            "candle_repository_example.py",
            "timeseries_repository_example.py",
            "websocket_live_ohlcv_example.py",
        ]
        self.available_examples = self.examples

        # API configuration
        self.api_host = os.getenv("API_HOST", "127.0.0.1")
        env_port = os.getenv("API_PORT")
        try:
            port = int(env_port) if env_port is not None else 9000
        except ValueError:
            self.logger.warning("Invalid API_PORT '%s'; falling back to 9000", env_port)
            port = 9000
        if port < 9000:
            self.logger.info("API_PORT %s is below 9000; using 9000", port)
            port = 9000
        self.api_port = port
        os.environ["API_PORT"] = str(self.api_port)

        # Test data configuration (matching fullon_ohlcv_service - NO BINANCE!)
        self.test_exchanges = ["kraken", "bitmex", "hyperliquid"]
        self.test_symbols = {
            "kraken": ["BTC/USDC"],
            "bitmex": ["BTC/USD:BTC"],
            "hyperliquid": ["BTC/USDC:USDC"]
        }

        # Legacy compatibility
        self.test_db_name = self.test_db_ohlcv
        if "test" not in self.test_db_name.lower():
            self.logger.warning(
                "DB_TEST_NAME '%s' does not look like a test database",
                self.test_db_name,
            )

    async def ensure_timescale_database(self) -> None:
        """Ensure the test database exists and has TimescaleDB enabled."""
        import asyncpg

        # Create DB if missing via postgres admin connection
        admin_user = os.getenv("DB_USER", "fullon")
        admin_pass = os.getenv("DB_PASSWORD", "fullon")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")

        admin_dsn = f"postgresql://{admin_user}:{admin_pass}@{host}:{port}/postgres"
        conn = await asyncpg.connect(admin_dsn)
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname=$1", self.test_db_name
            )
            if not exists:
                # Use f-string for database name (cannot use parameters for database name in CREATE DATABASE)
                await conn.execute(f"CREATE DATABASE {self.test_db_name}")
                print(f"✅ Created database {self.test_db_name}")
        finally:
            await conn.close()

        # Enable extension in target DB
        db_dsn = f"postgresql://{admin_user}:{admin_pass}@{host}:{port}/{self.test_db_name}"
        conn2 = await asyncpg.connect(db_dsn)
        try:
            await conn2.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
            print(f"✅ Ensured timescaledb extension in {self.test_db_name}")
        finally:
            await conn2.close()

    async def setup_test_database(self):
        """Setup test databases using demo_data.py pattern."""
        print("🗄️  Setting up test databases with demo data...")

        try:
            # Environment variables already set in __init__
            # Verify they're set correctly
            print(f"📊 Using test databases:")
            print(f"   - ORM (DB_NAME): {os.getenv('DB_NAME')}")
            print(f"   - OHLCV (DB_OHLCV_NAME): {os.getenv('DB_OHLCV_NAME')}")

            # Import demo_data functions (environment already set, so safe)
            from demo_data import (
                create_dual_test_databases,
                install_orm_schema,
                install_demo_orm_data,
                install_demo_ohlcv_data,
            )

            # Create both ORM and OHLCV test databases
            print(f"📊 Creating dual test databases...")
            orm_db, ohlcv_db = await create_dual_test_databases(self.test_db_base + "_test")

            # Install ORM schema
            print("📊 Installing ORM schema...")
            await install_orm_schema(orm_db)

            # Install demo ORM data (exchanges, symbols, users)
            print("📊 Installing demo ORM data...")
            await install_demo_orm_data(orm_db)

            # Install demo OHLCV data (trades, candles)
            print("📊 Installing demo OHLCV data...")
            await install_demo_ohlcv_data(orm_db, ohlcv_db)

            print("✅ Test databases setup complete with demo data")

        except Exception as e:
            print(f"❌ Failed to setup test databases: {e}")
            import traceback
            traceback.print_exc()
            raise  # Raise to abort - can't run examples without databases

    async def start_api_server(self):
        """Start the API server for testing."""
        print("🚀 Starting API server...")

        try:
            # Start the standalone server
            server_script = "../src/fullon_ohlcv_api/standalone_server.py"
            server_path = os.path.join(os.path.dirname(__file__), server_script)

            if not os.path.exists(server_path):
                raise FileNotFoundError(f"Server script not found: {server_path}")

            # Set test environment
            env = os.environ.copy()
            # Set both ORM and OHLCV database names
            env["DB_NAME"] = self.test_db_orm
            env["DB_OHLCV_NAME"] = self.test_db_ohlcv
            # CRITICAL: API server needs DB_TEST_NAME for test mode
            env["DB_TEST_NAME"] = self.test_db_ohlcv
            env["API_HOST"] = self.api_host
            env["API_PORT"] = str(self.api_port)

            # Debug: Print what we're setting
            print(f"   DB_NAME={env['DB_NAME']}")
            print(f"   DB_OHLCV_NAME={env['DB_OHLCV_NAME']}")
            print(f"   DB_TEST_NAME={env['DB_TEST_NAME']}")

            # Start server process (capture output for debugging)
            import tempfile
            self.server_log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')
            print(f"   Server log: {self.server_log_file.name}")

            self.api_process = subprocess.Popen(
                [sys.executable, server_path],
                env=env,
                stdout=self.server_log_file,
                stderr=subprocess.STDOUT,
            )

            # Wait for server to start
            print("⏳ Waiting for server to start...")
            # Poll health endpoint for readiness (up to ~10s)
            ready = await self._wait_for_health(timeout_seconds=10)

            # Check if server is running
            if self.api_process.poll() is not None or not ready:
                stdout, stderr = self.api_process.communicate()
                raise RuntimeError(f"Server failed to start: {stderr.decode()}")
            else:
                print(f"✅ API server started on {self.api_host}:{self.api_port}")

        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            raise

    async def _wait_for_health(self, timeout_seconds: int = 10) -> bool:
        """Poll the /health endpoint until it responds or timeout."""
        import time
        from urllib.request import urlopen
        from urllib.error import URLError

        deadline = time.time() + timeout_seconds
        url = f"http://{self.api_host}:{self.api_port}/health"
        while time.time() < deadline:
            try:
                with urlopen(url, timeout=1) as resp:
                    if resp.getcode() == 200:
                        return True
            except URLError:
                pass
            except Exception:
                pass
            await asyncio.sleep(0.5)
        return False

    def stop_api_server(self):
        """Stop the API server."""
        if self.api_process:
            print("🛑 Stopping API server...")
            self.api_process.terminate()

            # Wait for graceful shutdown
            try:
                self.api_process.wait(timeout=5)
                print("✅ API server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing API server...")
                self.api_process.kill()
                self.api_process.wait()

            # Show server log if there were errors
            if hasattr(self, 'server_log_file'):
                self.server_log_file.seek(0)
                log_content = self.server_log_file.read()
                if 'error' in log_content.lower() or 'exception' in log_content.lower():
                    print("\n🔍 Server errors detected:")
                    print(log_content[-2000:])  # Last 2000 chars
                self.server_log_file.close()
                import os
                os.unlink(self.server_log_file.name)

    async def run_example(self, example_file):
        """Run a single example."""
        print(f"\n🧪 Running {example_file}...")

        try:
            # Get the path to the example file (should be in the same directory as run_all.py)
            example_path = os.path.join(os.path.dirname(__file__), example_file)
            
            # Run the example
            result = subprocess.run(
                [sys.executable, example_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print(f"✅ {example_file} completed successfully")
                if result.stdout:
                    print("📋 Output:", result.stdout[-200:])  # Last 200 chars
                return True
            else:
                print(f"❌ {example_file} failed with return code {result.returncode}")
                if result.stderr:
                    print("📋 Error:", result.stderr[-200:])
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ {example_file} timed out")
            return False
        except Exception as e:
            print(f"❌ {example_file} failed: {e}")
            return False

    async def run_all_examples(self, specific_example=None):
        """Run all examples or a specific example sequentially."""
        examples_to_run = [specific_example] if specific_example else self.examples
        print(f"\n📚 Running {len(examples_to_run)} example(s)...")

        results = []
        for example in examples_to_run:
            if example not in self.examples:
                print(f"❌ Unknown example: {example}")
                print(f"Available examples: {', '.join(self.examples)}")
                return False

            success = await self.run_example(example)
            results.append((example, success))

        # Summary
        successful = sum(1 for _, success in results if success)
        print(f"\n📊 Results: {successful}/{len(results)} example(s) passed")

        for example, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {example}")

        return successful == len(results)

    async def cleanup(self):
        """Cleanup test environment - drop both ORM and OHLCV databases."""
        print("\n🧹 Cleaning up...")

        # Stop API server
        self.stop_api_server()

        # Drop both test databases
        try:
            from demo_data import drop_dual_test_databases

            await drop_dual_test_databases(self.test_db_orm, self.test_db_ohlcv)
            print(f"✅ Dropped test databases")

        except Exception as e:
            print(f"⚠️  Database cleanup failed: {e}")
            print("💡 Leaving databases in place for inspection")

        print("✅ Cleanup complete")

    async def run(self, specific_example=None, setup_only=False, cleanup_only=False):
        """Run the complete example test suite or specific operations."""
        if cleanup_only:
            print("🧹 Cleanup Mode")
            print("=" * 30)
            await self.cleanup()
            return 0

        title = "🧪 fullon_ohlcv_api Examples Test Suite"
        if specific_example:
            title += f" - {specific_example}"
        print(title)
        print("=" * 50)

        success = False

        try:
            # Setup database with data BEFORE starting server
            await self.setup_test_database()
            
            # Wait a moment to ensure database operations are complete
            await asyncio.sleep(1)
            
            # Start API server after data is populated
            await self.start_api_server()

            if setup_only:
                print("✅ Setup complete - server running, use Ctrl+C to stop")
                # Keep server running until interrupted
                while True:
                    await asyncio.sleep(1)
            else:
                # Run examples
                success = await self.run_all_examples(specific_example)

        except KeyboardInterrupt:
            print("\n🛑 Test suite interrupted")
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            logger.error("Test suite error", error=str(e))
        finally:
            # Always cleanup unless setup-only mode
            if not setup_only:
                await self.cleanup()

        if not setup_only:
            print("\n" + "=" * 50)
            if success:
                print(
                    "🎉 All examples passed!"
                    if not specific_example
                    else f"🎉 {specific_example} passed!"
                )
                return 0
            else:
                print(
                    "❌ Some examples failed"
                    if not specific_example
                    else f"❌ {specific_example} failed"
                )
                return 1

        return 0


def setup_signal_handlers():
    """Setup signal handlers for cleanup."""

    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}")
        # The async cleanup will be handled by the finally block
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function with command-line argument support."""
    parser = argparse.ArgumentParser(
        description="fullon_ohlcv_api Examples Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python run_all.py                                    # Run all examples
  python run_all.py --example trade_repository_example.py  # Run specific example
  python run_all.py --setup-only                       # Setup and keep server running
  python run_all.py --cleanup-only                     # Cleanup only
        """,
    )

    parser.add_argument(
        "--example",
        type=str,
        help="Run a specific example file (e.g., trade_repository_example.py)",
    )

    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Setup test database and start server, then wait (use Ctrl+C to stop)",
    )

    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Cleanup only (stop any running servers)",
    )

    parser.add_argument("--list", action="store_true", help="List available examples")

    args = parser.parse_args()

    runner = ExampleTestRunner()

    if args.list:
        print("📚 Available Examples:")
        for i, example in enumerate(runner.examples, 1):
            print(f"  {i}. {example}")
        return

    setup_signal_handlers()

    exit_code = await runner.run(
        specific_example=args.example,
        setup_only=args.setup_only,
        cleanup_only=args.cleanup_only,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    # Import and install uvloop for performance
    try:
        from fullon_ohlcv.utils import install_uvloop
        install_uvloop()
    except ImportError:
        print("⚠️  fullon_ohlcv not available - running without uvloop")

    asyncio.run(main())
