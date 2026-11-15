"""Next-day price forecasts versus the baseline "tomorrow equals today" (forecast return = 0).
Walk-forward: parameters are fitted only on data before each block of 63 days.
Error is mean absolute error of the next-day return, shown relative to the baseline (1.00).
A model only 'beats' the baseline if its squared error is lower and a Diebold-Mariano test agrees."""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from statsmodels.tsa.arima.model import ARIMA
from models.stats import diebold_mariano

MIN_TRAIN = 750
STEP = 63
ASSETS = ["SPY", "QQQ", "AAPL", "BTC", "ETH", "GLD"]


def lag_features(r: pd.Series) -> pd.DataFrame:
    F = pd.DataFrame({f"r{k}": r.shift(k - 1) for k in range(1, 6)})  # r1 = today's return, known at forecast time
    F["m5"] = r.rolling(5).mean(); F["m20"] = r.rolling(20).mean(); F["s20"] = r.rolling(20).std()
    return F


def walk_forward(r: pd.Series) -> dict:
    """Predictions of r[t+1] made at t, for t from MIN_TRAIN on."""
    y = r.shift(-1)
    F = lag_features(r)
    n = len(r)
    arima = np.full(n, np.nan); gbm = np.full(n, np.nan)
    for b in range(MIN_TRAIN, n - 1, STEP):
        e = min(b + STEP, n - 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = ARIMA(r.iloc[:b + 1].to_numpy(), order=(1, 0, 1)).fit()
            applied = res.apply(r.iloc[:e + 1].to_numpy())
            fv = applied.fittedvalues                 # one-step-ahead: fv[i] predicts r[i] from r[:i]
            arima[b:e] = fv[b + 1:e + 1]              # forecast of r[t+1] made at t
            tr = F.iloc[30:b].join(y.iloc[30:b].rename("y")).dropna()   # target r[t+1] must be known by b
            m = HistGradientBoostingRegressor(max_iter=100, max_depth=3, learning_rate=0.05, random_state=0)
            m.fit(tr.drop(columns="y"), tr["y"])
            blk = F.iloc[b:e]
            ok = ~blk.isna().any(axis=1)
            p = np.full(len(blk), np.nan)
            if ok.any():
                p[ok.to_numpy()] = m.predict(blk[ok])
            gbm[b:e] = p
    return {"y": y.to_numpy(), "arima": arima, "gbm": gbm}


def score(y: np.ndarray, pred: np.ndarray) -> dict | None:
    ok = ~np.isnan(pred) & ~np.isnan(y)
    if ok.sum() < 200:
        return None
    y, p = y[ok], pred[ok]
    e_base, e_mod = y, y - p                          # baseline forecasts 0
    dm = diebold_mariano(e_base ** 2, e_mod ** 2, lag=5)
    hit = float((np.sign(p) == np.sign(y)).mean())
    return {"rel_mae": float(np.abs(e_mod).mean() / np.abs(e_base).mean()), "dm_p": dm["p_value"],
            "better_sq": bool(dm["mean_diff"] > 0), "directional_accuracy": hit,
            "directional_p": float(stats.binomtest(int((np.sign(p) == np.sign(y)).sum()), len(y), 0.5).pvalue), "n": int(ok.sum())}


def evaluate(rets: pd.DataFrame, assets=ASSETS) -> dict:
    per = {}
    for t in assets:
        if t not in rets:
            continue
        r = rets[t].dropna()
        if len(r) < MIN_TRAIN + 250:
            continue
        w = walk_forward(r)
        per[t] = {"arima": score(w["y"], w["arima"]), "gbm": score(w["y"], w["gbm"])}
    summary = {}
    for name in ("arima", "gbm"):
        rows = [v[name] for v in per.values() if v[name]]
        if not rows:
            summary[name] = None
            continue
        n_beat = sum(1 for x in rows if x["rel_mae"] < 1 and x["better_sq"] and x["dm_p"] < 0.05)
        summary[name] = {"mean_rel_mae": float(np.mean([x["rel_mae"] for x in rows])),
                         "n_assets": len(rows), "n_beat": n_beat,
                         "mean_directional_accuracy": float(np.mean([x["directional_accuracy"] for x in rows])),
                         "verdict": "Beats baseline" if n_beat >= 0.6 * len(rows) else "Does not beat baseline"}
    return {"per_asset": per, "summary": summary}
