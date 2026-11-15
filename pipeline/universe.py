"""The assets Ledger tracks. One place to change the universe."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    ticker: str   # short name shown in the UI
    name: str
    cls: str      # "Equities" | "Crypto" | "Commodities and FX" | "Rates"
    yahoo: str    # symbol used to fetch history
    kind: str     # "stock" | "etf" | "crypto"


EQUITIES = "Equities"
CRYPTO = "Crypto"
COMMODITIES_FX = "Commodities and FX"
RATES = "Rates"  # shown in correlation, not as a map region

UNIVERSE = [
    Asset("SPY", "S&P 500 ETF", EQUITIES, "SPY", "etf"),
    Asset("QQQ", "Nasdaq 100 ETF", EQUITIES, "QQQ", "etf"),
    Asset("AAPL", "Apple", EQUITIES, "AAPL", "stock"),
    Asset("MSFT", "Microsoft", EQUITIES, "MSFT", "stock"),
    Asset("NVDA", "Nvidia", EQUITIES, "NVDA", "stock"),
    Asset("JPM", "JPMorgan Chase", EQUITIES, "JPM", "stock"),
    Asset("XOM", "Exxon Mobil", EQUITIES, "XOM", "stock"),
    Asset("UNH", "UnitedHealth", EQUITIES, "UNH", "stock"),
    Asset("PG", "Procter & Gamble", EQUITIES, "PG", "stock"),
    Asset("WMT", "Walmart", EQUITIES, "WMT", "stock"),
    Asset("CAT", "Caterpillar", EQUITIES, "CAT", "stock"),
    Asset("BTC", "Bitcoin", CRYPTO, "BTC-USD", "crypto"),
    Asset("ETH", "Ethereum", CRYPTO, "ETH-USD", "crypto"),
    Asset("SOL", "Solana", CRYPTO, "SOL-USD", "crypto"),
    Asset("GLD", "Gold ETF", COMMODITIES_FX, "GLD", "etf"),
    Asset("USO", "Oil ETF", COMMODITIES_FX, "USO", "etf"),
    Asset("UUP", "US dollar ETF", COMMODITIES_FX, "UUP", "etf"),
    Asset("FXE", "Euro ETF", COMMODITIES_FX, "FXE", "etf"),
    Asset("TLT", "Long Treasury ETF", RATES, "TLT", "etf"),
]

BY_TICKER = {a.ticker: a for a in UNIVERSE}
MAP_CLASSES = [EQUITIES, CRYPTO, COMMODITIES_FX]
CALENDAR_ANCHOR = "SPY"   # its trading days define the common calendar
HISTORY_START = "2015-01-01"
