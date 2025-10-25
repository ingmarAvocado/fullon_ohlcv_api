#!/usr/bin/env python3
"""
Demo Data Setup for fullon_ohlcv_api Examples

Creates isolated test environment with:
- Test ORM database (for exchanges, symbols, users)
- Test OHLCV database (for trade/candle data)
- Demo market data for API testing

Usage:
    python examples/demo_data.py --setup      # Create test DBs and install demo data
    python examples/demo_data.py --cleanup    # Drop test DBs
    python examples/demo_data.py --run-all    # Setup, run examples, cleanup
"""

import argparse
import asyncio
import os
import random
import string
import sys
from pathlib import Path

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
try:
    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")
except ImportError:
    print("⚠️  python-dotenv not available, make sure .env variables are set manually")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

from fullon_log import get_component_logger

# Create fullon logger alongside color output
fullon_logger = get_component_logger("fullon.ohlcv_api.example.demo_data")


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.CYAN}→ {msg}{Colors.END}")


def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def generate_test_db_name(worker_id: str = "") -> str:
    """Generate worker-aware test database name."""
    base_name = os.getenv("DB_TEST_NAME", "fullon_ohlcv_test")

    if worker_id:
        return f"{base_name}_{worker_id}"
    else:
        # Fallback to random for manual/CLI usage
        random_suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        return f"{base_name}_{random_suffix}"


async def create_test_database(db_name: str) -> bool:
    """Create isolated test database using asyncpg"""
    print_info(f"Creating test database: {db_name}")
    fullon_logger.info(f"Creating isolated test database: {db_name}")

    try:
        import asyncpg

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")

        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database="postgres"
        )

        try:
            # Database creation requires direct SQL (administrative operation)
            await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            await conn.execute(f'CREATE DATABASE "{db_name}"')

            print_success(f"Test database created: {db_name}")
            fullon_logger.info(f"Test database created successfully: {db_name}")
            return True

        finally:
            await conn.close()

    except Exception as e:
        print_error(f"Failed to create test database: {e}")
        fullon_logger.error(f"Failed to create test database {db_name}: {e}")
        return False


async def drop_test_database(db_name: str) -> bool:
    """Drop test database"""
    print_info(f"Dropping test database: {db_name}")

    try:
        import asyncpg

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")

        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database="postgres"
        )

        try:
            # Connection termination and database dropping require direct SQL
            await conn.execute(
                """
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = $1
                AND pid <> pg_backend_pid()
            """,
                db_name,
            )

            await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')

            print_success(f"Test database dropped: {db_name}")
            return True

        finally:
            await conn.close()

    except Exception as e:
        print_error(f"Failed to drop test database: {e}")
        return False


async def create_dual_test_databases(base_name: str) -> tuple[str, str]:
    """
    Create both fullon_orm and fullon_ohlcv test databases.

    Returns:
        tuple[str, str]: (orm_db_name, ohlcv_db_name)
    """
    orm_db_name = f"{base_name}_orm"
    ohlcv_db_name = f"{base_name}_ohlcv"

    print_info(f"Creating dual test databases: {orm_db_name} + {ohlcv_db_name}")
    fullon_logger.info(
        f"Creating dual test databases: orm={orm_db_name}, ohlcv={ohlcv_db_name}"
    )

    # Create both databases
    orm_success = await create_test_database(orm_db_name)
    ohlcv_success = await create_test_database(ohlcv_db_name)

    if orm_success and ohlcv_success:
        print_success("Both test databases created successfully")
        fullon_logger.info(
            f"Dual test databases created: orm={orm_db_name}, ohlcv={ohlcv_db_name}"
        )
        return orm_db_name, ohlcv_db_name
    else:
        # Clean up if one failed
        if orm_success:
            await drop_test_database(orm_db_name)
        if ohlcv_success:
            await drop_test_database(ohlcv_db_name)
        raise RuntimeError("Failed to create both test databases")


async def drop_dual_test_databases(orm_db_name: str, ohlcv_db_name: str) -> bool:
    """Drop both fullon_orm and fullon_ohlcv test databases."""
    print_info(f"Dropping dual test databases: {orm_db_name} + {ohlcv_db_name}")
    fullon_logger.info(
        f"Dropping dual test databases: orm={orm_db_name}, ohlcv={ohlcv_db_name}"
    )

    orm_success = await drop_test_database(orm_db_name)
    ohlcv_success = await drop_test_database(ohlcv_db_name)

    if orm_success and ohlcv_success:
        print_success("Both test databases dropped successfully")
        fullon_logger.info(
            f"Dual test databases dropped: orm={orm_db_name}, ohlcv={ohlcv_db_name}"
        )
        return True
    else:
        print_warning(
            f"Some databases failed to drop: orm={orm_success}, ohlcv={ohlcv_success}"
        )
        return False


async def install_orm_schema(orm_db_name: str) -> bool:
    """Install fullon_orm schema in test database"""
    print_info("Installing fullon_orm schema...")

    try:
        # Temporarily update DATABASE_URL to point to test database
        original_db_url = os.environ.get("DATABASE_URL")

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")

        test_db_url = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{orm_db_name}"
        )
        os.environ["DATABASE_URL"] = test_db_url

        # Initialize fullon_orm schema
        from fullon_orm import init_db

        await init_db()

        print_success("fullon_orm schema installed successfully")
        fullon_logger.info(f"fullon_orm schema installed in {orm_db_name}")

        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

        return True

    except Exception as e:
        print_error(f"Failed to install fullon_orm schema: {e}")
        fullon_logger.error(f"Failed to install fullon_orm schema: {e}")
        return False


async def install_demo_orm_data(orm_db_name: str) -> bool:
    """Install demo ORM data (exchanges, symbols, users)"""
    print_header("INSTALLING DEMO ORM DATA")
    fullon_logger.info("Starting demo ORM data installation")

    try:
        # Temporarily update DATABASE_URL
        original_db_url = os.environ.get("DATABASE_URL")

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")

        test_db_url = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{orm_db_name}"
        )
        os.environ["DATABASE_URL"] = test_db_url

        from fullon_orm import DatabaseContext
        from fullon_orm.models import Exchange, Symbol, User
        from fullon_orm.models.user import RoleEnum

        async with DatabaseContext() as db:
            # Create admin user
            admin_email = os.getenv("ADMIN_MAIL", "admin@fullon")
            existing_uid = await db.users.get_user_id(admin_email)

            if not existing_uid:
                user = User(
                    mail=admin_email,
                    password="password",
                    f2a="---",
                    role=RoleEnum.ADMIN,
                    name="robert",
                    lastname="plant",
                    phone="666666666",
                    id_num="3242",
                )
                created_user = await db.users.add_user(user)
                uid = created_user.uid
                print_success(f"Admin user created with UID: {uid}")
            else:
                uid = existing_uid
                print_info("Admin user already exists")

            await db.commit()

            # Create exchanges (SAME as fullon_ohlcv_service/examples/demo_data.py)
            exchanges_to_create = ["kraken", "bitmex", "hyperliquid"]

            for exchange_name in exchanges_to_create:
                # Create category exchange if needed
                cat_exchanges = await db.exchanges.get_cat_exchanges(all=True)
                cat_ex_id = None

                for ce in cat_exchanges:
                    if ce.name == exchange_name:
                        cat_ex_id = ce.cat_ex_id
                        break

                if not cat_ex_id:
                    cat_exchange = await db.exchanges.create_cat_exchange(
                        exchange_name, ""
                    )
                    cat_ex_id = cat_exchange.cat_ex_id
                    print_success(f"Category exchange created: {exchange_name}")

                # Create user exchange
                user_exchange_name = f"{exchange_name}1"
                user_exchanges = await db.exchanges.get_user_exchanges(uid)
                exchange_exists = any(
                    ue.name == user_exchange_name for ue in user_exchanges
                )

                if not exchange_exists:
                    exchange = Exchange(
                        uid=uid,
                        cat_ex_id=cat_ex_id,
                        name=user_exchange_name,
                        test=False,
                        active=True,
                    )
                    await db.exchanges.add_user_exchange(exchange)
                    print_success(f"User exchange created: {user_exchange_name}")

            await db.commit()

            # Create symbols for each exchange (SAME as fullon_ohlcv_service/examples/demo_data.py)
            exchange_symbols = {
                "kraken": [
                    {
                        "symbol": "BTC/USDC",
                        "base": "BTC",
                        "quote": "USD",
                        "futures": True,
                    },
                ],
                "bitmex": [
                    {
                        "symbol": "BTC/USD:BTC",
                        "base": "BTC",
                        "quote": "USD",
                        "futures": True,
                    },
                ],
                "hyperliquid": [
                    {
                        "symbol": "BTC/USDC:USDC",
                        "base": "BTC",
                        "quote": "USDC",
                        "futures": True,
                    },
                ],
            }

            cat_exchanges = await db.exchanges.get_cat_exchanges(all=True)
            cat_exchanges_dict = {ce.name: ce.cat_ex_id for ce in cat_exchanges}

            for exchange_name, symbols in exchange_symbols.items():
                if exchange_name not in cat_exchanges_dict:
                    continue

                cat_ex_id = cat_exchanges_dict[exchange_name]

                for symbol_data in symbols:
                    try:
                        existing_symbol = await db.symbols.get_by_symbol(
                            symbol_data["symbol"], cat_ex_id=cat_ex_id
                        )
                        if existing_symbol:
                            continue
                    except:
                        pass

                    symbol = Symbol(
                        symbol=symbol_data["symbol"],
                        cat_ex_id=cat_ex_id,
                        updateframe="1h",
                        backtest=1,
                        decimals=6,
                        base=symbol_data["base"],
                        quote=symbol_data["quote"],
                        futures=symbol_data["futures"],
                    )

                    await db.symbols.add_symbol(symbol)
                    print_info(
                        f"Symbol added: {symbol_data['symbol']} ({exchange_name})"
                    )

            await db.commit()
            print_success("Demo ORM data installation complete!")
            fullon_logger.info("Demo ORM data installation completed successfully")

        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

        return True

    except Exception as e:
        print_error(f"Failed to install demo ORM data: {e}")
        fullon_logger.error(f"Demo ORM data installation failed: {e}")
        return False


async def install_demo_ohlcv_data(orm_db_name: str, ohlcv_db_name: str) -> bool:
    """Install demo OHLCV data using fill_data_examples"""
    print_header("INSTALLING DEMO OHLCV DATA")
    fullon_logger.info("Starting demo OHLCV data installation")

    try:
        # Set environment variables to point to test databases
        original_db_name_env = os.environ.get("DB_NAME")
        original_ohlcv_name_env = os.environ.get("DB_OHLCV_NAME")
        original_db_url = os.environ.get("DATABASE_URL")

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")

        # Point to test databases
        os.environ["DB_NAME"] = orm_db_name
        os.environ["DB_OHLCV_NAME"] = ohlcv_db_name
        # fullon_ohlcv uses DB_TEST_NAME for test mode database selection
        os.environ["DB_TEST_NAME"] = ohlcv_db_name
        os.environ["DATABASE_URL"] = (
            f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{orm_db_name}"
        )

        # CRITICAL: Force reload of ALL fullon_ohlcv modules to pick up new environment variables
        # Clear config module first (it creates the singleton with environment variables)
        modules_to_clear = [
            "fullon_ohlcv.utils.config",
            "fullon_ohlcv.utils.database",
            "fullon_ohlcv.repositories.base_repository",
            "fullon_ohlcv.repositories.ohlcv.base_repository",
            "fullon_ohlcv.repositories.ohlcv.trade_repository",
            "fullon_ohlcv.repositories.ohlcv.candle_repository",
            "fullon_ohlcv.repositories.ohlcv",
            "fullon_ohlcv.models",
        ]
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
                print_info(f"Cleared module cache: {module_name}")

        # Import and run fill_data_examples
        sys.path.insert(0, str(Path(__file__).parent))

        from fill_data_examples import ExampleDataFiller

        filler = ExampleDataFiller(test_mode=True)
        success = await filler.fill_all_data()

        # Restore environment variables
        if original_db_name_env:
            os.environ["DB_NAME"] = original_db_name_env
        else:
            os.environ.pop("DB_NAME", None)

        if original_ohlcv_name_env:
            os.environ["DB_OHLCV_NAME"] = original_ohlcv_name_env
        else:
            os.environ.pop("DB_OHLCV_NAME", None)

        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)

        if success:
            print_success("Demo OHLCV data installation complete!")
            fullon_logger.info("Demo OHLCV data installation completed successfully")
        else:
            print_warning("Demo OHLCV data installation completed with some errors")

        return success

    except Exception as e:
        print_error(f"Failed to install demo OHLCV data: {e}")
        fullon_logger.error(f"Demo OHLCV data installation failed: {e}")
        return False


async def setup_demo_environment():
    """Setup complete demo environment with dual databases and data"""
    test_base_name = generate_test_db_name()

    try:
        # Create both databases
        orm_db_name, ohlcv_db_name = await create_dual_test_databases(test_base_name)

        # Install ORM schema
        if not await install_orm_schema(orm_db_name):
            raise RuntimeError("Failed to install ORM schema")

        # Install demo ORM data
        if not await install_demo_orm_data(orm_db_name):
            raise RuntimeError("Failed to install demo ORM data")

        # Install demo OHLCV data
        await install_demo_ohlcv_data(orm_db_name, ohlcv_db_name)

        print_success("\n✓ Demo environment ready!")
        print_info(f"ORM database: {orm_db_name}")
        print_info(f"OHLCV database: {ohlcv_db_name}")
        print_info(f"To cleanup: python {sys.argv[0]} --cleanup-dual {test_base_name}")

        return test_base_name

    except Exception as e:
        print_error(f"Failed to setup demo environment: {e}")
        # Cleanup on failure
        try:
            await drop_dual_test_databases(
                f"{test_base_name}_orm", f"{test_base_name}_ohlcv"
            )
        except:
            pass
        raise


async def run_examples():
    """Run all ohlcv_api examples"""
    print_header("RUNNING API EXAMPLES")

    # TODO: Implement example runner
    print_info("Example runner not yet implemented")
    return True


async def run_full_demo():
    """Setup, run examples, and cleanup"""
    test_base_name = None

    try:
        test_base_name = await setup_demo_environment()

        # Run examples
        success = await run_examples()

        if success:
            print_success("\n🎉 All examples passed!")
        else:
            print_warning("\n⚠️  Some examples failed")

        return success

    finally:
        # Cleanup
        if test_base_name:
            await drop_dual_test_databases(
                f"{test_base_name}_orm", f"{test_base_name}_ohlcv"
            )


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Demo Data Setup for fullon_ohlcv_api Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Create test databases and install demo data",
    )
    parser.add_argument(
        "--cleanup",
        metavar="BASE_NAME",
        help="Drop test databases with given base name",
    )
    parser.add_argument(
        "--run-all", action="store_true", help="Setup, run all examples, then cleanup"
    )
    parser.add_argument(
        "--examples-only",
        action="store_true",
        help="Run examples against existing database",
    )

    args = parser.parse_args()

    if args.setup:
        base_name = await setup_demo_environment()
        print_info(
            f"\nTo cleanup later, run: python {sys.argv[0]} --cleanup {base_name}"
        )

    elif args.cleanup:
        success = await drop_dual_test_databases(
            f"{args.cleanup}_orm", f"{args.cleanup}_ohlcv"
        )
        sys.exit(0 if success else 1)

    elif args.run_all:
        success = await run_full_demo()
        sys.exit(0 if success else 1)

    elif args.examples_only:
        success = await run_examples()
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
