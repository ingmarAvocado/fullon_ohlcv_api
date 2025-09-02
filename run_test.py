#!/usr/bin/env python3
"""
Enhanced test runner with better visibility and control.
Now includes proper database setup before running tests.
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from dotenv import load_dotenv

# Load environment
load_dotenv()


class TestRunner:
    def __init__(self):
        self.api_process = None
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "9000"))
        
    def setup_database(self):
        """Setup database with test data before running tests"""
        print("=" * 60)
        print("🗄️  STEP 1: Setting up test database")
        print("=" * 60)
        
        try:
            # Use the KISS approach that works
            sys.path.insert(0, 'examples')
            from fill_data_examples import ExampleDataFiller
            from fullon_ohlcv.utils import install_uvloop
            
            async def setup():
                install_uvloop()
                filler = ExampleDataFiller(test_mode=True)
                
                print("🧹 Clearing any existing data...")
                await filler.clear_all_data()
                
                print("📊 Filling database with test data...")
                success = await filler.fill_all_data()
                return success
            
            success = asyncio.run(setup())
            
            if success:
                print("✅ Database setup completed successfully")
                return True
            else:
                print("❌ Database setup failed")
                return False
                
        except Exception as e:
            print(f"❌ Database setup error: {e}")
            return False
    
    def start_server(self):
        """Start web server for integration tests"""
        print("=" * 60)
        print("🚀 STEP 2: Starting test server")
        print("=" * 60)
        
        try:
            server_script = "src/fullon_ohlcv_api/standalone_server.py"
            
            # Set environment for server
            env = os.environ.copy()
            env["API_HOST"] = self.api_host
            env["API_PORT"] = str(self.api_port)
            
            self.api_process = subprocess.Popen(
                ["python", server_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # Wait for server to start
            print(f"⏳ Waiting for server to start on {self.api_host}:{self.api_port}...")
            time.sleep(3)
            
            if self.api_process.poll() is None:
                print("✅ Test server started successfully")
                return True
            else:
                stdout, stderr = self.api_process.communicate()
                print(f"❌ Server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Server start error: {e}")
            return False
    
    def stop_server(self):
        """Stop test server"""
        if self.api_process:
            print("🛑 Stopping test server...")
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                print("✅ Test server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing server...")
                self.api_process.kill()
                self.api_process.wait()
                print("✅ Test server killed")
    
    def cleanup_database(self):
        """Clean database after tests"""
        print("=" * 60)
        print("🧹 STEP 4: Cleaning up test database")
        print("=" * 60)
        
        try:
            # Use KISS approach
            sys.path.insert(0, 'examples')
            from fill_data_examples import ExampleDataFiller
            
            async def cleanup():
                filler = ExampleDataFiller(test_mode=True) 
                await filler.clear_all_data()
            
            asyncio.run(cleanup())
            print("✅ Database cleaned up")
            return True
            
        except Exception as e:
            print(f"⚠️  Database cleanup error: {e}")
            return False


def run_tests(args, runner):
    """Run pytest tests with enhanced output."""
    print("=" * 60)
    print("🧪 STEP 3: Running pytest tests")
    print("=" * 60)
    
    # Base pytest command
    cmd = ["poetry", "run", "pytest"]

    # Add paths
    if args.paths:
        cmd.extend(args.paths)
    else:
        # Default paths excluding performance and stress tests
        cmd.extend(["tests/"])

    # Parallel execution (default to enabled with auto workers)
    workers_display = "1 (no parallel)"
    if not args.no_parallel:
        if args.parallel or args.workers != 4:
            # Use specified number of workers
            cmd.extend(["-n", str(args.workers)])
            workers_display = str(args.workers)
        else:
            # Default to auto workers for parallel execution
            cmd.extend(["-n", "auto"])
            try:
                import os

                cpu_count = os.cpu_count() or 1
                workers_display = f"auto (~{cpu_count})"
            except Exception:
                workers_display = "auto"
    else:
        workers_display = "1 (no parallel)"

    # Verbosity - ensure visible progress percent from xdist
    if args.verbose == 1:
        cmd.append("-v")
    elif args.verbose >= 2:
        cmd.append("-vv")
    elif args.quiet:
        cmd.append("-q")
    else:
        # Default to verbose progress to show [XX%] per test from xdist
        cmd.append("-vv")

    # Output format options
    if args.tb:
        cmd.extend(["--tb", args.tb])

    if args.capture:
        cmd.extend(["--capture", args.capture])

    if args.no_header:
        cmd.append("--no-header")

    if args.no_summary:
        cmd.append("--no-summary")

    # Timeout (only add if different from default)
    if args.timeout != 30:  # 30 is our pytest.ini default
        cmd.extend(["--timeout", str(args.timeout)])

    # Timeout method
    if args.timeout_method:
        cmd.extend(["--timeout-method", args.timeout_method])

    # Stop on first failure
    if args.exitfirst:
        cmd.append("-x")

    # Max failures
    if args.maxfail:
        cmd.extend(["--maxfail", str(args.maxfail)])

    # Markers
    if args.markers:
        cmd.extend(["-m", args.markers])

    # Keyword filter
    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # Run last failed
    if args.lf:
        cmd.append("--lf")

    # Run failed first
    if args.ff:
        cmd.append("--ff")

    # Show slowest tests (only if different from default)
    if args.durations != 10:  # 10 is our pytest.ini default
        cmd.extend(["--durations", str(args.durations)])

    # Disable warnings if requested
    if args.no_warnings:
        cmd.extend(["-p", "no:warnings"])

    # Collection options
    if args.collect_only:
        cmd.append("--collect-only")

    if args.dry_run:
        cmd.append("--collect-only")

    # Coverage
    cov_enabled = False
    cov_desc = "disabled"
    if args.cov:
        cov_enabled = True
        if args.cov is True:
            cmd.append("--cov")
        else:
            cmd.extend(["--cov", args.cov])
        if args.cov_report:
            cmd.extend(["--cov-report", args.cov_report])
            cov_desc = f"enabled ({args.cov_report})"
        if args.cov_fail_under:
            cmd.extend(["--cov-fail-under", str(args.cov_fail_under)])
    elif args.cov_table:
        cov_enabled = True
        cmd.append("--cov")
        cmd.extend(["--cov-report", "term-missing"])
        cov_desc = "enabled (term-missing)"

    # JUnit XML output
    if args.junitxml:
        cmd.extend(["--junitxml", args.junitxml])

    # Disable output capturing for debugging
    if args.capture_no:
        cmd.append("-s")

    # Force color output
    if args.color:
        cmd.append("--color=yes")
    elif args.no_color:
        cmd.append("--color=no")

    # Results output format
    if args.results:
        cmd.extend(["-r", args.results])

    # Friendly pre-run summary
    print("Pytest Configuration:")
    print("- Paths:       ", " ".join(args.paths) if args.paths else "tests/")
    print("- Workers:     ", workers_display)
    print("- Verbosity:   ", ("quiet" if args.quiet else ("-v" if args.verbose == 1 else ("-vv" if args.verbose >= 2 else "-vv (default)"))))
    if args.markers:
        print("- Markers:     ", args.markers)
    if args.keyword:
        print("- Keywords:    ", args.keyword)
    if args.results:
        print("- Report:      ", args.results)
    print("- Coverage:    ", cov_desc)
    print("- Raw command: ", " ".join(cmd))
    print("-" * 60)

    # Run the tests
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced test runner with database setup and better visibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Flow: Setup DB → Start Server → Run Tests → Stop Server → Cleanup DB

Examples:
  ./run_test.py                           # Run default test suite (with DB setup)
  ./run_test.py tests/unit/ -v           # Run unit tests with normal verbosity
  ./run_test.py tests/integration/ -x    # Run integration tests, stop on first failure
  ./run_test.py -k "websocket" -vv       # Run websocket-related tests with high verbosity
  ./run_test.py --unit -q                # Run unit tests quietly
  ./run_test.py --integration --no-parallel # Run integration tests sequentially
  ./run_test.py --quick --tb=line        # Run quick tests with line-level traceback
  ./run_test.py --lf -vv                 # Re-run last failed tests with high verbosity
  ./run_test.py --cov --cov-report=html  # Run with coverage reporting
  ./run_test.py -w 8                     # Run with 8 parallel workers
  ./run_test.py --no-setup               # Skip database setup (unit tests only)
        """,
    )

    # Test paths
    parser.add_argument("paths", nargs="*", help="Test paths to run")

    # Quick test sets
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick tests (unit + fast integration)"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all tests including performance/stress"
    )

    # Setup control
    parser.add_argument("--no-setup", action="store_true", help="Skip database setup and server start (for unit tests)")
    parser.add_argument("--no-server", action="store_true", help="Skip server start (database setup only)")

    # Execution control
    parser.add_argument(
        "-n", "--parallel", action="store_true", help="Force parallel execution"
    )
    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel execution"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=4, help="Number of parallel workers"
    )
    parser.add_argument(
        "-x", "--exitfirst", action="store_true", help="Exit on first failure"
    )
    parser.add_argument("--maxfail", type=int, help="Exit after N failures")
    parser.add_argument("--lf", action="store_true", help="Run last failed tests only")
    parser.add_argument("--ff", action="store_true", help="Run failed tests first")

    # Verbosity and output
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument(
        "--tb",
        choices=["auto", "long", "short", "line", "native", "no"],
        help="Traceback print mode",
    )
    parser.add_argument(
        "--capture", choices=["sys", "fd", "no"], help="Capture method: sys|fd|no"
    )
    parser.add_argument(
        "-s",
        "--capture-no",
        action="store_true",
        help="Disable output capturing (same as --capture=no)",
    )
    parser.add_argument("--no-header", action="store_true", help="Disable header")
    parser.add_argument("--no-summary", action="store_true", help="Disable summary")
    parser.add_argument("--color", action="store_true", help="Force colored output")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    # Filtering
    parser.add_argument(
        "-m", "--markers", help="Run tests matching markers (e.g., 'not performance')"
    )
    parser.add_argument("-k", "--keyword", help="Run tests matching keyword")

    # Timeout
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout per test in seconds"
    )
    parser.add_argument(
        "--timeout-method", choices=["signal", "thread"], help="Timeout method"
    )

    # Results and reporting
    parser.add_argument(
        "--durations", type=int, default=10, help="Show N slowest tests"
    )
    parser.add_argument(
        "-r",
        "--results",
        default="fEsxX",
        help="Show extra test summary info: (f)ailed, (E)rror, (s)kipped, e(x)pected failures, (X)passed",
    )
    parser.add_argument("--no-warnings", action="store_true", help="Disable warnings")

    # Collection
    parser.add_argument(
        "--collect-only", action="store_true", help="Only collect tests, don't run them"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what tests would be run"
    )

    # Coverage
    parser.add_argument(
        "--cov",
        nargs="?",
        const=True,
        help="Enable coverage reporting (optionally specify source)",
    )
    parser.add_argument(
        "--cov-report",
        choices=["term", "html", "xml", "term-missing"],
        help="Coverage report type",
    )
    parser.add_argument(
        "--cov-fail-under", type=int, help="Fail if coverage is under this percentage"
    )
    parser.add_argument("--junitxml", help="Create JUnit XML report file")
    # Convenience: quick coverage table
    parser.add_argument(
        "--cov-table",
        action="store_true",
        help="Enable coverage and show term-missing table at the end",
    )

    args = parser.parse_args()

    # Handle quick test sets and set defaults
    if args.unit:
        args.paths = ["tests/unit/"]
        # Unit tests don't need database setup (keep current --no-setup setting)
    elif args.integration:
        args.paths = ["tests/integration/"]
        args.no_setup = False  # Integration tests need full setup (override --no-setup)
    elif args.quick:
        args.paths = ["tests/"]
        args.markers = "not slow"
        # Quick tests don't need database setup (keep current --no-setup setting)
    elif args.all:
        args.paths = ["tests/"]
        # All tests don't need database setup by default (keep current --no-setup setting)
    else:
        # Default behavior: NO database setup unless --integration flag is used
        # This covers the case where user runs: ./run_test.py  or  ./run_test.py tests/unit/test_models.py
        if not args.integration:
            args.no_setup = True  # Default: no database setup for regular test runs
    
    # If no specific paths given, default to tests/ directory
    if not args.paths:
        args.paths = ["tests/"]

    # Validate conflicting options
    if args.quiet and args.verbose:
        parser.error("Cannot use both --quiet and --verbose")

    if args.color and args.no_color:
        parser.error("Cannot use both --color and --no-color")

    if args.parallel and args.no_parallel:
        parser.error("Cannot use both --parallel and --no-parallel")

    # Main test flow
    runner = TestRunner()
    exit_code = 0
    
    print("🎯 Enhanced Test Runner - fullon_ohlcv_api")
    if args.no_setup:
        print("Flow: Run Tests Only (no database setup)")
    else:
        print("Flow: Setup DB → Start Server → Run Tests → Stop Server → Cleanup DB")
    
    try:
        # Step 1: Setup database (unless skipped)
        if not args.no_setup:
            if not runner.setup_database():
                print("❌ Database setup failed")
                sys.exit(1)
        
        # Step 2: Start server (unless skipped)  
        if not args.no_setup and not args.no_server:
            if not runner.start_server():
                print("❌ Server start failed")
                sys.exit(1)
        
        # Step 3: Run tests
        exit_code = run_tests(args, runner)
        
    except KeyboardInterrupt:
        print("\n🛑 Test run interrupted")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Test run failed: {e}")
        exit_code = 1
    finally:
        # Step 4: Cleanup
        if not args.no_setup and not args.no_server:
            runner.stop_server()
        if not args.no_setup:
            runner.cleanup_database()
    
    # Final summary
    print("=" * 60)
    if exit_code == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()