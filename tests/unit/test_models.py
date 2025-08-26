"""
Test suite for fullon_ohlcv_api Pydantic models.

This module tests all request and response models following TDD principles,
ensuring proper validation, serialization, and compatibility with examples.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from pydantic import ValidationError

# Import models to be implemented
from fullon_ohlcv_api.models.requests import (
    PaginationRequest,
    TradeRangeRequest,
    CandleRangeRequest,
    TimeseriesRequest,
    WebSocketSubscription,
)
from fullon_ohlcv_api.models.responses import (
    TradesResponse,
    CandlesResponse,
    TimeseriesResponse,
    WebSocketUpdate,
    ErrorResponse,
)


class TestPaginationRequest:
    """Test pagination request model."""
    
    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        request = PaginationRequest(limit=100)
        assert request.limit == 100
        assert request.offset == 0  # Default value
        
    def test_pagination_with_offset(self):
        """Test pagination with offset."""
        request = PaginationRequest(limit=50, offset=25)
        assert request.limit == 50
        assert request.offset == 25
        
    def test_limit_validation_minimum(self):
        """Test limit minimum validation."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationRequest(limit=0)
        assert "Input should be greater than or equal to 1" in str(exc_info.value)
        
    def test_limit_validation_maximum(self):
        """Test limit maximum validation."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationRequest(limit=5001)
        assert "Input should be less than or equal to 5000" in str(exc_info.value)
        
    def test_offset_validation_minimum(self):
        """Test offset minimum validation."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationRequest(limit=100, offset=-1)
        assert "Input should be greater than or equal to 0" in str(exc_info.value)
        
    def test_default_values(self):
        """Test default values are set correctly."""
        request = PaginationRequest()
        assert request.limit == 100
        assert request.offset == 0


class TestTradeRangeRequest:
    """Test trade range request model."""
    
    def test_valid_trade_range(self):
        """Test valid trade range request."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        request = TradeRangeRequest(
            exchange="binance",
            symbol="BTC/USDT",
            start_time=start_time,
            end_time=end_time,
            limit=100
        )
        
        assert request.exchange == "binance"
        assert request.symbol == "BTC/USDT"
        assert request.start_time == start_time
        assert request.end_time == end_time
        assert request.limit == 100
        
    def test_optional_time_range(self):
        """Test trade range request with optional time parameters."""
        request = TradeRangeRequest(
            exchange="coinbase",
            symbol="ETH/USD"
        )
        
        assert request.exchange == "coinbase"
        assert request.symbol == "ETH/USD"
        assert request.start_time is None
        assert request.end_time is None
        assert request.limit == 100  # Default
        
    def test_timezone_aware_required(self):
        """Test that timezone-aware datetimes are required."""
        naive_datetime = datetime.now()  # No timezone
        
        with pytest.raises(ValidationError) as exc_info:
            TradeRangeRequest(
                exchange="binance",
                symbol="BTC/USDT",
                start_time=naive_datetime
            )
        assert "timezone" in str(exc_info.value).lower()
        
    def test_exchange_validation(self):
        """Test exchange name validation."""
        with pytest.raises(ValidationError) as exc_info:
            TradeRangeRequest(exchange="", symbol="BTC/USDT")
        assert "String should have at least 1 character" in str(exc_info.value)
        
    def test_symbol_validation(self):
        """Test symbol validation."""
        with pytest.raises(ValidationError) as exc_info:
            TradeRangeRequest(exchange="binance", symbol="")
        assert "String should have at least 1 character" in str(exc_info.value)


class TestCandleRangeRequest:
    """Test candle range request model."""
    
    def test_valid_candle_range(self):
        """Test valid candle range request."""
        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        end_time = datetime.now(timezone.utc)
        
        request = CandleRangeRequest(
            exchange="binance",
            symbol="ETH/USDT",
            timeframe="1h",
            start_time=start_time,
            end_time=end_time,
            limit=24
        )
        
        assert request.exchange == "binance"
        assert request.symbol == "ETH/USDT"
        assert request.timeframe == "1h"
        assert request.start_time == start_time
        assert request.end_time == end_time
        assert request.limit == 24
        
    def test_timeframe_validation(self):
        """Test timeframe validation."""
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        
        for tf in valid_timeframes:
            request = CandleRangeRequest(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe=tf
            )
            assert request.timeframe == tf
            
    def test_invalid_timeframe(self):
        """Test invalid timeframe validation."""
        with pytest.raises(ValidationError) as exc_info:
            CandleRangeRequest(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="invalid"
            )
        assert "timeframe" in str(exc_info.value).lower()


class TestTimeseriesRequest:
    """Test timeseries request model."""
    
    def test_valid_timeseries_request(self):
        """Test valid timeseries request."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        request = TimeseriesRequest(
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            start_time=start_time,
            end_time=end_time,
            limit=60
        )
        
        assert request.exchange == "binance"
        assert request.symbol == "BTC/USDT"
        assert request.timeframe == "1m"
        assert request.start_time == start_time
        assert request.end_time == end_time
        assert request.limit == 60
        
    def test_default_values(self):
        """Test default values for timeseries request."""
        request = TimeseriesRequest(
            exchange="coinbase",
            symbol="ETH/USD",
            timeframe="5m"
        )
        
        assert request.limit == 100  # Default
        assert request.start_time is None
        assert request.end_time is None


class TestWebSocketSubscription:
    """Test WebSocket subscription model."""
    
    def test_valid_subscription(self):
        """Test valid WebSocket subscription."""
        subscription = WebSocketSubscription(
            action="subscribe",
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            type="ohlcv_live"
        )
        
        assert subscription.action == "subscribe"
        assert subscription.exchange == "binance"
        assert subscription.symbol == "BTC/USDT"
        assert subscription.timeframe == "1m"
        assert subscription.type == "ohlcv_live"
        
    def test_valid_unsubscription(self):
        """Test valid WebSocket unsubscription."""
        unsubscription = WebSocketSubscription(
            action="unsubscribe",
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            type="ohlcv_live"
        )
        
        assert unsubscription.action == "unsubscribe"
        
    def test_action_validation(self):
        """Test action validation."""
        valid_actions = ["subscribe", "unsubscribe"]
        
        for action in valid_actions:
            subscription = WebSocketSubscription(
                action=action,
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                type="ohlcv_live"
            )
            assert subscription.action == action
            
    def test_invalid_action(self):
        """Test invalid action validation."""
        with pytest.raises(ValidationError) as exc_info:
            WebSocketSubscription(
                action="invalid",
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                type="ohlcv_live"
            )
        assert "action" in str(exc_info.value).lower()
        
    def test_type_validation(self):
        """Test subscription type validation."""
        valid_types = ["ohlcv_live", "trade_live", "candle_live"]
        
        for sub_type in valid_types:
            subscription = WebSocketSubscription(
                action="subscribe",
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                type=sub_type
            )
            assert subscription.type == sub_type


class TestTradesResponse:
    """Test trades response model."""
    
    def test_valid_trades_response(self, sample_trades_bulk):
        """Test valid trades response."""
        trades_data = sample_trades_bulk["trades"]
        
        response = TradesResponse(
            trades=trades_data,
            count=len(trades_data),
            exchange="binance",
            symbol="BTC/USDT"
        )
        
        assert response.trades == trades_data
        assert response.count == 2
        assert response.exchange == "binance"
        assert response.symbol == "BTC/USDT"
        assert response.success is True  # Default
        
    def test_empty_trades_response(self):
        """Test empty trades response."""
        response = TradesResponse(
            trades=[],
            count=0,
            exchange="coinbase",
            symbol="ETH/USD"
        )
        
        assert response.trades == []
        assert response.count == 0
        assert response.success is True
        
    def test_trades_response_with_metadata(self):
        """Test trades response with additional metadata."""
        response = TradesResponse(
            trades=[],
            count=0,
            exchange="binance",
            symbol="BTC/USDT",
            success=False,
            message="No trades found in range"
        )
        
        assert response.success is False
        assert response.message == "No trades found in range"


class TestCandlesResponse:
    """Test candles response model."""
    
    def test_valid_candles_response(self, sample_candle_data):
        """Test valid candles response."""
        candles_data = [sample_candle_data]
        
        response = CandlesResponse(
            candles=candles_data,
            count=len(candles_data),
            exchange="binance",
            symbol="ETH/USDT",
            timeframe="1h"
        )
        
        assert response.candles == candles_data
        assert response.count == 1
        assert response.exchange == "binance"
        assert response.symbol == "ETH/USDT"
        assert response.timeframe == "1h"
        assert response.success is True
        
    def test_candles_response_pagination(self):
        """Test candles response with pagination info."""
        response = CandlesResponse(
            candles=[],
            count=0,
            exchange="coinbase",
            symbol="BTC/USD",
            timeframe="5m",
            offset=100,
            limit=50,
            total_available=500
        )
        
        assert response.offset == 100
        assert response.limit == 50
        assert response.total_available == 500


class TestTimeseriesResponse:
    """Test timeseries response model."""
    
    def test_valid_timeseries_response(self):
        """Test valid timeseries response."""
        ohlcv_data = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "open": 45000.0,
                "high": 45100.0,
                "low": 44900.0,
                "close": 45050.0,
                "volume": 10.5
            }
        ]
        
        response = TimeseriesResponse(
            ohlcv=ohlcv_data,
            count=len(ohlcv_data),
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m"
        )
        
        assert response.ohlcv == ohlcv_data
        assert response.count == 1
        assert response.exchange == "binance"
        assert response.symbol == "BTC/USDT"
        assert response.timeframe == "1m"
        
    def test_timeseries_response_with_range(self):
        """Test timeseries response with time range."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        response = TimeseriesResponse(
            ohlcv=[],
            count=0,
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="5m",
            start_time=start_time,
            end_time=end_time
        )
        
        assert response.start_time == start_time
        assert response.end_time == end_time


class TestWebSocketUpdate:
    """Test WebSocket update model."""
    
    def test_valid_websocket_update(self):
        """Test valid WebSocket update."""
        ohlcv_data = {
            "timestamp": "2024-01-01T12:00:00Z",
            "open": 45000.0,
            "high": 45100.0,
            "low": 44900.0,
            "close": 45050.0,
            "volume": 10.5,
            "is_final": True
        }
        
        update = WebSocketUpdate(
            type="ohlcv_update",
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            data=ohlcv_data,
            timestamp=datetime.now(timezone.utc)
        )
        
        assert update.type == "ohlcv_update"
        assert update.exchange == "binance"
        assert update.symbol == "BTC/USDT"
        assert update.timeframe == "1m"
        assert update.data == ohlcv_data
        assert isinstance(update.timestamp, datetime)
        
    def test_websocket_error_update(self):
        """Test WebSocket error update."""
        update = WebSocketUpdate(
            type="error",
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            data={"message": "Invalid subscription"},
            timestamp=datetime.now(timezone.utc)
        )
        
        assert update.type == "error"
        assert update.data["message"] == "Invalid subscription"


class TestErrorResponse:
    """Test error response model."""
    
    def test_valid_error_response(self):
        """Test valid error response."""
        error = ErrorResponse(
            error="ValidationError",
            message="Invalid exchange name",
            status_code=400
        )
        
        assert error.error == "ValidationError"
        assert error.message == "Invalid exchange name"
        assert error.status_code == 400
        assert error.success is False
        
    def test_error_response_with_details(self):
        """Test error response with additional details."""
        error = ErrorResponse(
            error="NotFound",
            message="Exchange not found",
            status_code=404,
            details={"exchange": "invalid_exchange", "available": ["binance", "coinbase"]}
        )
        
        assert error.details["exchange"] == "invalid_exchange"
        assert "binance" in error.details["available"]
        
    def test_error_response_with_timestamp(self):
        """Test error response includes timestamp."""
        error = ErrorResponse(
            error="ServerError",
            message="Internal server error",
            status_code=500
        )
        
        assert isinstance(error.timestamp, datetime)
        assert error.timestamp.tzinfo == timezone.utc


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_request_model_json_serialization(self):
        """Test request model JSON serialization."""
        start_time = datetime.now(timezone.utc)
        request = TradeRangeRequest(
            exchange="binance",
            symbol="BTC/USDT",
            start_time=start_time,
            limit=100
        )
        
        json_data = request.model_dump_json()
        assert isinstance(json_data, str)
        
        # Test deserialization
        parsed_request = TradeRangeRequest.model_validate_json(json_data)
        assert parsed_request.exchange == "binance"
        assert parsed_request.symbol == "BTC/USDT"
        assert parsed_request.limit == 100
        
    def test_response_model_json_serialization(self):
        """Test response model JSON serialization."""
        response = TradesResponse(
            trades=[],
            count=0,
            exchange="binance",
            symbol="BTC/USDT"
        )
        
        json_data = response.model_dump_json()
        assert isinstance(json_data, str)
        
        # Test deserialization
        parsed_response = TradesResponse.model_validate_json(json_data)
        assert parsed_response.exchange == "binance"
        assert parsed_response.count == 0


class TestUtcTimestampHandling:
    """Test UTC timestamp handling across all models."""
    
    def test_utc_timestamp_validation(self):
        """Test that all datetime fields require UTC timezone."""
        utc_time = datetime.now(timezone.utc)
        
        # Test request model
        request = TradeRangeRequest(
            exchange="binance",
            symbol="BTC/USDT",
            start_time=utc_time,
            end_time=utc_time
        )
        
        assert request.start_time.tzinfo == timezone.utc
        assert request.end_time.tzinfo == timezone.utc
        
    def test_naive_datetime_rejection(self):
        """Test that naive datetimes are rejected."""
        naive_time = datetime.now()  # No timezone
        
        with pytest.raises(ValidationError):
            TradeRangeRequest(
                exchange="binance",
                symbol="BTC/USDT",
                start_time=naive_time
            )
            
    def test_non_utc_timezone_conversion(self):
        """Test that non-UTC timezones are handled properly."""
        from datetime import timezone, timedelta
        
        # Create a non-UTC timezone
        est_tz = timezone(timedelta(hours=-5))
        est_time = datetime.now(est_tz)
        
        request = TradeRangeRequest(
            exchange="binance",
            symbol="BTC/USDT",
            start_time=est_time
        )
        
        # Should be converted to UTC or at least timezone-aware
        assert request.start_time.tzinfo is not None


class TestExamplesCompatibility:
    """Test compatibility with examples API requirements."""
    
    def test_trade_repository_example_compatibility(self):
        """Test models work with trade_repository_example.py requirements."""
        # Test /api/trades/{exchange}/{symbol} endpoint params
        request = PaginationRequest(limit=10)
        assert request.limit == 10
        
        # Test /api/trades/{exchange}/{symbol}/range endpoint params
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        range_request = TradeRangeRequest(
            exchange="binance",
            symbol="BTC/USDT",
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify response model structure matches example expectations
        response = TradesResponse(
            trades=[],
            count=0,
            exchange="binance",
            symbol="BTC/USDT"
        )
        
        response_dict = response.model_dump()
        assert "trades" in response_dict
        assert "count" in response_dict
        
    def test_candle_repository_example_compatibility(self):
        """Test models work with candle_repository_example.py requirements."""
        # Test /api/candles/{exchange}/{symbol}/{timeframe} endpoint
        request = CandleRangeRequest(
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1h",
            limit=10
        )
        
        response = CandlesResponse(
            candles=[],
            count=0,
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1h"
        )
        
        response_dict = response.model_dump()
        assert "candles" in response_dict
        
    def test_timeseries_repository_example_compatibility(self):
        """Test models work with timeseries_repository_example.py requirements."""
        # Test /api/timeseries/{exchange}/{symbol}/ohlcv endpoint
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        request = TimeseriesRequest(
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            start_time=start_time,
            end_time=end_time,
            limit=10
        )
        
        response = TimeseriesResponse(
            ohlcv=[],
            count=0,
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m"
        )
        
        response_dict = response.model_dump()
        assert "ohlcv" in response_dict
        
    def test_websocket_example_compatibility(self):
        """Test models work with websocket_live_ohlcv_example.py requirements."""
        # Test subscription message
        subscription = WebSocketSubscription(
            action="subscribe",
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            type="ohlcv_live"
        )
        
        # Test update message
        ohlcv_data = {
            "timestamp": "2024-01-01T12:00:00Z",
            "close": 45000.0,
            "volume": 10.5,
            "is_final": False
        }
        
        update = WebSocketUpdate(
            type="ohlcv_update",
            exchange="binance",
            symbol="BTC/USDT",
            timeframe="1m",
            data=ohlcv_data,
            timestamp=datetime.now(timezone.utc)
        )
        
        update_dict = update.model_dump()
        assert "type" in update_dict
        assert "data" in update_dict
        assert update_dict["data"]["close"] == 45000.0