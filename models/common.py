"""Shared context: aligned prices and returns, plus per-asset GARCH walk-forward results."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from pipeline.clean import align_to_calendar
from pipeline.universe import UNIVERSE, CALENDAR_ANCHOR, BY_TICKER
from models import garch


@dataclass
class Ctx:
    prices: pd.DataFrame        # aligned to the anchor's trading days
    volume: pd.DataFrame
    rets: pd.DataFrame          # log returns in percent, causal
    meta: pd.DataFrame          # store meta: ticker, last_ok, status, error
    synthetic: bool
    now: pd.Timestamp
    garch_runs: dict = field(default_factory=dict)

    def series(self, t: str) -> pd.Series:
        return self.rets[t].dropna()

    def garch(self, t: str):
        if t not in self.garch_runs:
            self.garch_runs[t] = garch.walk_forward(self.series(t).to_numpy())
        return self.garch_runs[t]


def build_context(store, synthetic: bool, now: pd.Timestamp, tickers=None) -> Ctx:
    tickers = tickers or [a.ticker for a in UNIVERSE if a.ticker in store.tickers()]
    hist = {t: store.history(t) for t in tickers}
    closes = {t: h["close"] for t, h in hist.items()}
    prices, _ = align_to_calendar(closes, CALENDAR_ANCHOR)
    vols = pd.DataFrame({t: h["volume"].reindex(prices.index) for t, h in hist.items()}).fillna(0.0)
    rets = 100 * np.log(prices).diff()
    return Ctx(prices=prices, volume=vols, rets=rets, meta=store.meta(), synthetic=synthetic, now=now)


def class_returns(ctx: Ctx, members: list[str]) -> pd.Series:
    """Equal-weight return of an asset class: mean over members available that day."""
    return ctx.rets[[m for m in members if m in ctx.rets]].mean(axis=1).dropna()


def class_members(cls: str) -> list[str]:
    return [a.ticker for a in UNIVERSE if a.cls == cls]
