#!/usr/bin/env python3
"""
Library usage examples for fullon_ohlcv_api.

This demonstrates how to use fullon_ohlcv_api as a composable library
in a master_api or other FastAPI application.
"""

from fastapi import FastAPI
from fullon_ohlcv_api import FullonOhlcvGateway, get_all_routers


def example_1_direct_gateway():
    """Example 1: Using FullonOhlcvGateway directly."""
    print("=== Example 1: Direct Gateway Usage ===")
    
    # Create gateway instance
    gateway = FullonOhlcvGateway(
        title="My Master API - OHLCV Module",
        prefix="/ohlcv"  # All routes will be prefixed with /ohlcv
    )
    
    # Get the FastAPI app
    app = gateway.get_app()
    
    print(f"Gateway created with prefix: /ohlcv")
    print(f"Available routes: /ohlcv/, /ohlcv/health, /ohlcv/docs")
    
    return app


def example_2_router_composition():
    """Example 2: Using routers for master_api composition."""
    print("\n=== Example 2: Router Composition ===")
    
    # Create main FastAPI app
    app = FastAPI(title="Fullon Master API", version="1.0.0")
    
    # Get all routers from fullon_ohlcv_api
    routers = get_all_routers()
    
    # Mount them with prefix
    for router in routers:
        app.include_router(router, prefix="/ohlcv", tags=["OHLCV"])
    
    print(f"Composed {len(routers)} routers into master API")
    print("Routes will be available under /ohlcv/ prefix")
    
    return app


def example_3_multiple_libraries():
    """Example 3: Composing multiple fullon libraries (Production Pattern)."""
    print("\n=== Example 3: Fullon Master Trading API Composition ===")
    
    # Production master API with full ecosystem
    app = FastAPI(title="Fullon Master Trading API", version="1.0.0")
    
    # Database operations
    from fullon_ohlcv_api import get_all_routers as get_ohlcv_routers
    for router in get_ohlcv_routers():
        app.include_router(router, prefix="/api/v1/market", tags=["Market Data"])
    
    # Future libraries integration:
    # from fullon_orm_api import get_all_routers as get_orm_routers
    # for router in get_orm_routers():
    #     app.include_router(router, prefix="/api/v1/db", tags=["Database"])
    
    # from fullon_cache_api import get_all_routers as get_cache_routers
    # for router in get_cache_routers():
    #     app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])
    
    print("Master Trading API structure:")
    print("  /api/v1/market/* - Historical market data (fullon_ohlcv_api)")
    print("  /api/v1/db/*     - Persistent application data (fullon_orm_api)")
    print("  /api/v1/cache/*  - Real-time & temporary data (fullon_cache_api)")
    print("  /docs            - Combined API documentation with organized tags")
    
    print("\nAPI Benefits:")
    print("  📊 Clear separation: market data vs app data vs real-time")
    print("  🔗 Semantic URLs: intuitive endpoint discovery")
    print("  📚 Organized docs: tagged by data type and operation")
    print("  🔄 Versioned API: /api/v1/ for future compatibility")
    
    return app


def example_4_custom_configuration():
    """Example 4: Custom configuration for specific use case."""
    print("\n=== Example 4: Custom Configuration ===")
    
    # Create gateway with custom settings
    gateway = FullonOhlcvGateway(
        title="Crypto Market Data API",
        description="High-performance OHLCV market data operations for cryptocurrency trading",
        version="2.1.0",
        prefix="/api/v2/market"  # Custom prefix
    )
    
    app = gateway.get_app()
    
    # You could add additional middleware, routes, etc.
    
    print("Custom gateway configuration:")
    print("  Title: Crypto Market Data API")
    print("  Prefix: /api/v2/market")
    print("  Routes: /api/v2/market/, /api/v2/market/health")
    
    return app


async def example_5_programmatic_access():
    """Example 5: Programmatic access to gateway functionality."""
    print("\n=== Example 5: Programmatic Access ===")
    
    # Create gateway
    gateway = FullonOhlcvGateway()
    
    # Access routers programmatically
    routers = gateway.get_routers()
    print(f"Available routers: {len(routers)}")
    
    # Get app for inspection
    app = gateway.get_app()
    print(f"App routes count: {len(app.routes)}")
    
    # You could inspect routes, middleware, etc.
    for route in app.routes:
        print(f"  Route: {route.path} ({getattr(route, 'methods', ['N/A'])})")


def example_6_ohlcv_specific_patterns():
    """Example 6: OHLCV-specific usage patterns."""
    print("\n=== Example 6: OHLCV-Specific Patterns ===")
    
    # Market data focused configuration
    gateway = FullonOhlcvGateway(
        title="Market Data Gateway",
        description="""
        Real-time and historical cryptocurrency market data API.
        
        ## Features
        - 📊 Trade data retrieval with microsecond precision
        - 🕯️ OHLCV candles for multiple timeframes
        - ⚡ High-performance read operations
        - 📈 Time-series optimized read queries
        - 🔍 Multi-exchange data analysis
        
        ## Supported READ-ONLY Operations
        - Historical trade data queries
        - OHLCV candle data retrieval
        - Custom timeframe analysis
        - Cross-exchange data comparison
        """,
        prefix="/market"
    )
    
    app = gateway.get_app()
    
    print("OHLCV-specific configuration:")
    print("  Focus: Market data operations")
    print("  Optimized for: Time-series queries")
    print("  Use cases: Trading, analytics, research")
    
    return app


def example_7_production_deployment():
    """Example 7: Production deployment configuration."""
    print("\n=== Example 7: Production Deployment ===")
    
    # Production-ready configuration
    gateway = FullonOhlcvGateway(
        title="Fullon OHLCV API",
        description="Production OHLCV market data API with high availability",
        version="1.0.0",
        prefix="/api/v1"
    )
    
    app = gateway.get_app()
    
    # In production, you would add:
    # - Rate limiting
    # - Monitoring and metrics
    # - Custom error handlers
    # - Request/response logging
    # - Security middleware
    
    print("Production considerations:")
    print("  ✅ Structured logging enabled")
    print("  ⚡ Async operations throughout")
    print("  🔒 Ready for security middleware")
    print("  📊 Built-in health checks")
    print("  📖 Auto-generated documentation")
    
    return app


if __name__ == "__main__":
    """Run examples."""
    print("🚀 fullon_ohlcv_api Library Usage Examples")
    print("=" * 50)
    
    # Run examples
    app1 = example_1_direct_gateway()
    app2 = example_2_router_composition() 
    app3 = example_3_multiple_libraries()
    app4 = example_4_custom_configuration()
    app6 = example_6_ohlcv_specific_patterns()
    app7 = example_7_production_deployment()
    
    # Run async example
    import asyncio
    asyncio.run(example_5_programmatic_access())
    
    print("\n✅ All examples completed!")
    print("\nTo run a server with any of these configurations:")
    print("  uvicorn library_usage:app1 --reload  # Example 1 - Direct Gateway")
    print("  uvicorn library_usage:app2 --reload  # Example 2 - Router Composition") 
    print("  uvicorn library_usage:app3 --reload  # Example 3 - Multiple Libraries")
    print("  uvicorn library_usage:app4 --reload  # Example 4 - Custom Config")
    print("  uvicorn library_usage:app6 --reload  # Example 6 - OHLCV Focus")
    print("  uvicorn library_usage:app7 --reload  # Example 7 - Production Ready")
    
    print("\n📊 API Endpoint Structure:")
    print("  STANDALONE MODE (development/testing):")
    print("    GET  /api/trades/{exchange}/{symbol}")
    print("    GET  /api/candles/{exchange}/{symbol}/{timeframe}")
    print("    GET  /api/exchanges")
    
    print("\n  MASTER API MODE (production/recommended):")
    print("    GET  /api/v1/market/trades/{exchange}/{symbol}")
    print("    GET  /api/v1/market/candles/{exchange}/{symbol}/{timeframe}")
    print("    GET  /api/v1/market/exchanges")
    print("    GET  /api/v1/market/trades/{exchange}/{symbol}/stats")
    print("    GET  /api/v1/market/trades/{exchange}/{symbol}/export")
    
    print("\n🔗 Documentation URLs:")
    print("  📚 Interactive docs: /docs (combined when using master API)")
    print("  📖 ReDoc: /redoc") 
    print("  ❤️ Health check: /health")
    print("  🎯 Organized tags: Market Data, Database, Cache")