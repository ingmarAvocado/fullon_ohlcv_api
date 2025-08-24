from datetime import datetime

from pydantic import BaseModel, Field, validator


class TradeRangeRequest(BaseModel):
    start_time: datetime
    end_time: datetime

    @validator("*", pre=True, allow_reuse=True)
    def check_tz_awareness(cls, v: datetime) -> datetime:
        if isinstance(v, datetime) and v.tzinfo is None:
            raise ValueError("Timezone-aware datetime required")
        return v

    @validator("end_time")
    def check_time_range(cls, v: datetime, values: dict[str, datetime]) -> datetime:
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class PaginationRequest(BaseModel):
    limit: int = Field(100, ge=1, le=5000)
    offset: int = Field(0, ge=0)


class TimeframeRequest(BaseModel):
    timeframe: str

    @validator("timeframe")
    def check_timeframe(cls, v: str) -> str:
        # This is a simplified check. A more robust implementation would
        # validate against a list of supported timeframes.
        if v not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            raise ValueError("Invalid timeframe")
        return v


class ExchangeSymbolRequest(BaseModel):
    exchange: str
    symbol: str
