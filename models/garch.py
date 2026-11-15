"""GARCH(1,1) with a causal walk-forward. Returns are in percent.
sigma2[t] is the variance forecast for r[t] using data up to t-1 only, with
parameters fitted on data before the block that contains t."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from arch import arch_model

MIN_TRAIN = 750
STEP = 21


def fit_garch(r: np.ndarray) -> dict:
    res = arch_model(r, mean="Constant", vol="GARCH", p=1, q=1, dist="normal", rescale=False).fit(
        disp="off", show_warning=False)
    p = res.params
    return {"mu": float(p["mu"]), "omega": float(p["omega"]), "alpha": float(p["alpha[1]"]), "beta": float(p["beta[1]"])}


def filter_sigma2(r: np.ndarray, mu: float, omega: float, alpha: float, beta: float) -> np.ndarray:
    """Length len(r)+1. Entry t is the variance for r[t] given r[:t]; the last entry is the next day."""
    n = len(r)
    s2 = np.empty(n + 1)
    persist = alpha + beta
    s2[0] = omega / (1 - persist) if persist < 0.999 else float(np.var(r))
    for t in range(1, n + 1):
        e = r[t - 1] - mu
        s2[t] = omega + alpha * e * e + beta * s2[t - 1]
    return s2


def avg_variance_forecast(s2_next: float, omega: float, persist: float, h: int) -> float:
    """Average of the h-step-ahead variance forecasts, made after seeing today's return."""
    if persist >= 0.999:
        return s2_next
    lr = omega / (1 - persist)
    return float(np.mean([lr + persist ** k * (s2_next - lr) for k in range(h)]))


@dataclass
class GarchRun:
    s2: np.ndarray        # len n, NaN before the first block
    mu: np.ndarray        # len n, the mu used for each day
    omega: np.ndarray     # len n, omega of the block that predicted each day
    persist: np.ndarray   # len n, alpha+beta of that block
    next_s2: float        # live forecast for the next unseen day
    live: dict            # parameters fitted on all data


def walk_forward(r: np.ndarray, min_train: int = MIN_TRAIN, step: int = STEP) -> GarchRun:
    n = len(r)
    s2 = np.full(n, np.nan)
    mu = np.full(n, np.nan)
    om = np.full(n, np.nan)
    pe = np.full(n, np.nan)
    for b in range(min_train, n, step):
        e = min(b + step, n)
        prm = fit_garch(r[:b])
        full = filter_sigma2(r[:e], **prm)
        s2[b:e] = full[b:e]
        mu[b:e] = prm["mu"]
        om[b:e] = prm["omega"]
        pe[b:e] = prm["alpha"] + prm["beta"]
    live = fit_garch(r)
    nxt = filter_sigma2(r, **live)[-1]
    return GarchRun(s2=s2, mu=mu, omega=om, persist=pe, next_s2=float(nxt), live=live)
