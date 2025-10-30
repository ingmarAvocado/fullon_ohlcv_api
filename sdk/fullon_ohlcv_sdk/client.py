"""Async HTTP client for the fullon_ohlcv_api."""

import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import httpx

from fullon_ohlcv.models import Trade, Candle
from .models import json_list_to_trades, json_list_to_candles
from .exceptions import (
    FullonOhlcvError,
    APIConnectionError,
    ExchangeNotFoundError,
    SymbolNotFoundError,
    TimeframeError,
)


class FullonOhlcvClient:
    """Async client for the fullon_ohlcv_api.

    Provides a Pythonic interface that returns fullon_ohlcv objects
    instead of raw JSON responses.
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the client.

        Args:
            base_url: Base URL of the fullon_ohlcv_api server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the HTTP client session."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """Close the HTTP client session."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising error if not started."""
        if self._client is None:
            raise RuntimeError(
                "Client not started. Use 'async with client:' or call start() first."
            )
        return self._client

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request and handle common errors."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        client = self._get_client()

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            raise APIConnectionError(f"Request timeout: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection failed: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Try to determine the type of 404
                if "exchange" in endpoint.lower():
                    raise ExchangeNotFoundError(
                        f"Exchange not found in URL: {url}"
                    ) from e
                elif "symbol" in endpoint.lower():
                    raise SymbolNotFoundError(f"Symbol not found in URL: {url}") from e
                else:
                    raise FullonOhlcvError(f"Resource not found: {url}") from e
            elif e.response.status_code == 400:
                raise FullonOhlcvError(f"Bad request: {e.response.text}") from e
            else:
                raise FullonOhlcvError(
                    f"HTTP {e.response.status_code}: {e.response.text}"
                ) from e
        except Exception as e:
            raise FullonOhlcvError(f"Request failed: {e}") from e

    async def get_trades(
        self,
        exchange: str,
        symbol: str,
        limit: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Trade]:
        """Get recent trades for an exchange/symbol pair.

        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading pair (e.g., 'BTC/USDT')
            limit: Maximum number of trades to return
            start_time: Start time for range query (ISO format)
            end_time: End time for range query (ISO format)

        Returns:
            List[Trade]: List of Trade objects

        Raises:
            ExchangeNotFoundError: If exchange doesn't exist
            SymbolNotFoundError: If symbol doesn't exist
            APIConnectionError: If connection fails
        """
        if start_time or end_time:
            # Range query
            endpoint = f"api/trades/{exchange}/{symbol}/range"
            params = {}
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            if limit:
                params["limit"] = limit
        else:
            # Recent trades
            endpoint = f"api/trades/{exchange}/{symbol}"
            params = {}
            if limit:
                params["limit"] = limit

        data = await self._make_request("GET", endpoint, params=params)
        trades_data = data.get("trades", [])
        return json_list_to_trades(trades_data)

    async def get_candles(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        limit: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Candle]:
        """Get OHLCV candles for an exchange/symbol/timeframe.

        Args:
            exchange: Exchange name (e.g., 'binance')
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '1h', '1d')
            limit: Maximum number of candles to return
            start_time: Start time for range query (ISO format)
            end_time: End time for range query (ISO format)

        Returns:
            List[Candle]: List of Candle objects

        Raises:
            ExchangeNotFoundError: If exchange doesn't exist
            SymbolNotFoundError: If symbol doesn't exist
            TimeframeError: If timeframe is invalid
            APIConnectionError: If connection fails
        """
        # Validate timeframe format
        if not timeframe or not isinstance(timeframe, str):
            raise TimeframeError(f"Invalid timeframe: {timeframe}")

        if start_time or end_time:
            # Range query
            endpoint = f"api/candles/{exchange}/{symbol}/{timeframe}/range"
            params = {}
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            if limit:
                params["limit"] = limit
        else:
            # Recent candles
            endpoint = f"api/candles/{exchange}/{symbol}/{timeframe}"
            params = {}
            if limit:
                params["limit"] = limit

        data = await self._make_request("GET", endpoint, params=params)
        candles_data = data.get("candles", [])
        return json_list_to_candles(candles_data)

    async def get_ohlcv_timeseries(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Candle]:
        """Get OHLCV timeseries data (aggregated candles).

        Args:
            exchange: Exchange name
            symbol: Trading pair
            timeframe: Timeframe for aggregation
            start_time: Start time (ISO format)
            end_time: End time (ISO format)

        Returns:
            List[Candle]: List of aggregated Candle objects
        """
        endpoint = f"api/timeseries/{exchange}/{symbol}/ohlcv"
        params = {"timeframe": timeframe}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        data = await self._make_request("GET", endpoint, params=params)
        candles_data = data.get("candles", [])
        return json_list_to_candles(candles_data)

    async def get_exchanges(self) -> List[str]:
        """Get list of available exchanges.

        Returns:
            List[str]: List of exchange names
        """
        data = await self._make_request("GET", "api/exchanges")
        return data.get("exchanges", [])

    async def get_exchange_symbols(self, exchange: str) -> List[str]:
        """Get list of available symbols for an exchange.

        Args:
            exchange: Exchange name

        Returns:
            List[str]: List of symbol names
        """
        data = await self._make_request("GET", f"api/exchanges/{exchange}/symbols")
        return data.get("symbols", [])
