"""Latest-year fundamentals from Yahoo statements. Anything missing becomes None, never a guess."""
from __future__ import annotations
import math


def _latest(df, names):
    if df is None or getattr(df, "empty", True):
        return None
    for n in names:
        if n in df.index:
            row = df.loc[n].dropna()
            if len(row):
                v = float(row.iloc[0])
                return None if math.isnan(v) else v
    return None


def extract(financials, balance_sheet, cashflow) -> dict:
    rev = _latest(financials, ["Total Revenue", "Operating Revenue"])
    ni = _latest(financials, ["Net Income", "Net Income Common Stockholders"])
    op = _latest(financials, ["Operating Income", "Total Operating Income As Reported"])
    debt = _latest(balance_sheet, ["Total Debt"])
    eq = _latest(balance_sheet, ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
    fcf = _latest(cashflow, ["Free Cash Flow"])
    fy = None
    try:
        fy = str(financials.columns[0].date())
    except Exception:
        pass
    return {
        "fiscal_year_end": fy,
        "revenue": rev,
        "net_income": ni,
        "operating_margin": (op / rev) if (op is not None and rev) else None,
        "debt_to_equity": (debt / eq) if (debt is not None and eq) else None,
        "free_cash_flow": fcf,
    }


def fetch_fundamentals(symbol: str) -> dict | None:
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        out = extract(t.financials, t.balance_sheet, t.cashflow)
        return out if any(v is not None for k, v in out.items() if k != "fiscal_year_end") else None
    except Exception:
        return None
