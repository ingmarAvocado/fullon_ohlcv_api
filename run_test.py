#!/usr/bin/env python3
"""
Comprehensive test runner for fullon_ohlcv_api.

This script runs ALL tests and ensures they pass according to TDD principles.
Must be used before any pull request or merge.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔄 {description}...")
    print(f"   Command: {cmd}")

    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent
    )

    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ {description} - FAILED")
        print(f"   Error: {result.stderr.strip()}")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return False


def main():
    """Run comprehensive tests."""
    print("🚀 Running comprehensive test suite for fullon_ohlcv_api")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run from project root.")
        sys.exit(1)

    # List of all checks to run
    checks = [
        ("poetry install --without dev", "Install dependencies"),
        ("poetry run black --check .", "Code formatting check"),
        ("poetry run ruff check .", "Linting check"),
        ("poetry run mypy src/", "Type checking"),
        ("poetry run pytest tests/ -v", "Unit tests"),
        (
            "poetry run pytest tests/ --cov=src --cov-report=term-missing",
            "Test coverage",
        ),
    ]

    failed_checks = []

    for cmd, description in checks:
        if not run_command(cmd, description):
            failed_checks.append(description)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if not failed_checks:
        print("✅ ALL TESTS PASSED! 🎉")
        print("   Ready for commit/merge.")
        return 0
    else:
        print(f"❌ {len(failed_checks)} CHECKS FAILED:")
        for check in failed_checks:
            print(f"   - {check}")
        print("\n🔧 Fix the failing checks before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
