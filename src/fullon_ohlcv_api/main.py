"""
Legacy main.py - kept for backwards compatibility.

For new usage, prefer:
- Library usage: from fullon_ohlcv_api import FullonOhlcvGateway
- Standalone server: python -m fullon_ohlcv_api.standalone_server
"""

from .gateway import FullonOhlcvGateway

# Create gateway instance for backwards compatibility
_gateway = FullonOhlcvGateway()
app = _gateway.get_app()

# Export app for uvicorn compatibility
__all__ = ["app"]
