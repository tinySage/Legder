"""One-day Value-at-Risk and Expected Shortfall at 95%, backtested on the last 500 days.
Three methods: historical, normal, and filtered historical simulation (FHS, the main one).
A breach is a day when the loss was larger than the model's VaR."""
from __future__ import annotations
import numpy as np
import pandas as pd
from models import garch
from models.stats import kupiec_pof, christoffersen_independence, var_verdict

ALPHA = 0.05
EVAL_DAYS = 500
HIST_W = 250
FHS_W = 500
Z05 = -1.6448536269514722


def var_paths(r: np.ndarray, run: garch.GarchRun) -> dict:
    """VaR_t and ES_t (positive percent) for each day t, using only data before t."""
    n = len(r)
    z = (r - run.mu) / np.sqrt(run.s2)              # NaN before the first block
    hist = np.full(n, np.nan); par = np.full(n, np.nan); fhs = np.full(n, np.nan); es = np.full(n, np.nan)
    for t in range(garch.MIN_TRAIN, n):
        w = r[t - HIST_W: t]
        hist[t] = -np.quantile(w, ALPHA)
        par[t] = -(w.mean() + w.std(ddof=1) * Z05)
        zw = z[max(0, t - FHS_W): t]
        zw = zw[~np.isnan(zw)]
        if len(zw) >= 250:
            q = np.quantile(zw, ALPHA)
            sig = np.sqrt(run.s2[t])
            fhs[t] = -(run.mu[t] + sig * q)
            es[t] = -(run.mu[t] + sig * zw[zw <= q].mean())
    return {"historical": hist, "normal": par, "fhs": fhs, "es_fhs": es}


def backtest(r: np.ndarray, var: np.ndarray, days: int = EVAL_DAYS) -> dict | None:
    ok = ~np.isnan(var)
    idx = np.where(ok)[0][-days:]
    if len(idx) < 250:
        return None
    breach = r[idx] < -var[idx]
    k, c = kupiec_pof(breach, ALPHA), christoffersen_independence(breach)
    return {"days": len(idx), "breaches": k["breaches"], "expected": round(k["expected"], 1), "rate": k["rate"],
            "kupiec_p": k["p_value"], "independence_p": c["p_value"], "verdict": var_verdict(k, c)}


def live_var(r: np.ndarray, run: garch.GarchRun, paths: dict) -> dict:
    n = len(r)
    z = (r - run.mu) / np.sqrt(run.s2)
    zw = z[n - FHS_W: n]; zw = zw[~np.isnan(zw)]
    q = np.quantile(zw, ALPHA)
    sig = np.sqrt(run.next_s2)
    mu = run.live["mu"]
    return {"var95": float(-(mu + sig * q)), "es95": float(-(mu + sig * zw[zw <= q].mean())),
            "historical": float(-np.quantile(r[-HIST_W:], ALPHA))}


def drawdown(prices: pd.Series, days: int = 252) -> dict:
    p = prices.dropna().iloc[-days:]
    dd = p / p.cummax() - 1
    return {"series": [round(float(x) * 100, 3) for x in dd.to_numpy()], "max_drawdown_pct": float(dd.min() * 100)}


def analyse_asset(series: pd.Series, run: garch.GarchRun, prices: pd.Series) -> dict:
    r = series.to_numpy()
    paths = var_paths(r, run)
    bt = {m: backtest(r, paths[m]) for m in ("fhs", "historical", "normal")}
    last = np.where(~np.isnan(paths["fhs"]))[0][-120:]
    return {
        "live": live_var(r, run, paths),
        "backtest": bt,
        "verdict": bt["fhs"]["verdict"] if bt["fhs"] else "n/a",
        "last120": {
            "dates": [d.date().isoformat() for d in series.index[last]],
            "returns": [round(float(x), 3) for x in r[last]],
            "limit": [round(float(-x), 3) for x in paths["fhs"][last]],
        },
        "drawdown": drawdown(prices),
    }
