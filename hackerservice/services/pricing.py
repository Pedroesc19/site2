# hackerservice/services/pricing.py

import time, requests, logging

_log = logging.getLogger(__name__)

API = "https://api.coingecko.com/api/v3/simple/price"
TTL = 60          # cache 1 minute
_cache = {}       # { "monero": (price, ts), "bitcoin": (price, ts) }

def _query(ids: str) -> dict:
    params = {"ids": ids, "vs_currencies": "usd"}
    return requests.get(API, params=params, timeout=5).json()

def _get(symbol: str, fallback: float) -> float:
    entry = _cache.get(symbol)
    if entry and time.time() - entry[1] < TTL:
        return entry[0]

    try:
        data = _query(symbol)
        price = float(data[symbol]["usd"])
        _cache[symbol] = (price, time.time())
        return price
    except Exception as e:
        _log.warning("Price fetch failed for %s: %s – using fallback %.2f", symbol, e, fallback)
        return entry[0] if entry else fallback

def fetch_xmr_usd_rate() -> float:
    return _get("monero", 150.0)

def fetch_btc_usd_rate() -> float:
    return _get("bitcoin", 65000.0)
