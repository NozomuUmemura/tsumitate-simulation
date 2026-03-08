from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd
import vectorbt as vbt

from src.config import DEFAULT_HORIZONS, Horizon


@dataclass
class HorizonResult:
    ticker: str
    horizon: str
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    total_return_pct: float
    unrealized_pnl: float
    cagr_pct: float
    max_drawdown_pct: float


def _slice_by_years(prices: pd.Series, years: int) -> pd.Series:
    end_date = prices.index.max()
    start_target = end_date - pd.DateOffset(years=years)
    window = prices[prices.index >= start_target].dropna()
    return window


def analyze_ticker_horizons(
    ticker: str,
    prices: pd.Series,
    initial_capital: float,
    horizons: Iterable[Horizon] = DEFAULT_HORIZONS,
) -> list[HorizonResult]:
    results: list[HorizonResult] = []
    clean = prices.dropna()

    for horizon in horizons:
        window = _slice_by_years(clean, horizon.years)
        if len(window) < 2:
            continue

        # Set explicit frequency so annualized metrics are always computable.
        pf = vbt.Portfolio.from_holding(close=window, init_cash=initial_capital, freq="1D")
        start_price = float(window.iloc[0])
        end_price = float(window.iloc[-1])
        total_return = float(pf.total_return())
        cagr = float(pf.annualized_return())
        max_dd = float(pf.max_drawdown())

        results.append(
            HorizonResult(
                ticker=ticker,
                horizon=horizon.name,
                start_date=str(window.index[0].date()),
                end_date=str(window.index[-1].date()),
                start_price=start_price,
                end_price=end_price,
                total_return_pct=total_return * 100,
                unrealized_pnl=initial_capital * total_return,
                cagr_pct=cagr * 100,
                max_drawdown_pct=max_dd * 100,
            )
        )

    return results


def build_summary_table(
    closes: pd.DataFrame,
    initial_capital: float,
    horizons: Iterable[Horizon] = DEFAULT_HORIZONS,
) -> pd.DataFrame:
    rows: list[dict] = []
    for ticker in closes.columns:
        ticker_results = analyze_ticker_horizons(
            ticker=ticker,
            prices=closes[ticker],
            initial_capital=initial_capital,
            horizons=horizons,
        )
        rows.extend(asdict(r) for r in ticker_results)

    if not rows:
        raise ValueError("No analysis rows were produced. Not enough data in selected horizons.")

    df = pd.DataFrame(rows)
    return df.sort_values(["horizon", "ticker"]).reset_index(drop=True)


def compute_daily_returns(closes: pd.DataFrame) -> pd.DataFrame:
    returns = closes.pct_change().replace([pd.NA], 0.0).fillna(0.0)
    return returns
