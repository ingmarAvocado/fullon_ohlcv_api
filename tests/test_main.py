"""
Main integration tests for fullon_ohlcv_api.

Tests the core functionality of the gateway, basic endpoints,
and overall application behavior.
"""

import pytest
from fastapi.testclient import TestClient

from fullon_ohlcv_api import FullonOhlcvGateway, get_all_routers
from fullon_ohlcv_api.main import app as main_app


class TestMainApplication:
    """Test the main application module."""
    
    def test_main_app_exists(self):
        """Test that main app is available."""
        assert main_app is not None
        assert hasattr(main_app, 'routes')
    
    def test_main_app_is_fastapi_instance(self):
        """Test that main app is a FastAPI instance."""
        from fastapi import FastAPI
        assert isinstance(main_app, FastAPI)
    
    def test_main_app_has_basic_routes(self):
        """Test that main app has basic routes."""
        client = TestClient(main_app)
        
        # Health check should be available
        response = client.get("/health")
        assert response.status_code == 200
        
        # Root endpoint should be available
        response = client.get("/")
        assert response.status_code == 200


class TestGatewayIntegration:
    """Test gateway integration and functionality."""
    
    def test_gateway_creation(self):
        """Test basic gateway creation."""
        gateway = FullonOhlcvGateway()
        assert gateway is not None
        assert gateway.title == "fullon_ohlcv_api"
        assert gateway.version == "0.1.0"
        assert gateway.prefix == ""
    
    def test_gateway_with_custom_params(self):
        """Test gateway creation with custom parameters."""
        gateway = FullonOhlcvGateway(
            title="Custom OHLCV API",
            description="Custom description",
            version="1.0.0",
            prefix="/custom"
        )
        assert gateway.title == "Custom OHLCV API"
        assert gateway.description == "Custom description"
        assert gateway.version == "1.0.0"
        assert gateway.prefix == "/custom"
    
    def test_get_app(self, gateway):
        """Test getting FastAPI app from gateway."""
        app = gateway.get_app()
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)
        assert app.title == "Test OHLCV API"
    
    def test_get_routers(self, gateway):
        """Test getting routers from gateway."""
        routers = gateway.get_routers()
        assert isinstance(routers, list)
        # Should return all 6 routers for composition
        assert len(routers) == 6
        # Verify they are actual router instances
        from fastapi import APIRouter
        for router in routers:
            assert isinstance(router, APIRouter)
    
    def test_app_caching(self, gateway):
        """Test that app instance is cached."""
        app1 = gateway.get_app()
        app2 = gateway.get_app()
        assert app1 is app2  # Same instance


class TestBasicEndpoints:
    """Test basic endpoints available in all configurations."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fullon_ohlcv_api"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "fullon_ohlcv_api"
        assert data["description"] == "FastAPI Gateway for OHLCV market data"
        assert "docs_url" in data
        assert "health_url" in data
    
    def test_docs_endpoint(self, client):
        """Test documentation endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
    
    def test_openapi_endpoint(self, client):
        """Test OpenAPI specification endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert openapi_spec["info"]["title"] == "Test OHLCV API"
        assert openapi_spec["info"]["version"] == "0.1.0-test"


class TestPrefixedEndpoints:
    """Test endpoints with custom prefix."""
    
    def test_prefixed_health_endpoint(self, prefixed_client):
        """Test health check endpoint with prefix."""
        response = prefixed_client.get("/ohlcv/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fullon_ohlcv_api"
    
    def test_prefixed_root_endpoint(self, prefixed_client):
        """Test root endpoint with prefix."""
        response = prefixed_client.get("/ohlcv/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "fullon_ohlcv_api"
        assert data["docs_url"] == "/ohlcv/docs"
        assert data["health_url"] == "/ohlcv/health"
    
    def test_prefixed_docs_endpoint(self, prefixed_client):
        """Test documentation endpoint with prefix."""
        response = prefixed_client.get("/ohlcv/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
    
    def test_unprefixed_endpoints_not_available(self, prefixed_client):
        """Test that unprefixed endpoints are not available when prefix is set."""
        # These should return 404 when prefix is configured
        response = prefixed_client.get("/health")
        assert response.status_code == 404
        
        response = prefixed_client.get("/")
        assert response.status_code == 404


class TestLibraryInterface:
    """Test the public library interface."""
    
    def test_get_all_routers_function(self):
        """Test get_all_routers function."""
        routers = get_all_routers()
        assert isinstance(routers, list)
        # Should return all 6 routers for composition
        assert len(routers) == 6
        # Verify they are actual router instances
        from fastapi import APIRouter
        for router in routers:
            assert isinstance(router, APIRouter)
    
    def test_public_exports(self):
        """Test that public exports are available."""
        from fullon_ohlcv_api import FullonOhlcvGateway, get_all_routers
        
        # Should not raise ImportError
        assert FullonOhlcvGateway is not None
        assert get_all_routers is not None


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test endpoints using async client."""
    
    async def test_async_health_endpoint(self, async_client):
        """Test health endpoint with async client."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fullon_ohlcv_api"
    
    async def test_async_root_endpoint(self, async_client):
        """Test root endpoint with async client."""
        response = await async_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "fullon_ohlcv_api"
        assert "docs_url" in data


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_404_endpoint(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test method not allowed responses."""
        response = client.post("/health")  # Health endpoint is GET only
        assert response.status_code == 405