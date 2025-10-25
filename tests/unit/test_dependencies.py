"""
Tests for database dependencies in fullon_ohlcv_api.

This module tests FastAPI dependency injection for database repositories,
following TDD principles and comprehensive error handling coverage.
"""

import pytest
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fullon_ohlcv.repositories.ohlcv import (
    TradeRepository,
    CandleRepository,
    TimeseriesRepository,
)

from fullon_ohlcv_api.dependencies.database import (
    get_trade_repository,
    get_candle_repository,
    get_timeseries_repository,
    validate_exchange_symbol,
)


class TestValidateExchangeSymbol:
    """Test exchange and symbol validation function."""

    def test_valid_exchange_symbol(self):
        """Test validation passes for valid exchange and symbol."""
        # Should not raise any exception
        validate_exchange_symbol("binance", "BTC/USDT")
        validate_exchange_symbol("coinbase", "ETH/USD")
        validate_exchange_symbol("kraken", "BTC/EUR")

    def test_empty_exchange(self):
        """Test validation fails for empty exchange."""
        with pytest.raises(HTTPException) as exc_info:
            validate_exchange_symbol("", "BTC/USDT")
        
        assert exc_info.value.status_code == 422
        assert "Exchange cannot be empty" in exc_info.value.detail

    def test_whitespace_exchange(self):
        """Test validation fails for whitespace-only exchange."""
        with pytest.raises(HTTPException) as exc_info:
            validate_exchange_symbol("   ", "BTC/USDT")
        
        assert exc_info.value.status_code == 422
        assert "Exchange cannot be empty" in exc_info.value.detail

    def test_empty_symbol(self):
        """Test validation fails for empty symbol."""
        with pytest.raises(HTTPException) as exc_info:
            validate_exchange_symbol("binance", "")
        
        assert exc_info.value.status_code == 422
        assert "Symbol cannot be empty" in exc_info.value.detail

    def test_whitespace_symbol(self):
        """Test validation fails for whitespace-only symbol."""
        with pytest.raises(HTTPException) as exc_info:
            validate_exchange_symbol("binance", "   ")
        
        assert exc_info.value.status_code == 422
        assert "Symbol cannot be empty" in exc_info.value.detail

    def test_none_exchange(self):
        """Test validation fails for None exchange."""
        with pytest.raises(HTTPException) as exc_info:
            validate_exchange_symbol(None, "BTC/USDT")
        
        assert exc_info.value.status_code == 422

    def test_none_symbol(self):
        """Test validation fails for None symbol."""
        with pytest.raises(HTTPException) as exc_info:
            validate_exchange_symbol("binance", None)
        
        assert exc_info.value.status_code == 422


class TestGetTradeRepository:
    """Test get_trade_repository dependency function."""

    @pytest.mark.asyncio
    async def test_successful_repository_creation(self):
        """Test successful TradeRepository creation and cleanup."""
        exchange = "binance"
        symbol = "BTC/USDT"

        # Mock TradeRepository
        mock_repo = AsyncMock(spec=TradeRepository)
        mock_repo.__aenter__ = AsyncMock(return_value=mock_repo)
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class:
            mock_class.return_value = mock_repo

            # Use the dependency as async generator
            dependency_gen = get_trade_repository(exchange, symbol)
            
            try:
                repo = await dependency_gen.__anext__()
                
                # Verify repository was created correctly
                mock_class.assert_called_once_with(exchange, symbol)
                assert repo == mock_repo
                
                # Verify context manager was entered
                mock_repo.__aenter__.assert_called_once()
                
                # Trigger generator cleanup
                try:
                    await dependency_gen.__anext__()
                except StopAsyncIteration:
                    pass
                
            finally:
                await dependency_gen.aclose()

        # Verify context manager was exited
        mock_repo.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_repository_creation_failure(self):
        """Test handling of TradeRepository creation failure."""
        exchange = "invalid_exchange"
        symbol = "BTC/USDT"

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class:
            mock_class.side_effect = Exception("Database connection failed")

            dependency_gen = get_trade_repository(exchange, symbol)
            
            with pytest.raises(HTTPException) as exc_info:
                await dependency_gen.__anext__()
            
            assert exc_info.value.status_code == 500
            assert "Database connection error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_repository_context_enter_failure(self):
        """Test handling of context manager entry failure."""
        exchange = "binance"
        symbol = "BTC/USDT"

        mock_repo = AsyncMock(spec=TradeRepository)
        mock_repo.__aenter__ = AsyncMock(side_effect=Exception("Context entry failed"))
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class:
            mock_class.return_value = mock_repo

            dependency_gen = get_trade_repository(exchange, symbol)
            
            with pytest.raises(HTTPException) as exc_info:
                await dependency_gen.__anext__()
            
            assert exc_info.value.status_code == 500
            assert "Repository initialization error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_proper_cleanup_on_exception(self):
        """Test that cleanup happens even when exception occurs."""
        exchange = "binance"
        symbol = "BTC/USDT"

        mock_repo = AsyncMock(spec=TradeRepository)
        mock_repo.__aenter__ = AsyncMock(return_value=mock_repo)
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class:
            mock_class.return_value = mock_repo

            dependency_gen = get_trade_repository(exchange, symbol)
            
            try:
                repo = await dependency_gen.__anext__()
                # Simulate exception during usage by throwing to generator
                await dependency_gen.athrow(RuntimeError("Simulated error"))
            except RuntimeError:
                pass  # Expected
            except HTTPException:
                # The dependency wraps exceptions in HTTPException, this is expected
                pass
            except StopAsyncIteration:
                pass  # Generator cleanup

        # Verify cleanup happened
        mock_repo.__aexit__.assert_called_once()


class TestGetCandleRepository:
    """Test get_candle_repository dependency function."""

    @pytest.mark.asyncio
    async def test_successful_repository_creation(self):
        """Test successful CandleRepository creation and cleanup."""
        exchange = "binance"
        symbol = "ETH/USDT"

        mock_repo = AsyncMock(spec=CandleRepository)
        mock_repo.__aenter__ = AsyncMock(return_value=mock_repo)
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.CandleRepository") as mock_class:
            mock_class.return_value = mock_repo

            dependency_gen = get_candle_repository(exchange, symbol)
            
            try:
                repo = await dependency_gen.__anext__()
                
                mock_class.assert_called_once_with(exchange, symbol)
                assert repo == mock_repo
                mock_repo.__aenter__.assert_called_once()
                
                try:
                    await dependency_gen.__anext__()
                except StopAsyncIteration:
                    pass
                
            finally:
                await dependency_gen.aclose()

        mock_repo.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_repository_creation_failure(self):
        """Test handling of CandleRepository creation failure."""
        exchange = "invalid_exchange"
        symbol = "ETH/USDT"

        with patch("fullon_ohlcv_api.dependencies.database.CandleRepository") as mock_class:
            mock_class.side_effect = Exception("Database connection failed")

            dependency_gen = get_candle_repository(exchange, symbol)
            
            with pytest.raises(HTTPException) as exc_info:
                await dependency_gen.__anext__()
            
            assert exc_info.value.status_code == 500
            assert "Database connection error" in exc_info.value.detail


class TestGetTimeseriesRepository:
    """Test get_timeseries_repository dependency function."""

    @pytest.mark.asyncio
    async def test_successful_repository_creation(self):
        """Test successful TimeseriesRepository creation and cleanup."""
        exchange = "binance"
        symbol = "BTC/USDT"

        mock_repo = AsyncMock(spec=TimeseriesRepository)
        mock_repo.__aenter__ = AsyncMock(return_value=mock_repo)
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.TimeseriesRepository") as mock_class:
            mock_class.return_value = mock_repo

            dependency_gen = get_timeseries_repository(exchange, symbol)
            
            try:
                repo = await dependency_gen.__anext__()
                
                mock_class.assert_called_once_with(exchange, symbol)
                assert repo == mock_repo
                mock_repo.__aenter__.assert_called_once()
                
                try:
                    await dependency_gen.__anext__()
                except StopAsyncIteration:
                    pass
                
            finally:
                await dependency_gen.aclose()

        mock_repo.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_repository_creation_failure(self):
        """Test handling of TimeseriesRepository creation failure."""
        exchange = "invalid_exchange" 
        symbol = "BTC/USDT"

        with patch("fullon_ohlcv_api.dependencies.database.TimeseriesRepository") as mock_class:
            mock_class.side_effect = Exception("Database connection failed")

            dependency_gen = get_timeseries_repository(exchange, symbol)
            
            with pytest.raises(HTTPException) as exc_info:
                await dependency_gen.__anext__()
            
            assert exc_info.value.status_code == 500
            assert "Database connection error" in exc_info.value.detail


class TestDependencyLogging:
    """Test logging behavior in dependencies."""

    @pytest.mark.asyncio
    async def test_successful_operation_logging(self):
        """Test that successful operations are logged correctly."""
        exchange = "binance"
        symbol = "BTC/USDT"

        mock_repo = AsyncMock(spec=TradeRepository)
        mock_repo.__aenter__ = AsyncMock(return_value=mock_repo)
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class, \
             patch("fullon_ohlcv_api.dependencies.database.logger") as mock_logger:
            
            mock_class.return_value = mock_repo

            dependency_gen = get_trade_repository(exchange, symbol)
            
            try:
                await dependency_gen.__anext__()
                try:
                    await dependency_gen.__anext__()
                except StopAsyncIteration:
                    pass
            finally:
                await dependency_gen.aclose()

            # Verify logging calls
            mock_logger.info.assert_any_call(
                "Creating TradeRepository",
                exchange=exchange,
                symbol=symbol
            )
            mock_logger.info.assert_any_call(
                "TradeRepository cleaned up",
                exchange=exchange,
                symbol=symbol
            )

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test that errors are logged correctly."""
        exchange = "invalid_exchange"
        symbol = "BTC/USDT"

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class, \
             patch("fullon_ohlcv_api.dependencies.database.logger") as mock_logger:
            
            mock_class.side_effect = Exception("Database connection failed")

            dependency_gen = get_trade_repository(exchange, symbol)
            
            with pytest.raises(HTTPException):
                await dependency_gen.__anext__()

            # Verify error logging
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to create TradeRepository" in call_args[0][0]
            assert call_args[1]["exchange"] == exchange
            assert call_args[1]["symbol"] == symbol


class TestDependencyConfiguration:
    """Test configuration-related aspects of dependencies."""

    @pytest.mark.asyncio
    async def test_production_mode_configuration(self):
        """Test that repositories are created in production mode by default."""
        exchange = "binance"
        symbol = "BTC/USDT"

        mock_repo = AsyncMock(spec=TradeRepository)
        mock_repo.__aenter__ = AsyncMock(return_value=mock_repo)
        mock_repo.__aexit__ = AsyncMock(return_value=None)

        with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class:
            mock_class.return_value = mock_repo

            dependency_gen = get_trade_repository(exchange, symbol)

            try:
                await dependency_gen.__anext__()

                # Verify test=False is the default (production mode)
                mock_class.assert_called_once_with(exchange, symbol)

                try:
                    await dependency_gen.__anext__()
                except StopAsyncIteration:
                    pass

            finally:
                await dependency_gen.aclose()

    def test_dependency_type_annotations(self):
        """Test that dependency functions have correct type annotations."""
        import inspect
        from typing import get_type_hints

        # Test get_trade_repository annotations
        hints = get_type_hints(get_trade_repository)
        assert "return" in hints
        
        # Test get_candle_repository annotations  
        hints = get_type_hints(get_candle_repository)
        assert "return" in hints
        
        # Test get_timeseries_repository annotations
        hints = get_type_hints(get_timeseries_repository)
        assert "return" in hints

    def test_validate_exchange_symbol_type_annotations(self):
        """Test that validation function has correct type annotations."""
        import inspect
        from typing import get_type_hints

        hints = get_type_hints(validate_exchange_symbol)
        # The function accepts Optional[str] which is str | None
        assert "exchange" in hints
        assert "symbol" in hints  
        assert hints.get("return") is type(None)


class TestDependencyIntegration:
    """Test integration aspects of dependencies."""

    @pytest.mark.asyncio
    async def test_multiple_repositories_concurrent(self):
        """Test that multiple repositories can be created concurrently."""
        import asyncio

        exchange = "binance"
        symbol1 = "BTC/USDT"
        symbol2 = "ETH/USDT"

        mock_repo1 = AsyncMock(spec=TradeRepository)
        mock_repo1.__aenter__ = AsyncMock(return_value=mock_repo1)
        mock_repo1.__aexit__ = AsyncMock(return_value=None)

        mock_repo2 = AsyncMock(spec=CandleRepository)
        mock_repo2.__aenter__ = AsyncMock(return_value=mock_repo2)
        mock_repo2.__aexit__ = AsyncMock(return_value=None)

        async def get_trade_repo():
            with patch("fullon_ohlcv_api.dependencies.database.TradeRepository") as mock_class:
                mock_class.return_value = mock_repo1
                dependency_gen = get_trade_repository(exchange, symbol1)
                try:
                    repo = await dependency_gen.__anext__()
                    await asyncio.sleep(0.1)  # Simulate work
                    return repo
                finally:
                    await dependency_gen.aclose()

        async def get_candle_repo():
            with patch("fullon_ohlcv_api.dependencies.database.CandleRepository") as mock_class:
                mock_class.return_value = mock_repo2
                dependency_gen = get_candle_repository(exchange, symbol2)
                try:
                    repo = await dependency_gen.__anext__()
                    await asyncio.sleep(0.1)  # Simulate work
                    return repo
                finally:
                    await dependency_gen.aclose()

        # Run concurrently
        trade_repo, candle_repo = await asyncio.gather(
            get_trade_repo(),
            get_candle_repo()
        )

        assert trade_repo == mock_repo1
        assert candle_repo == mock_repo2