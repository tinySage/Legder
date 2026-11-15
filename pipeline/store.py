"""DuckDB price store. Adjusted history is replaced whole on each refresh,
because dividends and splits change every past adjusted price."""
from __future__ import annotations
import pandas as pd
import duckdb


class PriceStore:
    def __init__(self, path: str = ":memory:"):
        self.con = duckdb.connect(path)
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS prices ("
            "ticker VARCHAR, date DATE, close DOUBLE, volume DOUBLE, "
            "PRIMARY KEY (ticker, date))"
        )
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS meta ("
            "ticker VARCHAR PRIMARY KEY, last_ok TIMESTAMP, status VARCHAR, error VARCHAR)"
        )

    def replace_history(self, ticker: str, df: pd.DataFrame, now: pd.Timestamp) -> None:
        """df: index = dates, columns close, volume. Replaces the ticker's rows atomically."""
        d = df[["close", "volume"]].copy()
        d.insert(0, "ticker", ticker)
        d.insert(1, "date", pd.to_datetime(d.index).date)
        self.con.execute("BEGIN")
        try:
            self.con.execute("DELETE FROM prices WHERE ticker = ?", [ticker])
            self.con.register("_incoming", d.reset_index(drop=True))
            self.con.execute("INSERT INTO prices SELECT ticker, date, close, volume FROM _incoming")
            self.con.unregister("_incoming")
            self.con.execute(
                "INSERT OR REPLACE INTO meta VALUES (?, ?, 'ok', NULL)", [ticker, now.to_pydatetime()]
            )
            self.con.execute("COMMIT")
        except Exception:
            self.con.execute("ROLLBACK")
            raise

    def mark_stale(self, ticker: str, error: str) -> None:
        """Keep the old prices, record that the latest fetch failed."""
        row = self.con.execute("SELECT last_ok FROM meta WHERE ticker = ?", [ticker]).fetchone()
        last_ok = row[0] if row else None
        self.con.execute(
            "INSERT OR REPLACE INTO meta VALUES (?, ?, 'stale', ?)", [ticker, last_ok, error[:300]]
        )

    def history(self, ticker: str) -> pd.DataFrame:
        df = self.con.execute(
            "SELECT date, close, volume FROM prices WHERE ticker = ? ORDER BY date", [ticker]
        ).df()
        if df.empty:
            return pd.DataFrame(columns=["close", "volume"], index=pd.DatetimeIndex([], name="date"))
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date")

    def meta(self) -> pd.DataFrame:
        return self.con.execute("SELECT * FROM meta ORDER BY ticker").df()

    def tickers(self) -> list[str]:
        return [r[0] for r in self.con.execute("SELECT DISTINCT ticker FROM prices ORDER BY 1").fetchall()]
