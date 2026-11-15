"""Fetchers. Yahoo (via yfinance) for history; CoinGecko for the crypto snapshot."""
from __future__ import annotations
import time
import pandas as pd


class FetchError(RuntimeError):
    pass


def fetch_yahoo(symbol: str, start: str, retries: int = 3, backoff: float = 2.0) -> pd.DataFrame:
    """Daily adjusted close and volume. Retries with backoff; raises FetchError if empty."""
    import yfinance as yf
    last = "no data"
    for attempt in range(retries):
        try:
            df = yf.Ticker(symbol).history(start=start, auto_adjust=True, actions=False)
            if df is not None and not df.empty and "Close" in df:
                out = pd.DataFrame({"close": df["Close"], "volume": df.get("Volume", 0.0)})
                out.index = pd.to_datetime(out.index).tz_localize(None).normalize()
                out.index.name = "date"
                return out
            last = "empty response"
        except Exception as e:  # network, rate limit, parse
            last = f"{type(e).__name__}: {e}"
        time.sleep(backoff * (2 ** attempt))
    raise FetchError(f"{symbol}: {last}")


def fetch_coingecko_snapshot(ids: list[str], retries: int = 3, backoff: float = 3.0) -> dict:
    """Latest price and 24h change for crypto. Needs attribution to CoinGecko in the UI."""
    import requests
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(ids), "vs_currencies": "usd", "include_24hr_change": "true"}
    last = "no response"
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(backoff * (2 ** attempt))
    raise FetchError(f"coingecko: {last}")
