"""Fetch every asset into the DuckDB store.
Real run:   python scripts/fetch.py --db cache/prices.duckdb
Dev/test:   python scripts/fetch.py --synthetic --db cache/synthetic.duckdb
A failed asset keeps its old prices and is marked stale; an empty result never
overwrites good data."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.universe import UNIVERSE, HISTORY_START, CALENDAR_ANCHOR
from pipeline.store import PriceStore
from pipeline.clean import clean_series, drop_incomplete_last_bar, quality_report
from pipeline import fetch as F


def run(db: str, synthetic: bool, now: pd.Timestamp | None = None, fetcher=None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    store = PriceStore(db)
    fetcher = fetcher or F.fetch_yahoo
    results = {}
    if synthetic:
        from pipeline.synthetic import make_panel
        panel, _ = make_panel()
    for a in UNIVERSE:
        try:
            raw = panel[a.ticker] if synthetic else fetcher(a.yahoo, HISTORY_START)
            df = drop_incomplete_last_bar(clean_series(raw), a.kind, now)
            if len(df) < 250:
                raise F.FetchError(f"{a.ticker}: only {len(df)} rows")
            store.replace_history(a.ticker, df, now.tz_localize(None) if now.tzinfo else now)
            results[a.ticker] = "ok"
        except Exception as e:  # keep old data, record the failure
            store.mark_stale(a.ticker, str(e))
            results[a.ticker] = f"stale: {e}"
    panel_db = {t: store.history(t) for t in store.tickers()}
    report = quality_report(panel_db) if panel_db else pd.DataFrame()
    return {
        "synthetic": synthetic,
        "ran_at": now.isoformat(),
        "results": results,
        "quality": report.to_dict("records"),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="cache/prices.duckdb")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    out = run(args.db, args.synthetic)
    text = json.dumps(out, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    bad = [t for t, s in out["results"].items() if s != "ok"]
    sys.exit(1 if bad and not args.synthetic and len(bad) == len(out["results"]) else 0)
