"""환율 서비스."""
from forex_python.converter import CurrencyRates
from functools import lru_cache
from datetime import datetime, timedelta

_cr = CurrencyRates()
_cache = {}


@lru_cache(maxsize=128)
def convert(amount: float, src: str, dst: str) -> float:
    if src == dst:
        return amount
    rate = _cr.get_rate(src, dst)
    return amount * rate 