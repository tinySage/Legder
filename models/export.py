"""Run every model and assemble the JSON files the web app reads."""
from __future__ import annotations
import numpy as np
import pandas as pd
from pipeline.universe import UNIVERSE, BY_TICKER, MAP_CLASSES
from models import volatility, risk, regimes, anomalies, correlation, forecasts, report
from models.common import Ctx, class_returns, class_members

CREDITS = ["Prices: Yahoo Finance via yfinance", "Crypto snapshot: CoinGecko (https://www.coingecko.com)"]


def _r(x, k=4):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


def build_all(ctx: Ctx, fundamentals: dict | None = None, progress=lambda m: None) -> dict:
    fundamentals = fundamentals or {}
    tickers = [t for t in ctx.prices.columns]
    as_of = ctx.prices.index[-1].date().isoformat()
    meta_rows = ctx.meta.set_index("ticker") if len(ctx.meta) else pd.DataFrame()
    stale = {t: bool(len(meta_rows) and t in meta_rows.index and meta_rows.loc[t, "status"] != "ok") for t in tickers}

    # --- per-asset models -------------------------------------------------
    vol_eval, risk_res, flagged, probs = {}, {}, {}, {}
    for t in tickers:
        progress(f"models: {t}")
        s = ctx.series(t)
        if len(s) < regimes.MIN_TRAIN + 250:
            continue
        run = ctx.garch(t)
        vol_eval[t] = volatility.evaluate_asset(s.to_numpy(), run)
        risk_res[t] = risk.analyse_asset(s, run, ctx.prices[t])
        flagged[t] = anomalies.flag_asset(s, ctx.volume[t].reindex(s.index))
        probs[t] = regimes.causal_probs(s.to_numpy())
    modelled = list(risk_res)

    # --- class regimes ----------------------------------------------------
    classes, spells_by_series = [], {}
    class_probs = {}
    for cls in MAP_CLASSES:
        members = [m for m in class_members(cls) if m in ctx.rets]
        cr = class_returns(ctx, members)
        P = regimes.causal_probs(cr.to_numpy())
        class_probs[cls] = (P, cr.index)
        sm = regimes.summarise(P, cr.index)
        spells_by_series[cls] = sm["avg_spell_days"]
        ok = ~np.isnan(P[:, 0])
        classes.append({"name": cls, "regime": sm["regime"], "label": sm["label"], "days": sm["days"],
                        "confidence": _r(sm["confidence"]), "stress_probability": _r(sm["stress_probability"]),
                        "stress60": [_r(x) for x in P[ok][-60:, 2]], "avg_spell_days": _r(sm["avg_spell_days"], 1)})
    eq_P, eq_idx = class_probs[MAP_CLASSES[0]]
    eq_hist = regimes.history(eq_P, eq_idx)

    # --- stations and advisories -----------------------------------------
    stations = []
    for t in tickers:
        a = BY_TICKER[t]
        p = ctx.prices[t].dropna()
        stations.append({"ticker": t, "name": a.name, "cls": a.cls, "price": _r(p.iloc[-1], 2),
                         "change_1d": _r((p.iloc[-1] / p.iloc[-2] - 1) * 100, 2),
                         "spark": [_r(x, 2) for x in p.iloc[-10:]], "stale": stale[t]})
    adv = []
    for t, df in flagged.items():
        tail = df.iloc[-5:]
        for d, row in tail[tail["flag"]].iterrows():
            r = df["r"]
            prev = r.loc[:d].iloc[-251:-1].abs()
            z = row["z"] if not np.isnan(row["z"]) else 0.0
            if abs(z) >= anomalies.Z_FLAG:
                pct = float((prev < abs(row["r"])).mean() * 100)
                msg = f"Move of {abs(z):.1f} standard deviations {'up' if row['r'] > 0 else 'down'}, larger than {pct:.0f}% of the past year's daily moves."
            else:
                msg = "Return, volume and volatility pattern unlike the last 500 sessions, flagged by the isolation forest."
            adv.append({"ticker": t, "date": d.date().isoformat(), "message": msg, "_k": abs(z)})
    adv = sorted(adv, key=lambda x: -x["_k"])[:3]
    for a in adv: a.pop("_k")
    regimes_json = {"synthetic": ctx.synthetic, "as_of": as_of, "classes": classes, "equities_history": eq_hist,
                    "stations": stations, "advisories": adv}

    # --- asset pages ------------------------------------------------------
    assets_json = {}
    for t in modelled:
        a = BY_TICKER[t]
        s = ctx.series(t)
        run = ctx.garch(t)
        win = ctx.prices[t].dropna().iloc[-252:]
        sig5 = pd.Series(np.sqrt(run.s2) * np.sqrt(5) / 100, index=s.index).reindex(win.index).ffill().bfill()
        P = probs[t]
        pidx = pd.Series(["ctS"[int(np.argmax(p))] if not np.isnan(p[0]) else "" for p in P], index=s.index).reindex(win.index).fillna("")
        sm = regimes.summarise(P, s.index)
        fl = flagged[t]
        marks = [{"date": d.date().isoformat(), "z": _r(fl.loc[d, "z"], 2), "direction": "up" if fl.loc[d, "r"] > 0 else "down"}
                 for d in win.index if d in fl.index and bool(fl.loc[d, "flag"])]
        last_flag = fl[fl["flag"]].tail(1)
        last_unusual = None
        if len(last_flag):
            d = last_flag.index[0]
            last_unusual = {"date": d.date().isoformat(), "days_ago": int((ctx.prices.index[-1] - d).days),
                            "z": _r(last_flag["z"].iloc[0], 1), "direction": "Up" if last_flag["r"].iloc[0] > 0 else "Down"}
        vf = volatility.live_forecast(run)
        assets_json[t] = {
            "ticker": t, "name": a.name, "cls": a.cls, "as_of": win.index[-1].date().isoformat(), "stale": stale[t],
            "price": _r(win.iloc[-1], 2), "change_1d": _r((win.iloc[-1] / win.iloc[-2] - 1) * 100, 2),
            "regime": {"key": sm["regime"], "label": sm["label"], "days": sm["days"], "confidence": _r(sm["confidence"])},
            "window": {"dates": [d.date().isoformat() for d in win.index], "close": [_r(x, 3) for x in win],
                       "codes": list(pidx), "band_lo": [_r(x * (1 - v), 3) for x, v in zip(win, sig5)],
                       "band_hi": [_r(x * (1 + v), 3) for x, v in zip(win, sig5)], "marks": marks},
            "model": {"regime": sm["label"], "var95_pct": _r(risk_res[t]["live"]["var95"], 2),
                      "vol_forecast_5d_annualised_pct": _r(vf["annualised_pct"], 1), "last_unusual_move": last_unusual},
            "fundamentals": fundamentals.get(t),
        }

    # --- risk -------------------------------------------------------------
    risk_json = {"synthetic": ctx.synthetic, "as_of": as_of, "assets": risk_res}

    # --- correlation ------------------------------------------------------
    tick = [t for t in correlation.DISPLAY if t in ctx.rets]
    P_eq, idx_eq = class_probs[MAP_CLASSES[0]]
    cvs = correlation.calm_vs_stress(ctx.rets, P_eq, idx_eq, tick)
    corr_json = {"synthetic": ctx.synthetic, "tickers": tick, "default_window": 60,
                 "matrices": correlation.matrices(ctx.rets, tick), "calm_vs_stress": cvs}

    # --- report -----------------------------------------------------------
    progress("forecasts")
    fc = forecasts.evaluate(ctx.rets)
    anom = anomalies.evaluate(flagged)
    vol_sum = volatility.summarise(vol_eval)
    spells = {t: regimes.summarise(probs[t], ctx.series(t).index)["avg_spell_days"] for t in modelled}
    rep = report.build(vol_sum, risk_res, spells, anom, fc, cvs, ctx.synthetic)
    rep["evaluation_detail"] = {"volatility": vol_eval, "anomalies": anom, "forecasts": fc,
                                "regime_spells_by_asset": spells}

    meta = {"synthetic": ctx.synthetic, "models_run_at": ctx.now.isoformat(),
            "fetched_at": (str(ctx.meta["last_ok"].dropna().max()) if len(ctx.meta) and ctx.meta["last_ok"].notna().any() else None),
            "assets": {t: {"status": ("stale" if stale[t] else "ok"),
                           "last_ok": (str(meta_rows.loc[t, "last_ok"]) if len(meta_rows) and t in meta_rows.index else None)} for t in tickers},
            "credits": CREDITS}
    out = {"meta.json": meta, "regimes.json": regimes_json, "risk.json": risk_json,
           "correlation.json": corr_json, "report.json": rep}
    for t, v in assets_json.items():
        out[f"assets/{t}.json"] = v
    return out
