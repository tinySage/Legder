import numpy as np
import pandas as pd
import pytest

from pipeline import clean, store as S, fetch as F
from pipeline.synthetic import make_panel
from pipeline.universe import UNIVERSE, CALENDAR_ANCHOR
from tests.leakage import assert_causal
import scripts.fetch as runner

NOW = pd.Timestamp("2026-11-14 22:30", tz="UTC")


def frame(n=400, start="2024-01-01", seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=n)
    return pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))), "volume": 1e6}, index=idx)


# ---- store -----------------------------------------------------------------
def test_store_replace_is_idempotent_no_duplicates():
    st = S.PriceStore()
    df = frame()
    st.replace_history("X", df, NOW.tz_localize(None))
    st.replace_history("X", df, NOW.tz_localize(None))
    n = st.con.execute("SELECT COUNT(*) FROM prices WHERE ticker='X'").fetchone()[0]
    assert n == len(df)
    assert st.history("X").index.is_unique


def test_stale_keeps_old_prices_and_records_failure():
    st = S.PriceStore()
    df = frame()
    st.replace_history("X", df, NOW.tz_localize(None))
    st.mark_stale("X", "429 too many requests")
    pd.testing.assert_series_equal(st.history("X")["close"], df["close"], check_freq=False, check_names=False)
    m = st.meta().set_index("ticker").loc["X"]
    assert m["status"] == "stale" and pd.notna(m["last_ok"])


def test_failed_or_empty_fetch_never_overwrites_good_data(tmp_path):
    db = str(tmp_path / "p.duckdb")
    good = lambda sym, start: frame(400, seed=hash(sym) % 1000)
    r1 = runner.run(db, False, now=NOW, fetcher=good)
    assert set(r1["results"].values()) == {"ok"}
    before = S.PriceStore(db).history("SPY")

    def boom(sym, start): raise F.FetchError("blocked")
    def empty(sym, start): return frame(5)
    for fetcher in (boom, empty):
        st = S.PriceStore(db); st.con.close()
        r = runner.run(db, False, now=NOW, fetcher=fetcher)
        assert all(v.startswith("stale") for v in r["results"].values())
        after = S.PriceStore(db).history("SPY")
        pd.testing.assert_frame_equal(before, after)


# ---- cleaning --------------------------------------------------------------
def test_clean_series_dedupes_sorts_and_drops_bad_rows():
    idx = pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-02", "2024-01-04", "2024-01-05"])
    df = pd.DataFrame({"close": [3.0, 1.0, 2.0, -5.0, np.nan], "volume": [1, 1, 1, 1, np.nan]}, index=idx)
    out = clean.clean_series(df)
    assert out.index.is_monotonic_increasing and out.index.is_unique
    assert out.loc["2024-01-02", "close"] == 2.0          # duplicate keeps the last
    assert (out["close"] > 0).all() and out["close"].notna().all()


def test_timestamps_with_times_are_normalised_to_dates():
    idx = pd.to_datetime(["2024-01-02 21:00", "2024-01-03 21:00"])
    out = clean.clean_series(pd.DataFrame({"close": [1.0, 2.0], "volume": [1, 1]}, index=idx))
    assert list(out.index) == [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]


@pytest.mark.parametrize("kind,last,now,keep", [
    ("crypto", "2026-11-14", "2026-11-14 22:30", False),   # UTC day not finished
    ("crypto", "2026-11-13", "2026-11-14 22:30", True),
    ("stock", "2026-11-13", "2026-11-13 18:00", False),    # before the US close
    ("stock", "2026-11-13", "2026-11-13 22:30", True),
    ("stock", "2026-11-12", "2026-11-13 18:00", True),
])
def test_partial_last_bar_is_dropped(kind, last, now, keep):
    idx = pd.to_datetime(["2026-11-10", "2026-11-11", last]).drop_duplicates()
    df = pd.DataFrame({"close": 1.0, "volume": 1.0}, index=idx)
    out = clean.drop_incomplete_last_bar(df, kind, pd.Timestamp(now, tz="UTC"))
    assert (out.index[-1] == pd.Timestamp(last)) == keep


def test_unadjusted_split_is_flagged():
    df = frame(300)
    df.iloc[200:, 0] = df.iloc[200:, 0] / 2.0     # a 2:1 split left unadjusted
    flagged = clean.suspect_jumps(df["close"])
    assert df.index[200] in flagged


# ---- alignment -------------------------------------------------------------
def test_crypto_alignment_uses_same_day_value_only():
    panel, _ = make_panel(n_days=400)
    series = {t: d["close"] for t, d in panel.items()}
    prices, filled = clean.align_to_calendar(series, CALENDAR_ANCHOR)
    btc = series["BTC"]
    for d in prices.index[::40]:
        assert prices.loc[d, "BTC"] == btc.loc[d]       # same-day close, not a later one
    assert prices.index.equals(series[CALENDAR_ANCHOR].dropna().index)


def test_ffill_is_limited_and_never_backward():
    idx = pd.bdate_range("2024-01-01", periods=30)
    spy = pd.Series(100.0, index=idx)
    x = pd.Series(1.0, index=idx[10:])            # starts late: must stay NaN before
    x = x.drop(idx[15:21])                         # six-day hole
    prices, filled = clean.align_to_calendar({"SPY": spy, "X": x}, "SPY", ffill_limit=3)
    assert prices["X"].iloc[:10].isna().all()      # no backfill
    hole = prices["X"].loc[idx[15:21]]
    assert hole.notna().sum() == 3 and hole.isna().sum() == 3
    assert filled["X"] == 3


def test_duplicate_timestamps_do_not_survive_alignment():
    idx = pd.bdate_range("2024-01-01", periods=10)
    spy = pd.Series(100.0, index=idx)
    dup = pd.concat([spy, spy.iloc[:3] * 2])
    prices, _ = clean.align_to_calendar({"SPY": spy, "D": dup}, "SPY")
    assert prices.index.is_unique and len(prices) == 10


# ---- look-ahead ------------------------------------------------------------
def test_log_returns_and_rolling_features_are_causal():
    p = frame(700)[["close"]]
    assert_causal(lambda d: clean.log_returns(d), p)
    assert_causal(lambda d: clean.log_returns(d)["close"].rolling(20).std().to_frame(), p)


def test_leakage_checker_catches_a_leaky_feature():
    p = frame(700)[["close"]]
    leaky_future = lambda d: d["close"].shift(-1).to_frame()
    leaky_full_sample = lambda d: ((d["close"] - d["close"].mean()) / d["close"].std()).to_frame()
    for leaky in (leaky_future, leaky_full_sample):
        with pytest.raises(AssertionError):
            assert_causal(leaky, p)


# ---- reporting and generator ----------------------------------------------
def test_quality_report_counts():
    df = frame(300)
    df = df.drop(df.index[100:104])                # makes a gap
    rep = clean.quality_report({"X": df}).iloc[0]
    assert rep["rows"] == 296 and rep["duplicates"] == 0 and rep["max_gap_days"] >= 5


def test_synthetic_is_deterministic_and_regimes_differ():
    a, ta = make_panel(n_days=900, seed=3)
    b, tb = make_panel(n_days=900, seed=3)
    pd.testing.assert_frame_equal(a["SPY"], b["SPY"])
    assert len(a) == len(UNIVERSE) and (a["BTC"].index.to_series().diff().dt.days.dropna() == 1).all()
    r = np.log(a["SPY"]["close"]).diff()
    vol = r.groupby(ta.reindex(r.index)).std()
    assert vol[2] > 1.8 * vol[0]                   # stress is clearly more volatile than calm
