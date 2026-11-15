"""JSON contract between the Python models and the web app. CI fails if an output file does not match."""
NUM = {"type": "number"}
NUM_OR_NULL = {"type": ["number", "null"]}
STR = {"type": "string"}
ARR = lambda item: {"type": "array", "items": item}

META = {
    "type": "object",
    "required": ["synthetic", "models_run_at", "assets", "credits"],
    "properties": {"synthetic": {"type": "boolean"}, "models_run_at": STR, "fetched_at": {"type": ["string", "null"]},
                   "assets": {"type": "object"}, "credits": ARR(STR)},
}
REGIMES = {
    "type": "object",
    "required": ["synthetic", "as_of", "classes", "equities_history", "stations", "advisories"],
    "properties": {
        "classes": ARR({"type": "object", "required": ["name", "regime", "label", "days", "confidence", "stress_probability", "stress60"],
                        "properties": {"regime": {"enum": ["calm", "trend", "stress"]}, "stress60": ARR(NUM)}}),
        "equities_history": {"type": "object", "required": ["dates", "codes", "stress_probability"]},
        "stations": ARR({"type": "object", "required": ["ticker", "name", "cls", "price", "change_1d", "spark", "stale"]}),
        "advisories": ARR({"type": "object", "required": ["ticker", "date", "message"]}),
    },
}
ASSET = {
    "type": "object",
    "required": ["ticker", "name", "cls", "as_of", "stale", "window", "regime", "model", "fundamentals"],
    "properties": {
        "window": {"type": "object", "required": ["dates", "close", "codes", "band_lo", "band_hi", "marks"],
                   "properties": {"close": ARR(NUM), "band_lo": ARR(NUM), "band_hi": ARR(NUM)}},
        "model": {"type": "object", "required": ["regime", "var95_pct", "vol_forecast_5d_annualised_pct"]},
    },
}
RISK = {"type": "object", "required": ["synthetic", "as_of", "assets"],
        "properties": {"assets": {"type": "object", "additionalProperties": {
            "type": "object", "required": ["live", "backtest", "verdict", "last120", "drawdown"]}}}}
CORRELATION = {"type": "object", "required": ["synthetic", "tickers", "matrices", "calm_vs_stress"],
               "properties": {"tickers": ARR(STR), "matrices": {"type": "object"}}}
REPORT = {"type": "object", "required": ["synthetic", "forecast_vs_baseline", "models"],
          "properties": {"forecast_vs_baseline": ARR({"type": "object", "required": ["name", "value"]}),
                         "models": ARR({"type": "object", "required": ["name", "verdict", "what", "test", "result", "limit"]})}}

SCHEMAS = {"meta.json": META, "regimes.json": REGIMES, "risk.json": RISK, "correlation.json": CORRELATION, "report.json": REPORT}
