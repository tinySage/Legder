import json
import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps
from arch import arch_model

from models import stats, garch, regimes, anomalies, forecasts, correlation, volatility
from pipeline.synthetic import make_panel
from tests.leakage import assert_causal


# ---- statistics ------------------------------------------------------------
def test_kupiec_matches_direct_likelihood_ratio():
    n, x, p = 500, 38, 0.05
    b = np.r_[np.ones(x), np.zeros(n - x)].astype(bool)
    k = stats.kupiec_pof(b, p)
    ll0 = x * np.log(p) + (n - x) * np.log(1 - p)
    ll1 = x * np.log(x / n) + (n - x) * np.log(1 - x / n)
    assert k["lr"] == pytest.approx(-2 * (ll0 - ll1))
    assert k["p_value"] == pytest.approx(sps.chi2.sf(k["lr"], 1))
    assert stats.kupiec_pof(np.r_[np.ones(25), np.zeros(475)].astype(bool), 0.05)["p_value"] == pytest.approx(1.0)


def test_christoffersen_flags_clustering_and_has_the_right_false_alarm_rate():
    rng = np.random.default_rng(11)
    iid_p = [stats.christoffersen_independence(rng.random(500) < 0.05)["p_value"] for _ in range(400)]
    assert 0.02 < np.mean(np.array(iid_p) < 0.05) < 0.10             # about 5% false alarms on independent breaches
    cluster = np.zeros(500, dtype=bool); cluster[200:225] = True       # 25 breaches in one burst
    assert stats.christoffersen_independence(cluster)["p_value"] < 0.001
    assert stats.christoffersen_independence(np.zeros(500, dtype=bool))["p_value"] == 1.0


def test_var_verdict_labels():
    k = lambda p, rate: {"p_value": p, "rate": rate, "expected": 25.0, "n": 500}
    i = lambda p: {"p_value": p}
    assert stats.var_verdict(k(0.5, 0.05), i(0.5)) == "Pass"
    assert stats.var_verdict(k(0.5, 0.05), i(0.01)) == "Clustered"
    assert stats.var_verdict(k(0.01, 0.09), i(0.5)) == "Too many"
    assert stats.var_verdict(k(0.01, 0.01), i(0.5)) == "Too few"


def test_diebold_mariano_detects_a_real_difference_and_a_tie():
    rng = np.random.default_rng(0)
    base = rng.normal(1.0, 0.2, 1000) ** 2
    assert stats.diebold_mariano(base, base)["p_value"] == pytest.approx(1.0)
    assert stats.diebold_mariano(base, base * 0.6)["p_value"] < 0.001


# ---- GARCH -----------------------------------------------------------------
def simulate_garch(n, seed=1):
    rng = np.random.default_rng(seed)
    r, s2 = np.zeros(n), np.ones(n)
    for t in range(1, n):
        s2[t] = 0.05 + 0.1 * r[t - 1] ** 2 + 0.85 * s2[t - 1]
        r[t] = np.sqrt(s2[t]) * rng.standard_normal()
    return r


def test_garch_filter_matches_the_arch_library():
    r = simulate_garch(1500)
    p = garch.fit_garch(r)
    ref = arch_model(r, mean="Constant", vol="GARCH", p=1, q=1, rescale=False).fit(disp="off").conditional_volatility
    mine = np.sqrt(garch.filter_sigma2(r, **p)[:-1])
    assert np.allclose(mine[-1000:], ref[-1000:], rtol=1e-6)


def test_garch_walk_forward_does_not_use_later_data():
    r = simulate_garch(1400)
    full, part = garch.walk_forward(r), garch.walk_forward(r[:1000])
    for name in ("s2", "mu", "omega", "persist"):
        a, b = getattr(full, name)[:1000], getattr(part, name)
        assert np.allclose(a, b, equal_nan=True), name


def test_multi_step_variance_forecast_reverts_to_long_run():
    long_run = 0.5 / (1 - 0.95)
    assert garch.avg_variance_forecast(long_run, 0.5, 0.95, 5) == pytest.approx(long_run)
    hi = garch.avg_variance_forecast(4 * long_run, 0.5, 0.95, 5)
    assert long_run < hi < 4 * long_run


# ---- regimes ---------------------------------------------------------------
def three_regime_series(n=1700, seed=5):
    rng = np.random.default_rng(seed)
    state = np.zeros(n, dtype=int)
    T = np.array([[0.98, 0.015, 0.005], [0.02, 0.97, 0.01], [0.04, 0.06, 0.90]])
    for i in range(1, n):
        state[i] = rng.choice(3, p=T[state[i - 1]])
    vol = np.array([0.5, 0.9, 3.0])[state]
    return rng.standard_normal(n) * vol + np.array([0.03, 0.08, -0.25])[state], state


def test_regime_model_finds_stress_when_it_exists():
    r, truth = three_regime_series()
    P = regimes.causal_probs(r)
    ok = ~np.isnan(P[:, 0])
    lab, tr = P[ok].argmax(axis=1), truth[ok]
    tp = ((lab == 2) & (tr == 2)).sum()
    assert tp / (tr == 2).sum() > 0.6          # most true stress days are called
    assert tp / max(1, (lab == 2).sum()) > 0.4  # and the stress label is not mostly false alarms
    assert np.allclose(P[ok].sum(axis=1), 1.0)


def test_regime_probabilities_use_only_past_data():
    r, _ = three_regime_series(1400)
    full, part = regimes.causal_probs(r), regimes.causal_probs(r[:1100])
    a, b = full[750:1100], part[750:1100]
    assert np.allclose(a, b, atol=1e-6)


def test_regime_spells():
    assert regimes.spells(np.array([0, 0, 0, 1, 1, 2])) == [3, 2, 1]


# ---- anomalies -------------------------------------------------------------
def test_a_ten_sigma_shock_is_flagged_and_robust_z_is_causal():
    rng = np.random.default_rng(2)
    idx = pd.bdate_range("2020-01-01", periods=900)
    r = pd.Series(rng.normal(0, 1, 900), index=idx)
    r.iloc[800] = -10.0
    vol = pd.Series(1e6, index=idx)
    df = anomalies.flag_asset(r, vol)
    assert df["flag"].iloc[800] and df["z"].iloc[800] < -8
    assert df["flag"].iloc[300:790].mean() < 0.06           # quiet days are mostly unflagged
    assert_causal(lambda d: anomalies.robust_z(d["r"]).to_frame(), r.to_frame("r"), checkpoints=(300, 500, 700))


def test_forward_stats_look_forward_only_where_intended():
    idx = pd.bdate_range("2021-01-01", periods=40)
    df = pd.DataFrame({"r": np.arange(40, dtype=float), "flag": False}, index=idx)
    fs = anomalies.forward_stats(df)
    assert fs["fwd_ret1"].iloc[3] == 4.0                       # next day's return
    assert fs["fwd_ret5"].iloc[3] == sum(range(4, 9))
    assert np.isnan(fs["fwd_vol5"].iloc[-1])                   # no future, no number


# ---- forecasts -------------------------------------------------------------
def test_forecast_models_do_not_beat_noise_but_find_real_autocorrelation():
    rng = np.random.default_rng(3)
    n = 1500
    idx = pd.bdate_range("2018-01-01", periods=n)
    noise = pd.Series(rng.normal(0, 1, n), index=idx)
    ar = np.zeros(n)
    e = rng.normal(0, 1, n)
    for t in range(1, n):
        ar[t] = 0.35 * ar[t - 1] + e[t]
    ar = pd.Series(ar, index=idx)
    res = forecasts.evaluate(pd.DataFrame({"SPY": noise, "BTC": ar}), assets=["SPY", "BTC"])
    assert res["per_asset"]["SPY"]["arima"]["rel_mae"] > 0.995         # nothing to find in noise
    assert res["per_asset"]["BTC"]["arima"]["rel_mae"] < 0.97          # real structure is found
    assert res["per_asset"]["BTC"]["arima"]["dm_p"] < 0.05


def test_zero_forecast_equals_the_baseline():
    y = np.random.default_rng(0).normal(0, 1, 500)
    s = forecasts.score(y, np.zeros(500))
    assert s["rel_mae"] == pytest.approx(1.0) and s["dm_p"] == pytest.approx(1.0)


# ---- correlation -----------------------------------------------------------
def test_correlation_rise_in_stress_is_detected_when_it_exists():
    rng = np.random.default_rng(4)
    n = 1200
    idx = pd.bdate_range("2019-01-01", periods=n)
    stress = rng.random(n) < 0.25
    common = rng.standard_normal(n)
    w = np.where(stress, 0.9, 0.2)[:, None]
    X = np.sqrt(w) * common[:, None] + np.sqrt(1 - w) * rng.standard_normal((n, 4))
    rets = pd.DataFrame(X, index=idx, columns=list("ABCD"))
    P = np.zeros((n, 3)); P[:, 0] = ~stress; P[:, 2] = stress
    out = correlation.calm_vs_stress(rets, P, idx, tickers=list("ABCD"))
    assert out["rises_in_stress"] and out["stress"] > out["calm"] + 0.3


# ---- end to end ------------------------------------------------------------
@pytest.mark.slow
def test_full_export_matches_the_json_contract():
    from pipeline.store import PriceStore
    from pipeline.clean import clean_series
    from models.common import build_context
    from models.export import build_all
    import scripts.run_all as run_all
    panel, _ = make_panel(n_days=1300)
    st = PriceStore()
    now = pd.Timestamp("2026-11-14 22:30", tz="UTC")
    keep = ["SPY", "QQQ", "AAPL", "XOM", "GLD", "TLT", "BTC", "ETH"]
    for t in keep:
        st.replace_history(t, clean_series(panel[t]), now.tz_localize(None))
    ctx = build_context(st, True, now, tickers=keep)
    files = run_all._clean(build_all(ctx))
    run_all.validate(files)
    assert files["meta.json"]["synthetic"] is True
    assert {"regimes.json", "risk.json", "correlation.json", "report.json", "assets/SPY.json"} <= set(files)
    json.dumps(files)                                              # no NaN or numpy types left
    names = [m["name"] for m in files["report.json"]["models"]]
    assert names == ["Volatility forecast", "Value-at-Risk line", "Regime detection",
                     "Unusual-move flags", "Price forecast", "Correlation structure"]
