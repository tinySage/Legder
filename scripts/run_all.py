"""Run every model and write the JSON the web app reads.
   python scripts/run_all.py --db cache/prices.duckdb --out web/public/data [--synthetic] [--fundamentals]"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.store import PriceStore
from pipeline.universe import UNIVERSE
from models.common import build_context
from models.export import build_all
from models.schemas import SCHEMAS, ASSET


def _clean(o):
    if isinstance(o, dict): return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if np.isnan(o) or np.isinf(o) else float(o)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    return o


def validate(files: dict) -> None:
    for name, doc in files.items():
        schema = ASSET if name.startswith("assets/") else SCHEMAS.get(name)
        if schema is not None:
            jsonschema.validate(doc, schema)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="cache/prices.duckdb")
    ap.add_argument("--out", default="web/public/data")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--fundamentals", action="store_true")
    args = ap.parse_args()
    store = PriceStore(args.db)
    now = pd.Timestamp.now(tz="UTC")
    ctx = build_context(store, args.synthetic, now)
    fund = {}
    if args.fundamentals and not args.synthetic:
        from pipeline.fundamentals import fetch_fundamentals
        fund = {a.ticker: fetch_fundamentals(a.yahoo) for a in UNIVERSE if a.kind == "stock"}
    t0 = time.time()
    files = _clean(build_all(ctx, fund, progress=lambda m: print(f"  {m}", flush=True)))
    validate(files)
    out = Path(args.out)
    for name, doc in files.items():
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc, separators=(",", ":")))
    print(f"wrote {len(files)} files to {out} in {time.time() - t0:.0f}s (synthetic={args.synthetic})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
