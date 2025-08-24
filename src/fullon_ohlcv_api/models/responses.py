from typing import Any

from pydantic import BaseModel


class TradesResponse(BaseModel):
    trades: list[Any]  # Using Any for now, will be replaced with OHLCVTrade
    count: int


class CandlesResponse(BaseModel):
    candles: list[Any]  # Using Any for now, will be replaced with OHLCVCandle
    count: int


class ExchangesResponse(BaseModel):
    exchanges: list[str]
    count: int


class ErrorResponse(BaseModel):
    detail: str
