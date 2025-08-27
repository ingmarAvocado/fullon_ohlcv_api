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
    from fullon_ohlcv.models import Candle, Trade
    from fullon_ohlcv.repositories.ohlcv import CandleRepository, TradeRepository
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
        load_dotenv()
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
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = os.getenv("API_PORT", "8000")
        self.test_exchange = "binance"
        self.test_symbols = ["BTC/USDT", "ETH/USDT"]

    async def setup_test_database(self):
        """Setup test database with sample data."""
        print("🗄️  Setting up test database...")

        try:
            # Create test data
            test_trades = []
            test_candles = []

            base_time = datetime.now(UTC)
            base_price = 50000.0

            for i in range(20):
                # Create test trades
                trade_time = base_time - timedelta(minutes=i * 5)
                price = base_price + (i * 100)  # Varying prices

                trade = Trade(
                    timestamp=trade_time,
                    price=price,
                    volume=0.1 + (i * 0.01),
                    side="BUY" if i % 2 == 0 else "SELL",
                    type="MARKET",
                )
                test_trades.append(trade)

                # Create test candles
                if i % 5 == 0:  # Every 5th iteration
                    candle = Candle(
                        timestamp=trade_time,
                        open=price - 50,
                        high=price + 100,
                        low=price - 100,
                        close=price,
                        vol=10.0 + i,
                    )
                    test_candles.append(candle)

            # Save to test database
            for symbol in self.test_symbols:
                # Save trades
                async with TradeRepository(
                    self.test_exchange, symbol, test=True
                ) as repo:
                    success = await repo.save_trades(test_trades)
                    if success:
                        print(f"✅ Created {len(test_trades)} test trades for {symbol}")
                    else:
                        print(f"⚠️  Failed to create test trades for {symbol}")

                # Save candles
                async with CandleRepository(
                    self.test_exchange, symbol, test=True
                ) as repo:
                    success = await repo.save_candles(test_candles)
                    if success:
                        print(
                            f"✅ Created {len(test_candles)} test candles for {symbol}"
                        )
                    else:
                        print(f"⚠️  Failed to create test candles for {symbol}")

            print("✅ Test database setup complete")

        except Exception as e:
            print(f"❌ Failed to setup test database: {e}")
            raise

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
            env["DB_TEST_NAME"] = "fullon_ohlcv_test"  # Force test database

            # Start server process
            self.api_process = subprocess.Popen(
                [sys.executable, server_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to start
            print("⏳ Waiting for server to start...")
            await asyncio.sleep(3)

            # Check if server is running
            if self.api_process.poll() is None:
                print(f"✅ API server started on {self.api_host}:{self.api_port}")
            else:
                stdout, stderr = self.api_process.communicate()
                raise RuntimeError(f"Server failed to start: {stderr.decode()}")

        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            raise

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
            # Run the example
            result = subprocess.run(
                [sys.executable, example_file],
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

        # Clean up test database (optional - test data is isolated)
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
            # Setup
            await self.setup_test_database()
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
