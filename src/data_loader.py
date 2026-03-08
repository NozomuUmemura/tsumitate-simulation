from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
TZ_CACHE_DIR = ROOT / "data" / "tz_cache"


def download_close_prices(tickers: Iterable[str], period: str = "max") -> pd.DataFrame:
    """Download adjusted close-like prices for each ticker."""
    tickers = list(dict.fromkeys(tickers))

    # Use a local timezone cache to avoid lock conflicts with global cache files.
    TZ_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(TZ_CACHE_DIR))

    data = yf.download(
        tickers=tickers,
        period=period,
        auto_adjust=True,
        progress=False,
        # yfinance occasionally raises sqlite timezone-cache lock errors in threaded mode.
        threads=False,
    )

    if data.empty:
        raise ValueError("No price data downloaded. Check ticker symbols and network connectivity.")

    if isinstance(data.columns, pd.MultiIndex):
        closes = data["Close"].copy()
    else:
        closes = data.to_frame(name=tickers[0])

    closes = closes.sort_index().dropna(how="all")
    closes = closes.ffill().dropna(how="all")
    closes = closes.dropna(axis=1, how="all")

    if closes.empty:
        raise ValueError("Close price table is empty after cleanup.")

    return closes
