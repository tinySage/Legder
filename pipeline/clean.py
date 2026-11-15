"""Cleaning and alignment. Everything here is causal: no step uses a later
observation to change an earlier value."""
from __future__ import annotations
import numpy as np
import pandas as pd

FFILL_LIMIT = 3          # trading days a value may be carried forward
SUSPECT_JUMP = 0.35      # |log return| above this is flagged as a possible unadjusted split


def clean_series(df: pd.DataFrame) -> pd.DataFrame:
    """Sort, drop duplicate dates (keep the last), drop non-positive or missing closes."""
    d = df.copy()
    d.index = pd.to_datetime(d.index).normalize()
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d = d[d["close"].notna() & (d["close"] > 0)]
    d["volume"] = d["volume"].fillna(0.0)
    d.index.name = "date"
    return d


def drop_incomplete_last_bar(df: pd.DataFrame, kind: str, now: pd.Timestamp) -> pd.DataFrame:
    """Remove a partial final day. Crypto's UTC day is partial until midnight UTC.
    Stock bars dated today are partial until the US close (21:00 UTC covers both DST cases)."""
    if df.empty:
        return df
    today = now.normalize().tz_localize(None) if now.tzinfo else now.normalize()
    last = df.index[-1]
    if kind == "crypto" and last >= today:
        return df.iloc[:-1]
    if kind != "crypto" and last >= today and now.hour < 21:
        return df.iloc[:-1]
    return df


def suspect_jumps(close: pd.Series, thresh: float = SUSPECT_JUMP) -> pd.DatetimeIndex:
    r = np.log(close).diff()
    return r.index[r.abs() > thresh]


def align_to_calendar(panel: dict[str, pd.Series], anchor: str, ffill_limit: int = FFILL_LIMIT):
    """Reindex every series to the anchor's trading days. Crypto trades every day, so its
    value on a trading day is that day's close (no future data). Gaps are carried forward
    at most `ffill_limit` days, never backward. Returns (prices, filled_counts)."""
    cal = panel[anchor].dropna().index
    out, filled = {}, {}
    for t, s in panel.items():
        s = s[~s.index.duplicated(keep="last")].sort_index()
        r = s.reindex(cal)
        before = r.isna().sum()
        r = r.ffill(limit=ffill_limit)
        filled[t] = int(before - r.isna().sum())
        out[t] = r
    return pd.DataFrame(out), filled


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """r_t = log(P_t / P_{t-1}). Uses only data up to t."""
    return np.log(prices).diff()


def quality_report(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for t, df in panel.items():
        idx = df.index
        gaps = idx.to_series().diff().dt.days.dropna()
        rows.append({
            "ticker": t,
            "rows": len(df),
            "first": idx.min().date().isoformat() if len(df) else None,
            "last": idx.max().date().isoformat() if len(df) else None,
            "max_gap_days": int(gaps.max()) if len(gaps) else 0,
            "duplicates": int(idx.duplicated().sum()),
            "suspect_jumps": int(len(suspect_jumps(df["close"]))) if len(df) > 1 else 0,
        })
    return pd.DataFrame(rows)
