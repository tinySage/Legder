"""Rolling correlation, and a test of whether correlations rise in stress.
Calm and stress days come from the causal regime labels of the equity class."""
from __future__ import annotations
import numpy as np
import pandas as pd
from models.stats import block_bootstrap_diff

DISPLAY = ["SPY", "QQQ", "AAPL", "XOM", "GLD", "TLT", "BTC", "ETH"]
WINDOWS = [20, 40, 60, 90, 120, 180, 250]


def matrices(rets: pd.DataFrame, tickers=DISPLAY, windows=WINDOWS) -> dict:
    out = {}
    sub = rets[tickers].dropna()
    for w in windows:
        c = sub.iloc[-w:].corr()
        out[str(w)] = [[round(float(c.loc[a, b]), 3) for b in tickers] for a in tickers]
    return out


def _avg_pair(X: np.ndarray) -> float:
    if len(X) < 30:
        return float("nan")
    c = np.corrcoef(X, rowvar=False)
    iu = np.triu_indices_from(c, 1)
    return float(np.nanmean(c[iu]))


def calm_vs_stress(rets: pd.DataFrame, probs: np.ndarray, probs_index: pd.DatetimeIndex, tickers=DISPLAY) -> dict:
    sub = rets[tickers].dropna()
    P = pd.DataFrame(probs, index=probs_index).reindex(sub.index)
    ok = ~P.isna().any(axis=1)
    sub, lab = sub[ok], P[ok].to_numpy().argmax(axis=1)
    calm, stress = sub.to_numpy()[lab == 0], sub.to_numpy()[lab == 2]
    if len(calm) < 60 or len(stress) < 60:
        return {"calm": None, "stress": None, "verdict": "n/a", "n_calm": len(calm), "n_stress": len(stress)}
    a, b = _avg_pair(calm), _avg_pair(stress)
    mat = lambda X: [[round(float(v), 3) for v in row] for row in np.corrcoef(X, rowvar=False)]
    # resample whole blocks of days, keeping each group's rows together
    m = min(len(calm), len(stress))
    lo, hi = block_bootstrap_diff(stress[-m:], calm[-m:], _avg_pair)
    verdict = "Stable" if lo > 0 else "Mixed"
    return {"calm": a, "stress": b, "difference": b - a, "ci95": [lo, hi], "n_calm": len(calm), "n_stress": len(stress),
            "rises_in_stress": bool(lo > 0), "verdict": verdict,
            "matrices": {"calm": mat(calm), "stress": mat(stress)}}
