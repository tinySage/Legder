"""Plain-language model cards. Every number in the text comes from the evaluation results."""
from __future__ import annotations
import numpy as np


def _tier_vol(s):
    v = s["verdict"]
    return v


def build(vol: dict, risk_by_asset: dict, reg_spells: dict, anom: dict, fc: dict, corr: dict, synthetic: bool) -> dict:
    cards = []
    # volatility
    imp = vol["median_improvement"] * 100
    cards.append({
        "name": "Volatility forecast", "verdict": vol["verdict"],
        "what": "Predicts how large daily moves will be over the next 5 days (GARCH).",
        "test": f"forecasting 5-day volatility across {vol['n_assets']} assets with a walk-forward test, versus a plain 30-day average.",
        "result": f"median error {abs(imp):.0f}% {'lower' if imp >= 0 else 'higher'} than the baseline; clearly better on {vol['n_beat']} of {vol['n_assets']} assets.",
        "limit": "Slow to react to a sudden shock such as an earnings surprise."})
    # VaR
    rows = [v for v in risk_by_asset.values() if v["verdict"] != "n/a"]
    n = len(rows)
    n_pass = sum(1 for v in rows if v["verdict"] == "Pass")
    n_clu = sum(1 for v in rows if v["verdict"] == "Clustered")
    n_many = sum(1 for v in rows if v["verdict"] == "Too many")
    share = n_pass / n if n else 0
    verdict = "Stable" if share >= 0.75 else "Mixed" if share >= 0.4 else "Unreliable"
    cards.append({
        "name": "Value-at-Risk line", "verdict": verdict,
        "what": "Sets a daily loss level that should be crossed about 1 day in 20.",
        "test": f"counting crossings over the last 500 days for {n} assets and testing whether they bunch up.",
        "result": f"passed on {n_pass} of {n} assets; crossings cluster on {n_clu} and are too frequent on {n_many}.",
        "limit": "Underestimates risk right after volatility jumps."})
    # regimes
    avg = float(np.mean(list(reg_spells.values()))) if reg_spells else 0.0
    cards.append({
        "name": "Regime detection", "verdict": "Stable" if avg >= 10 else "Mixed" if avg >= 5 else "Unstable",
        "what": "Labels each market calm, trending or stress from returns and volatility.",
        "test": "checking that regimes persist instead of flipping daily, using a filter that sees only the past.",
        "result": f"the average regime lasts {avg:.0f} trading days.",
        "limit": "Stress is simply the most volatile of three fitted states, so it is called even in mild turbulence."})
    # anomalies
    if anom.get("vol_ratio"):
        dirs = [h for h, v in anom.get("direction", {}).items() if v["p"] < 0.05]
        res = f"volatility over the next 5 days is {anom['vol_ratio']:.1f}x normal; " + (
            f"direction is significant at {', '.join(str(h) + 'd' for h in dirs)}." if dirs else "no clear direction.")
    else:
        res = "too few independent flags to say."
    cards.append({
        "name": "Unusual-move flags", "verdict": anom["verdict"],
        "what": "Flags days that look unlike the recent past.",
        "test": "comparing the next 1, 5 and 20 days after a flag with days without one, one flag per 5-day window.",
        "result": res, "limit": "Says something odd happened, not what comes next."})
    # forecasts
    a, g = fc["summary"].get("arima"), fc["summary"].get("gbm")
    gaps = [abs(x["mean_rel_mae"] - 1) * 100 for x in (a, g) if x]
    beat = any(x and x["verdict"] == "Beats baseline" for x in (a, g))
    cards.append({
        "name": "Price forecast", "verdict": "Beats baseline" if beat else "Does not beat baseline",
        "what": "Predicts tomorrow’s price change (ARIMA and gradient boosting).",
        "test": "walk-forward test, no look-ahead, versus “tomorrow equals today”.",
        "result": (f"error within {max(gaps):.0f}% of the baseline in either direction." if gaps else "not enough data."),
        "limit": "Daily price changes are close to random. Do not trade on this."})
    # correlation
    if corr.get("calm") is not None:
        res = (f"average pair correlation {corr['calm']:.2f} on calm days, {corr['stress']:.2f} on stress days; "
               + ("the rise is statistically clear." if corr["rises_in_stress"] else "the rise is not clear."))
    else:
        res = "not enough calm and stress days to compare."
    cards.append({
        "name": "Correlation structure", "verdict": corr.get("verdict", "n/a"),
        "what": "Shows which assets move together over a rolling window.",
        "test": "comparing correlations on calm and stress days, with a block bootstrap for the difference.",
        "result": res, "limit": "Correlations change quickly and a short window is noisy."})
    fvb = [{"name": "Tomorrow equals today", "value": 1.0}]
    if a: fvb.append({"name": "ARIMA", "value": round(a["mean_rel_mae"], 3)})
    if g: fvb.append({"name": "Gradient boosting", "value": round(g["mean_rel_mae"], 3)})
    return {"synthetic": synthetic, "forecast_vs_baseline": fvb, "models": cards}
