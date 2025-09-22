#!/usr/bin/env python3
"""
Run All SDK Examples - fullon_ohlcv_api

Sets up test database, starts API server, runs all SDK examples, then cleans up.
Mirrors examples/run_all.py but targets examples/sdk/*_sdk_example.py.
"""

import argparse
import asyncio
import os
import signal
import subprocess
import sys

from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:
    print("❌ fullon_ohlcv not available - cannot run SDK examples")
    sys.exit(1)

from fullon_log import get_component_logger

logger = get_component_logger("fullon.examples.run_all_sdk")


class SdkExampleTestRunner:
    """SDK example runner with server + DB orchestration."""

    def __init__(self) -> None:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        load_dotenv(env_path)
        self.api_process: subprocess.Popen | None = None
        self.examples = [
            "trade_repository_sdk_example.py",
            "candle_repository_sdk_example.py",
            "timeseries_repository_sdk_example.py",
            "websocket_live_ohlcv_sdk_example.py",
        ]

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
        os.environ["API_PORT"] = str(self.api_port)

        self.test_db_name = os.getenv("DB_TEST_NAME", "fullon_ohlcv2_test")
        if "test" not in self.test_db_name.lower():
            logger.warning(
                "DB_TEST_NAME '%s' does not look like a test database; examples may write to non-test DB",
                self.test_db_name,
            )

    async def setup_test_database(self) -> None:
        print("🗄️  Setting up test database with realistic market data...")
        try:
            from fill_data_examples import ExampleDataFiller

            filler = ExampleDataFiller(test_mode=True)
            print("🧹 Clearing any existing data...")
            await filler.clear_all_data()

            print("📊 Filling database...")
            success = await filler.fill_all_data()
            if success:
                print("✅ Test database setup complete with realistic market data")
            else:
                print("⚠️  Database fill failed, but SDK examples will still run")
                print("💡 API will return valid empty responses where data is missing")
        except Exception as e:
            print(f"⚠️  Failed to setup test database: {e}")
            print("💡 SDK examples will run without test data (API may return empty responses)")

    async def _wait_for_health(self, timeout_seconds: int = 10) -> bool:
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

    async def start_api_server(self) -> None:
        print("🚀 Starting API server...")
        try:
            server_script = "../src/fullon_ohlcv_api/standalone_server.py"
            server_path = os.path.join(os.path.dirname(__file__), server_script)
            if not os.path.exists(server_path):
                raise FileNotFoundError(f"Server script not found: {server_path}")

            env = os.environ.copy()
            env["DB_TEST_NAME"] = os.getenv("DB_TEST_NAME", self.test_db_name)
            env["API_HOST"] = self.api_host
            env["API_PORT"] = str(self.api_port)

            self.api_process = subprocess.Popen(
                [sys.executable, server_path],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )

            print("⏳ Waiting for server to start...")
            ready = await self._wait_for_health(timeout_seconds=10)
            if self.api_process.poll() is not None or not ready:
                stdout, stderr = self.api_process.communicate()
                raise RuntimeError(
                    f"Server failed to start: {'' if stderr is None else stderr.decode()}"
                )
            else:
                print(f"✅ API server started on {self.api_host}:{self.api_port}")
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            raise

    def stop_api_server(self) -> None:
        if self.api_process:
            print("🛑 Stopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
                print("✅ API server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing API server...")
                self.api_process.kill()
                self.api_process.wait()

    async def run_example(self, example_file: str) -> bool:
        print(f"\n🧪 Running {example_file}...")
        try:
            example_path = os.path.join(os.path.dirname(__file__), "sdk", example_file)
            result = subprocess.run(
                [sys.executable, example_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                print(f"✅ {example_file} completed successfully")
                if result.stdout:
                    print("📋 Output:", result.stdout[-200:])
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

    async def run_all_examples(self, specific_example: str | None = None) -> bool:
        examples_to_run = [specific_example] if specific_example else self.examples
        print(f"\n📚 Running {len(examples_to_run)} SDK example(s)...")

        results: list[tuple[str, bool]] = []
        for example in examples_to_run:
            if example not in self.examples:
                print(f"❌ Unknown example: {example}")
                print(f"Available SDK examples: {', '.join(self.examples)}")
                return False
            success = await self.run_example(example)
            results.append((example, success))

        successful = sum(1 for _, s in results if s)
        print(f"\n📊 Results: {successful}/{len(results)} SDK example(s) passed")
        for example, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {example}")
        return successful == len(results)

    async def cleanup(self) -> None:
        print("\n🧹 Cleaning up...")
        self.stop_api_server()
        print("✅ Cleanup complete")


def setup_signal_handlers() -> None:
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="fullon_ohlcv_api SDK Examples Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  poetry run python examples/run_all_sdk.py                       # Run all SDK examples
  poetry run python examples/run_all_sdk.py --example trade_repository_sdk_example.py
  poetry run python examples/run_all_sdk.py --setup-only          # Setup and keep server running
  poetry run python examples/run_all_sdk.py --cleanup-only        # Cleanup only
        """,
    )
    parser.add_argument("--example", type=str, help="Run a specific SDK example file")
    parser.add_argument("--setup-only", action="store_true", help="Setup and keep server running")
    parser.add_argument("--cleanup-only", action="store_true", help="Cleanup only")
    parser.add_argument("--list", action="store_true", help="List available SDK examples")
    args = parser.parse_args()

    runner = SdkExampleTestRunner()

    if args.list:
        print("📚 Available SDK Examples:")
        for i, example in enumerate(runner.examples, 1):
            print(f"  {i}. {example}")
        return 0

    setup_signal_handlers()

    if args.cleanup_only:
        await runner.cleanup()
        return 0

    title = "🧪 fullon_ohlcv_api SDK Examples Test Suite"
    if args.example:
        title += f" - {args.example}"
    print(title)
    print("=" * 50)

    success = False
    try:
        await runner.setup_test_database()
        await runner.start_api_server()
        if args.setup_only:
            print("✅ Setup complete - server running, use Ctrl+C to stop")
            while True:
                await asyncio.sleep(1)
        else:
            success = await runner.run_all_examples(args.example)
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        logger.error("SDK suite error", error=str(e))
    finally:
        if not args.setup_only:
            await runner.cleanup()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All SDK examples passed!" if not args.example else f"🎉 {args.example} passed!")
        return 0
    else:
        print("❌ Some SDK examples failed" if not args.example else f"❌ {args.example} failed")
        return 1


if __name__ == "__main__":
    install_uvloop()
    sys.exit(asyncio.run(main()))

