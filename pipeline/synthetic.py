"""Deterministic synthetic market for tests and local development ONLY.
Three hidden regimes (calm, trending, stress) drive volatility, drift and
cross-asset correlation, so models can be checked against a known truth.
Anything built from this is flagged synthetic and must never look real."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .universe import UNIVERSE

# regime: (daily vol multiplier, daily drift, common-factor weight)
REGIMES = {0: (0.7, 0.0004, 0.35), 1: (1.0, 0.0012, 0.45), 2: (2.6, -0.0030, 0.85)}
TRANS = np.array([[0.985, 0.012, 0.003], [0.020, 0.975, 0.005], [0.060, 0.040, 0.900]])


def make_regime_path(n: int, rng: np.random.Generator) -> np.ndarray:
    s = np.zeros(n, dtype=int)
    for i in range(1, n):
        s[i] = rng.choice(3, p=TRANS[s[i - 1]])
    return s


def make_panel(n_days: int = 1800, seed: int = 7, end: str = "2026-11-13"):
    """Returns (panel, truth). panel: ticker -> DataFrame(close, volume). truth: regime path
    on the business-day calendar. Crypto also has weekend rows."""
    rng = np.random.default_rng(seed)
    bdays = pd.bdate_range(end=end, periods=n_days)
    state = make_regime_path(n_days, rng)
    vol_mult = np.array([REGIMES[s][0] for s in state])
    drift = np.array([REGIMES[s][1] for s in state])
    w = np.array([REGIMES[s][2] for s in state])
    common = rng.standard_normal(n_days)
    panel = {}
    for a in UNIVERSE:
        base_vol = {"crypto": 0.035, "stock": 0.016, "etf": 0.009}[a.kind]
        beta = {"Equities": 1.0, "Crypto": 0.6, "Commodities and FX": 0.15, "Rates": -0.4}[a.cls]
        idio = rng.standard_normal(n_days)
        z = np.sqrt(w) * beta * common + np.sqrt(1 - w) * idio
        r = drift * (0.2 if a.cls == "Commodities and FX" else 1.0) + base_vol * vol_mult * z
        price = 100 * np.exp(np.cumsum(r))
        vol = rng.integers(1_000_000, 5_000_000, n_days).astype(float)
        df = pd.DataFrame({"close": price, "volume": vol}, index=bdays)
        if a.kind == "crypto":  # add weekend rows by interpolation-free extension
            full = pd.date_range(bdays[0], bdays[-1], freq="D")
            df = df.reindex(full)
            wk = df["close"].isna()
            df.loc[wk, "close"] = df["close"].ffill()[wk] * np.exp(rng.normal(0, base_vol * 0.8, wk.sum()))
            df["volume"] = df["volume"].fillna(1_000_000.0)
        df.index.name = "date"
        panel[a.ticker] = df
    truth = pd.Series(state, index=bdays, name="regime")
    return panel, truth
