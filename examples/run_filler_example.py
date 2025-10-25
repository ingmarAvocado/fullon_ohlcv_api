#!/usr/bin/env python3
"""
Simple filler test - KISS approach
Load env, clear DB, fill data
"""

import asyncio

from dotenv import load_dotenv

# Load environment
load_dotenv()


async def main():
    print("🔧 Simple Filler Test")
    print("=" * 30)

    # Import after env is loaded
    from fill_data_examples import ExampleDataFiller

    filler = ExampleDataFiller(test_mode=True)

    print("1. Clear database...")
    await filler.clear_all_data()

    print("2. Fill database...")
    success = await filler.fill_all_data()

    print(f"Result: {success}")


if __name__ == "__main__":
    from fullon_ohlcv.utils import install_uvloop

    install_uvloop()
    asyncio.run(main())
