"""5-day volatility forecast: GARCH(1,1) vs a plain 30-day average, walk-forward."""
from __future__ import annotations
import numpy as np
from models import garch
from models.stats import diebold_mariano

H = 5
BASE_WINDOW = 30


def evaluate_asset(r: np.ndarray, run: garch.GarchRun) -> dict | None:
    n = len(r)
    g_pred, b_pred, real = [], [], []
    for t in range(garch.MIN_TRAIN, n - H):
        # forecast made after seeing r[t]; day t+1 uses parameters fitted on data <= t, never later data
        s2_next = run.s2[t + 1]
        if np.isnan(s2_next):
            continue
        v = garch.avg_variance_forecast(s2_next, run.omega[t + 1], run.persist[t + 1], H)
        g_pred.append(np.sqrt(v))
        b_pred.append(np.sqrt(np.mean(r[t - BASE_WINDOW + 1: t + 1] ** 2)))
        real.append(np.sqrt(np.mean(r[t + 1: t + 1 + H] ** 2)))
    if len(real) < 100:
        return None
    g, b, y = map(np.array, (g_pred, b_pred, real))
    dm = diebold_mariano((y - b) ** 2, (y - g) ** 2, lag=H)
    rmse_g, rmse_b = float(np.sqrt(np.mean((y - g) ** 2))), float(np.sqrt(np.mean((y - b) ** 2)))
    return {"rmse_garch": rmse_g, "rmse_baseline": rmse_b, "improvement": 1 - rmse_g / rmse_b,
            "dm_p": dm["p_value"], "n": len(y)}


def live_forecast(run: garch.GarchRun) -> dict:
    p = run.live
    persist = p["alpha"] + p["beta"]
    v = garch.avg_variance_forecast(run.next_s2, p["omega"], persist, H)
    daily = float(np.sqrt(v))
    return {"daily_vol_pct": daily, "annualised_pct": daily * np.sqrt(252), "next_day_vol_pct": float(np.sqrt(run.next_s2))}


def summarise(per_asset: dict) -> dict:
    ok = {t: m for t, m in per_asset.items() if m}
    if not ok:
        return {"verdict": "Does not beat baseline", "median_improvement": 0.0, "n_assets": 0, "n_beat": 0}
    imps = np.array([m["improvement"] for m in ok.values()])
    beat = sum(1 for m in ok.values() if m["improvement"] > 0 and m["dm_p"] < 0.05)
    worse = sum(1 for m in ok.values() if m["improvement"] < 0 and m["dm_p"] < 0.05)
    n = len(ok)
    if beat >= 0.6 * n:
        verdict = "Beats baseline"
    elif worse >= 0.6 * n:
        verdict = "Does not beat baseline"
    else:
        verdict = "Mixed"
    return {"verdict": verdict, "median_improvement": float(np.median(imps)), "n_assets": n, "n_beat": beat}
