
import pytest
from pydantic import ValidationError
from datetime import datetime, timezone, timedelta
from typing import List

# Import the models to be tested
from fullon_ohlcv_api.models.requests import (
    TradeRangeRequest,
    PaginationRequest,
    TimeframeRequest,
    ExchangeSymbolRequest,
)
from fullon_ohlcv_api.models.responses import (
    TradesResponse,
    CandlesResponse,
    ExchangesResponse,
    ErrorResponse,
)

# Mock OHLCV models from fullon_ohlcv
class MockOHLCVTrade:
    def __init__(self, timestamp, price, volume, side):
        self.timestamp = timestamp
        self.price = price
        self.volume = volume
        self.side = side

class MockOHLCVCandle:
    def __init__(self, timestamp, open, high, low, close, volume, closed, timeframe):
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.closed = closed
        self.timeframe = timeframe


def test_trade_range_request_valid():
    start_time = datetime.now(timezone.utc) - timedelta(days=1)
    end_time = datetime.now(timezone.utc)
    request = TradeRangeRequest(start_time=start_time, end_time=end_time)
    assert request.start_time == start_time
    assert request.end_time == end_time

def test_trade_range_request_invalid_range():
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValidationError):
        TradeRangeRequest(start_time=start_time, end_time=end_time)

def test_trade_range_request_naive_datetime():
    start_time = datetime.now() - timedelta(days=1)
    end_time = datetime.now()
    with pytest.raises(ValidationError):
        TradeRangeRequest(start_time=start_time, end_time=end_time)

def test_pagination_request_valid():
    request = PaginationRequest(limit=100, offset=0)
    assert request.limit == 100
    assert request.offset == 0

def test_pagination_request_invalid_limit():
    with pytest.raises(ValidationError):
        PaginationRequest(limit=0)
    with pytest.raises(ValidationError):
        PaginationRequest(limit=5001)

def test_timeframe_request_valid():
    request = TimeframeRequest(timeframe="1h")
    assert request.timeframe == "1h"

def test_timeframe_request_invalid():
    with pytest.raises(ValidationError):
        TimeframeRequest(timeframe="invalid")

def test_exchange_symbol_request_valid():
    request = ExchangeSymbolRequest(exchange="binance", symbol="BTC/USDT")
    assert request.exchange == "binance"
    assert request.symbol == "BTC/USDT"

def test_trades_response_valid():
    trades = [
        MockOHLCVTrade(datetime.now(timezone.utc), 50000.0, 1.0, "buy"),
        MockOHLCVTrade(datetime.now(timezone.utc), 50001.0, 0.5, "sell"),
    ]
    response = TradesResponse(trades=trades, count=len(trades))
    assert response.count == 2
    assert len(response.trades) == 2

def test_candles_response_valid():
    candles = [
        MockOHLCVCandle(
            datetime.now(timezone.utc),
            50000.0,
            50100.0,
            49900.0,
            50050.0,
            100.0,
            True,
            "1h",
        )
    ]
    response = CandlesResponse(candles=candles, count=len(candles))
    assert response.count == 1
    assert len(response.candles) == 1

def test_exchanges_response_valid():
    exchanges = ["binance", "coinbase"]
    response = ExchangesResponse(exchanges=exchanges, count=len(exchanges))
    assert response.count == 2
    assert response.exchanges == exchanges

def test_error_response_valid():
    response = ErrorResponse(detail="Not Found")
    assert response.detail == "Not Found"
