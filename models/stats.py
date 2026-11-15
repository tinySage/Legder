"""Small, tested statistical helpers: VaR backtests, Diebold-Mariano, block bootstrap."""
from __future__ import annotations
import numpy as np
from scipy import stats
from scipy.special import xlogy


def kupiec_pof(breaches: np.ndarray, p: float) -> dict:
    """Unconditional coverage test. H0: breach probability equals p."""
    b = np.asarray(breaches, dtype=bool)
    n, x = len(b), int(b.sum())
    pi = x / n
    ll0 = xlogy(n - x, 1 - p) + xlogy(x, p)
    ll1 = xlogy(n - x, 1 - pi) + xlogy(x, pi)
    lr = max(0.0, -2 * (ll0 - ll1))
    return {"n": n, "breaches": x, "expected": n * p, "rate": pi, "lr": lr, "p_value": float(stats.chi2.sf(lr, 1))}


def christoffersen_independence(breaches: np.ndarray) -> dict:
    """Tests whether breaches bunch together. H0: today's breach does not depend on yesterday's."""
    b = np.asarray(breaches, dtype=int)
    a, c = b[:-1], b[1:]
    n00 = int(((a == 0) & (c == 0)).sum()); n01 = int(((a == 0) & (c == 1)).sum())
    n10 = int(((a == 1) & (c == 0)).sum()); n11 = int(((a == 1) & (c == 1)).sum())
    if n01 + n11 == 0 or n00 + n01 == 0:      # no breaches: test has nothing to say
        return {"lr": 0.0, "p_value": 1.0, "n00": n00, "n01": n01, "n10": n10, "n11": n11}
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)
    pi01 = n01 / (n00 + n01)
    pi11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0.0
    ll0 = xlogy(n00 + n10, 1 - pi) + xlogy(n01 + n11, pi)
    ll1 = xlogy(n00, 1 - pi01) + xlogy(n01, pi01) + xlogy(n10, 1 - pi11) + xlogy(n11, pi11)
    lr = max(0.0, -2 * (ll0 - ll1))
    return {"lr": lr, "p_value": float(stats.chi2.sf(lr, 1)), "n00": n00, "n01": n01, "n10": n10, "n11": n11}


def var_verdict(kupiec: dict, indep: dict, alpha: float = 0.05) -> str:
    if kupiec["p_value"] < alpha:
        return "Too many" if kupiec["rate"] > kupiec["expected"] / kupiec["n"] else "Too few"
    if indep["p_value"] < alpha:
        return "Clustered"
    return "Pass"


def newey_west_var(d: np.ndarray, lag: int) -> float:
    d = d - d.mean()
    n = len(d)
    v = float(d @ d) / n
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        v += 2 * w * float(d[k:] @ d[:-k]) / n
    return v


def diebold_mariano(loss_base: np.ndarray, loss_model: np.ndarray, lag: int = 5) -> dict:
    """d>0 means the model has the smaller loss. Two-sided p-value, Newey-West variance."""
    d = np.asarray(loss_base) - np.asarray(loss_model)
    n = len(d)
    var = newey_west_var(d, lag)
    stat = d.mean() / np.sqrt(var / n) if var > 0 else 0.0
    return {"mean_diff": float(d.mean()), "stat": float(stat), "p_value": float(2 * stats.norm.sf(abs(stat))), "n": n}


def block_bootstrap_diff(x: np.ndarray, y: np.ndarray, stat_fn, block: int = 20, reps: int = 300, seed: int = 0):
    """CI for stat_fn(x) - stat_fn(y) resampling the SAME row blocks of both (keeps dependence)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    nb = int(np.ceil(n / block))
    out = []
    for _ in range(reps):
        starts = rng.integers(0, n - block + 1, nb)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        out.append(stat_fn(x[idx]) - stat_fn(y[idx]))
    lo, hi = np.percentile(out, [2.5, 97.5])
    return float(lo), float(hi)
