"""SDK-specific exceptions for the fullon_ohlcv_api SDK."""


class FullonOhlcvError(Exception):
    """Base exception class for all SDK errors."""

    pass


class APIConnectionError(FullonOhlcvError):
    """Raised when there are connection issues with the API."""

    pass


class ExchangeNotFoundError(FullonOhlcvError):
    """Raised when the specified exchange is not found."""

    pass


class SymbolNotFoundError(FullonOhlcvError):
    """Raised when the specified symbol is not found."""

    pass


class TimeframeError(FullonOhlcvError):
    """Raised when an invalid timeframe is specified."""

    pass


class DeserializationError(FullonOhlcvError):
    """Raised when JSON response cannot be converted to fullon_ohlcv objects."""

    pass
