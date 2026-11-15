"""Calm / Trending / Stress from a 3-state Gaussian hidden Markov model.

Causal by construction. Parameters are fitted only on data before each block
(expanding window, refit every 63 days). Probabilities come from the forward
filter (never the smoother), so the label on day t uses data up to day t only.
States are named from the fitted parameters: lowest-volatility state = Calm,
highest = Stress, the one in between = Trending."""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

MIN_TRAIN = 750
STEP = 63
BURN = 250
LABELS = ["Calm", "Trending", "Stress"]
KEYS = ["calm", "trend", "stress"]


def features(r: np.ndarray) -> np.ndarray:
    """[return, 10-day realised volatility], both causal."""
    s = pd.Series(r)
    vol = s.rolling(10, min_periods=5).std().fillna(s.abs())
    return np.c_[r, vol.to_numpy()]


def _fit(X: np.ndarray, seed: int = 0):
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-9
    best = None
    for s in (seed, seed + 1, seed + 2):               # a few starts, keep the best likelihood
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = GaussianHMM(n_components=3, covariance_type="diag", n_iter=200, tol=1e-3, random_state=s)
            m.fit((X - mu) / sd)
            ll = m.score((X - mu) / sd)
        if best is None or ll > best[0]:
            best = (ll, m)
    m = best[1]
    order = np.argsort(m.means_[:, 1])                 # by the volatility feature: calm, trending, stress
    return m, mu, sd, order


def _filter(m: GaussianHMM, Xs: np.ndarray) -> np.ndarray:
    """Forward algorithm: P(state_t | data up to t)."""
    logb = m._compute_log_likelihood(Xs)
    A = m.transmat_
    alpha = m.startprob_ * np.exp(logb[0] - logb[0].max())
    alpha /= alpha.sum()
    out = np.empty_like(logb)
    out[0] = alpha
    for t in range(1, len(Xs)):
        alpha = (alpha @ A) * np.exp(logb[t] - logb[t].max())
        alpha /= alpha.sum()
        out[t] = alpha
    return out


def causal_probs(r: np.ndarray, min_train: int = MIN_TRAIN, step: int = STEP, burn: int = BURN, seed: int = 0) -> np.ndarray:
    """(n, 3) probabilities ordered [calm, trending, stress]; NaN before min_train."""
    X = features(r)
    n = len(r)
    P = np.full((n, 3), np.nan)
    for b in range(min_train, n, step):
        e = min(b + step, n)
        m, mu, sd, order = _fit(X[:b], seed)
        lo = max(0, b - burn)
        probs = _filter(m, (X[lo:e] - mu) / sd)[:, order]
        P[b:e] = probs[b - lo:]
    return P


def spells(labels: np.ndarray) -> list[int]:
    out, run = [], 1
    for i in range(1, len(labels)):
        if labels[i] == labels[i - 1]:
            run += 1
        else:
            out.append(run); run = 1
    out.append(run)
    return out


def summarise(P: np.ndarray, index: pd.DatetimeIndex) -> dict:
    ok = ~np.isnan(P[:, 0])
    lab = P[ok].argmax(axis=1)
    cur = int(lab[-1])
    days = 1
    for x in lab[::-1][1:]:
        if x == cur:
            days += 1
        else:
            break
    last3 = lab[-756:]
    return {
        "regime": KEYS[cur], "label": LABELS[cur], "days": days,
        "confidence": float(P[ok][-1].max()), "stress_probability": float(P[ok][-1][2]),
        "avg_spell_days": float(np.mean(spells(last3))),
        "share_days": {k: float((last3 == i).mean()) for i, k in enumerate(KEYS)},
    }


def history(P: np.ndarray, index: pd.DatetimeIndex, days: int = 120) -> dict:
    ok = np.where(~np.isnan(P[:, 0]))[0][-days:]
    return {"dates": [index[i].date().isoformat() for i in ok],
            "codes": ["ctS"[int(P[i].argmax())] for i in ok],
            "stress_probability": [round(float(P[i][2]), 4) for i in ok]}
