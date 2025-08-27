"""
FullonOhlcvGateway - Main library class for fullon_ohlcv_api.

This class provides the core functionality for integrating fullon_ohlcv
with FastAPI for OHLCV market data operations via REST API.
"""

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from fullon_log import get_component_logger

    logger = get_component_logger("fullon.api.ohlcv")
except ImportError:
    import logging

    logger = logging.getLogger("fullon.api.ohlcv")


class FullonOhlcvGateway:
    """
    Main gateway class for fullon_ohlcv_api.

    This class can be used in two ways:
    1. As a standalone server for testing/development
    2. As a composable library in a master_api

    Examples:
        # Standalone usage
        gateway = FullonOhlcvGateway()
        app = gateway.get_app()

        # Master API composition
        gateway = FullonOhlcvGateway(prefix="/ohlcv")
        routers = gateway.get_routers()
    """

    def __init__(
        self,
        title: str = "fullon_ohlcv_api",
        description: str = "FastAPI Gateway for fullon_ohlcv OHLCV market data operations",
        version: str = "0.1.0",
        prefix: str = "",
    ):
        """
        Initialize the gateway.

        Args:
            title: FastAPI app title
            description: FastAPI app description
            version: API version
            prefix: URL prefix for all routes (e.g., "/ohlcv" for master_api)
        """
        self.title = title
        self.description = description
        self.version = version
        self.prefix = prefix
        self._app: Optional[FastAPI] = None

        logger.info(
            "FullonOhlcvGateway initialized",
            title=title,
            version=version,
            prefix=prefix,
        )

    def get_app(self) -> FastAPI:
        """
        Get or create the FastAPI application.

        Returns:
            FastAPI application instance
        """
        if self._app is None:
            self._app = self._create_app()
        return self._app

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title=self.title,
            description=self.description,
            version=self.version,
            docs_url=f"{self.prefix}/docs" if self.prefix else "/docs",
            redoc_url=f"{self.prefix}/redoc" if self.prefix else "/redoc",
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add routes
        self._add_routes(app)

        # Add event handlers
        self._add_event_handlers(app)

        logger.info("FastAPI application created")
        return app

    def _add_routes(self, app: FastAPI) -> None:
        """Add routes to the application."""

        @app.get(f"{self.prefix}/health")
        async def health_check():
            """Health check endpoint."""
            logger.debug("Health check requested")
            return {"status": "healthy", "service": "fullon_ohlcv_api"}

        @app.get(f"{self.prefix}/")
        async def root():
            """Root endpoint."""
            logger.debug("Root endpoint requested")
            return {
                "message": "fullon_ohlcv_api",
                "description": "FastAPI Gateway for OHLCV market data",
                "docs_url": f"{self.prefix}/docs",
                "health_url": f"{self.prefix}/health",
            }

        # Add implemented routers
        from .routers import trades_router
        app.include_router(trades_router, prefix=f"{self.prefix}/api/trades", tags=["trades"])

    def _add_event_handlers(self, app: FastAPI) -> None:
        """Add event handlers to the application."""

        @app.on_event("startup")
        async def startup_event():
            """Application startup event."""
            logger.info(
                "OHLCV Gateway starting up",
                service="fullon_ohlcv_api",
                version=self.version,
                prefix=self.prefix,
            )

        @app.on_event("shutdown")
        async def shutdown_event():
            """Application shutdown event."""
            logger.info("OHLCV Gateway shutting down")

    def get_routers(self) -> list:
        """
        Get all routers for composing into master_api.

        Returns:
            List of FastAPI router instances
        """
        routers = []

        # Return implemented routers
        from .routers import trades_router
        routers.extend([
            trades_router,
        ])

        logger.debug("Returning routers for composition", count=len(routers))
        return routers
