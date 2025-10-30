#!/usr/bin/env python3
"""
Run All SDK Examples - fullon_ohlcv_sdk

Runs all SDK examples that demonstrate the Python SDK returning fullon_ohlcv objects.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    from fullon_ohlcv.utils import install_uvloop
except ImportError:

    def install_uvloop():
        pass


async def main():
    """Run all SDK examples."""
    # Load environment
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = os.getenv("API_PORT", "9000")
    base_url = f"http://{api_host}:{api_port}"

    print("🚀 Fullon OHLCV SDK Examples")
    print(f"API URL: {base_url}")
    print("=" * 40)

    # SDK examples to run
    examples = [
        "trade_repository_sdk_example.py",
        "candle_repository_sdk_example.py",
        "timeseries_repository_sdk_example.py",
        "websocket_live_ohlcv_sdk_example.py",
    ]

    results = []

    for example in examples:
        print(f"\n🧪 Running {example}...")

        try:
            example_path = Path(__file__).parent / example

            # Run the example
            result = subprocess.run(
                [sys.executable, str(example_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print(f"✅ {example} completed successfully")
                results.append((example, True))
            else:
                print(f"❌ {example} failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[-200:]}")
                results.append((example, False))

        except subprocess.TimeoutExpired:
            print(f"⏰ {example} timed out")
            results.append((example, False))
        except Exception as e:
            print(f"❌ {example} failed: {e}")
            results.append((example, False))

    # Summary
    print("\n" + "=" * 40)
    successful = sum(1 for _, success in results if success)
    print(f"📊 Results: {successful}/{len(results)} SDK examples passed")

    for example, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {example}")

    if successful == len(results):
        print("\n🎉 All SDK examples passed!")
        return 0
    else:
        print("\n❌ Some SDK examples failed")
        return 1


if __name__ == "__main__":
    install_uvloop()
    sys.exit(asyncio.run(main()))
