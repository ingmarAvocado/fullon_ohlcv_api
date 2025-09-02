"""
Standalone server for fullon_ohlcv_api.

This module provides a standalone FastAPI server for development and testing.
For production use, prefer library mode with master_api composition.

Usage:
    python -m fullon_ohlcv_api.standalone_server

    Or with uvicorn directly:
    uvicorn fullon_ohlcv_api.standalone_server:app --reload
"""

import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, environment variables should be set externally
    pass

try:
    # Try relative import first (when imported as module)
    from .gateway import FullonOhlcvGateway
except ImportError:
    # Fall back to absolute import (when run directly)
    from fullon_ohlcv_api.gateway import FullonOhlcvGateway

# Create standalone server instance
gateway = FullonOhlcvGateway(
    title="Fullon OHLCV API - Standalone Server",
    description="""
    Standalone FastAPI server for OHLCV market data operations.

    This server exposes all fullon_ohlcv operations via REST API.
    For production use, prefer master_api composition.

    ## Features
    - 📊 Complete OHLCV market data operations
    - ⏰ Time-series optimized queries
    - 🔍 Interactive API documentation
    - 🚀 High-performance async operations

    ## Documentation
    - Swagger UI: /docs
    - ReDoc: /redoc
    - Health Check: /health
    """,
    version="0.1.0",
)

# Export app for uvicorn
app = gateway.get_app()

# For direct execution
if __name__ == "__main__":
    import uvicorn

    # Configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    # Enforce port >= 9000 (default 9000)
    env_port = os.getenv("API_PORT")
    try:
        port = int(env_port) if env_port is not None else 9000
    except ValueError:
        print(f"⚠️  Invalid API_PORT '{env_port}'; using default 9000")
        port = 9000
    if port < 9000:
        print(f"⚠️  API_PORT {port} is below 9000; using 9000")
        port = 9000
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    print("🚀 Starting fullon_ohlcv_api standalone server")
    print(f"   Host: {host}:{port}")
    print(f"   Reload: {reload}")
    print(f"   Docs: http://{host}:{port}/docs")

    uvicorn.run(
        "fullon_ohlcv_api.standalone_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
