"""Unusual-move flags: a robust z-score plus an isolation forest on multi-feature windows.
Both are causal: statistics use the trailing year only, and the forest is fitted on the
past before scoring each 63-day block. Afterwards, what followed a flag is compared with
what followed days that were not flagged."""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest

Z_FLAG = 3.5
WIN = 250
STEP = 63
FOREST_TRAIN = 500
FWD = (1, 5, 20)


def robust_z(r: pd.Series, win: int = WIN) -> pd.Series:
    """(r_t - median) / (1.4826 * MAD) over the previous `win` days, excluding day t."""
    prev = r.shift(1)
    med = prev.rolling(win, min_periods=120).median()
    mad = (prev - med).abs().rolling(win, min_periods=120).median()
    return (r - med) / (1.4826 * mad + 1e-9)


def window_features(r: pd.Series, vol: pd.Series) -> pd.DataFrame:
    s5 = r.rolling(5).std()
    s60 = r.rolling(60).std()
    lv = np.log1p(vol)
    vz = (lv - lv.shift(1).rolling(60).mean()) / (lv.shift(1).rolling(60).std() + 1e-9)
    return pd.DataFrame({"abs_r": r.abs(), "vol_ratio": s5 / (s60 + 1e-9), "vol_z": vz.fillna(0.0)}).replace([np.inf, -np.inf], np.nan)


def forest_flags(F: pd.DataFrame, seed: int = 0) -> pd.Series:
    out = pd.Series(False, index=F.index)
    X = F.to_numpy()
    n = len(F)
    first = FOREST_TRAIN + 60
    for b in range(first, n, STEP):
        e = min(b + STEP, n)
        tr = X[b - FOREST_TRAIN: b]
        tr = tr[~np.isnan(tr).any(axis=1)]
        if len(tr) < 200:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = IsolationForest(n_estimators=100, contamination=0.02, random_state=seed).fit(tr)
            blk = X[b:e]
            ok = ~np.isnan(blk).any(axis=1)
            pred = np.zeros(len(blk), dtype=bool)
            if ok.any():
                pred[ok] = m.predict(blk[ok]) == -1
        out.iloc[b:e] = pred
    return out


def flag_asset(r: pd.Series, vol: pd.Series) -> pd.DataFrame:
    z = robust_z(r)
    forest = forest_flags(window_features(r, vol))
    df = pd.DataFrame({"r": r, "z": z, "forest": forest})
    df["flag"] = (df["z"].abs() >= Z_FLAG) | df["forest"]
    return df


def forward_stats(df: pd.DataFrame) -> pd.DataFrame:
    r = df["r"]
    fv = pd.concat([r.shift(-k) for k in range(1, 6)], axis=1)
    out = pd.DataFrame(index=df.index)
    out["fwd_vol5"] = np.sqrt((fv ** 2).mean(axis=1, skipna=False))
    for h in FWD:
        out[f"fwd_ret{h}"] = r[::-1].rolling(h).sum()[::-1].shift(-1)
    return out


def evaluate(flagged: dict[str, pd.DataFrame]) -> dict:
    """Pool across assets. Flag days within 5 days of an earlier flag are thinned so windows do not overlap."""
    fl_vol, base_vol, fl_ret = [], [], {h: [] for h in FWD}
    n_flags = 0
    for t, df in flagged.items():
        fs = forward_stats(df).dropna(subset=["fwd_vol5"])
        d = df.loc[fs.index]
        is_flag = d["flag"].to_numpy()
        keep, last = [], -10
        for i, f in enumerate(is_flag):
            if f and i - last >= 5:
                keep.append(i); last = i
        n_flags += int(is_flag.sum())
        mask = np.zeros(len(d), dtype=bool); mask[keep] = True
        fl_vol += list(fs["fwd_vol5"].to_numpy()[mask])
        base_vol += list(fs["fwd_vol5"].to_numpy()[~is_flag])
        for h in FWD:
            col = fs[f"fwd_ret{h}"].to_numpy()
            fl_ret[h] += list(col[mask][~np.isnan(col[mask])])
    if len(fl_vol) < 30:
        return {"n_flags": n_flags, "n_independent": len(fl_vol), "verdict": "Does not beat baseline", "vol_ratio": None}
    fl_vol, base_vol = np.array(fl_vol), np.array(base_vol)
    ratio = float(fl_vol.mean() / base_vol.mean())
    p_vol = float(stats.mannwhitneyu(fl_vol, base_vol, alternative="greater").pvalue)
    dirs = {h: {"mean": float(np.mean(v)), "p": float(stats.ttest_1samp(v, 0.0).pvalue), "n": len(v)} for h, v in fl_ret.items() if len(v) > 10}
    dir_sig = any(v["p"] < 0.05 for v in dirs.values())
    vol_sig = p_vol < 0.05 and ratio > 1
    verdict = "Beats baseline" if vol_sig and dir_sig else "Mixed" if vol_sig else "Does not beat baseline"
    return {"n_flags": n_flags, "n_independent": len(fl_vol), "vol_ratio": ratio, "vol_p": p_vol, "direction": dirs, "verdict": verdict}
