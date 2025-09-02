#!/usr/bin/env python3
"""
Run All Examples - fullon_ohlcv_api

Sets up test database, starts API server, runs all examples, then cleans up.
Mirrors the fullon_ohlcv examples pattern.
"""

import argparse
import asyncio
import os
import signal
import subprocess
import sys
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:
    print("❌ fullon_ohlcv not available - cannot run examples")
    sys.exit(1)

from fullon_log import get_component_logger

logger = get_component_logger("fullon.examples.run_all")


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
        # Load environment variables from the project root .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        load_dotenv(env_path)
        self.api_process = None
        self.examples = [
            "trade_repository_example.py",
            "candle_repository_example.py",
            "timeseries_repository_example.py",
            "websocket_live_ohlcv_example.py",
        ]

        # Make examples available as property for CLI help
        self.available_examples = self.examples

        # Test configuration
        self.api_host = os.getenv("API_HOST", "127.0.0.1")
        # Enforce API port >= 9000 (default 9000)
        env_port = os.getenv("API_PORT")
        try:
            port = int(env_port) if env_port is not None else 9000
        except ValueError:
            logger.warning("Invalid API_PORT '%s'; falling back to 9000", env_port)
            port = 9000
        if port < 9000:
            logger.info("API_PORT %s is below 9000; using 9000", port)
            port = 9000
        self.api_port = port
        # Ensure child processes (server/examples) see the same port
        os.environ["API_PORT"] = str(self.api_port)
        self.test_exchange = "binance"
        self.test_symbols = ["BTC/USDT", "ETH/USDT"]
        # Database names
        self.test_db_name = os.getenv("DB_TEST_NAME", "fullon_ohlcv2_test")
        if "test" not in self.test_db_name.lower():
            logger.warning(
                "DB_TEST_NAME '%s' does not look like a test database; examples may write to non-test DB",
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
        """Setup test database with realistic sample data - KISS approach."""
        print("🗄️  Setting up test database with realistic market data...")

        try:
            # Ensure DB and extension
            await self.ensure_timescale_database()
            # Use the KISS approach that actually works
            from fill_data_examples import ExampleDataFiller
            filler = ExampleDataFiller(test_mode=True)
            
            print("🧹 Clearing any existing data...")
            await filler.clear_all_data()
            
            print("📊 Filling database...")
            success = await filler.fill_all_data()
            
            if success:
                print("✅ Test database setup complete with realistic market data")
            else:
                print("⚠️  Database fill failed, but examples will still run")
                print("💡 API will return valid empty responses where data is missing")

        except Exception as e:
            print(f"⚠️  Failed to setup test database: {e}")
            print("💡 Examples will run without test data (API will return empty but valid responses)")
            # Don't raise - let examples run even without data

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
            # Use the test database name from environment or default
            test_db_name = os.getenv("DB_TEST_NAME", "fullon_ohlcv2_test")
            env["DB_TEST_NAME"] = test_db_name
            env["API_HOST"] = self.api_host
            env["API_PORT"] = str(self.api_port)

            # Start server process
            self.api_process = subprocess.Popen(
                [sys.executable, server_path],
                env=env,
                stdout=subprocess.DEVNULL,
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
        """Cleanup test environment."""
        print("\n🧹 Cleaning up...")

        # Stop API server
        self.stop_api_server()

        # Optionally drop the whole test database
        try:
            import asyncpg
            admin_user = os.getenv("DB_USER", "fullon")
            admin_pass = os.getenv("DB_PASSWORD", "fullon")
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            admin_dsn = f"postgresql://{admin_user}:{admin_pass}@{host}:{port}/postgres"
            conn = await asyncpg.connect(admin_dsn)
            try:
                # terminate connections
                await conn.execute(
                    f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{self.test_db_name}' AND pid <> pg_backend_pid()
                    """
                )
                await conn.execute(f"DROP DATABASE IF EXISTS {self.test_db_name}")
                print(f"✅ Dropped test database {self.test_db_name}")
            finally:
                await conn.close()
        except Exception as e:
            print(f"⚠️  Database drop failed: {e}")
            print("💡 Leaving database in place for inspection")

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
    install_uvloop()
    asyncio.run(main())
