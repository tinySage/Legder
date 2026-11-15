# Ledger

A financial dashboard presented as a market weather chart. Stocks, crypto and
commodities are shown as regions on a map; the models behind it are tested on
unseen data against simple baselines and the results are shown as found.

Work in progress. Built in four stages, each on its own branch:

1. `stage-1-data-pipeline`: fetching, cleaning, caching, tests
2. `stage-2-models`: volatility, risk, regimes, anomalies, correlation, forecasts
3. `stage-3-dashboard`: the five-sheet web app
4. `stage-4-ship`: scheduled refresh, deploy config, full README

`design/` holds the design canvas files (source of truth for the web app).

Educational tool, not financial advice.
