from __future__ import annotations

import argparse
import re
import sys
from shutil import copy2
from pathlib import Path

import quantstats as qs

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.analysis import build_summary_table, compute_daily_returns
from src.config import (
    DEFAULT_BENCHMARK,
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_MONTHLY_CONTRIBUTION,
    DEFAULT_TICKERS,
    OUTPUT_DIR,
    TEARSHEET_DIR,
    TICKER_LABELS,
)
from src.data_loader import download_close_prices
from src.reporting import write_summary_csv, write_summary_html, write_tsumitate_simulation_html


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="短期・中期・長期・超長期の含み益比較 + QuantStatsレポート生成")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=list(DEFAULT_TICKERS),
        help="分析対象ティッカー（例: ACWI SPY ^N225）",
    )
    parser.add_argument(
        "--benchmark",
        default=DEFAULT_BENCHMARK,
        help="ベンチマークティッカー（デフォルト: SPY）",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=DEFAULT_INITIAL_CAPITAL,
        help="含み損益計算に使う初期元本（デフォルト: 100000）",
    )
    parser.add_argument(
        "--monthly-contribution",
        type=float,
        default=DEFAULT_MONTHLY_CONTRIBUTION,
        help="将来積立シミュレーターの月次積立額（デフォルト: 100000）",
    )
    return parser.parse_args()


def _safe_name(symbol: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", symbol)


def generate_quantstats_reports(returns, benchmark: str) -> None:
    TEARSHEET_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in returns.columns:
        out_file = TEARSHEET_DIR / f"{_safe_name(ticker)}_tearsheet.html"
        if ticker == benchmark:
            qs.reports.html(returns[ticker], output=str(out_file), title=f"{ticker} Tearsheet")
        else:
            qs.reports.html(
                returns[ticker],
                benchmark=returns[benchmark],
                output=str(out_file),
                title=f"{ticker} vs {benchmark}",
            )


def build_cumulative_returns(closes):
    cumulative = closes.divide(closes.iloc[0]).subtract(1.0)
    cumulative = cumulative.resample("W-FRI").last().dropna(how="all")
    return cumulative


def main() -> None:
    args = parse_args()

    requested_tickers = list(dict.fromkeys(args.tickers + [args.benchmark]))
    closes = download_close_prices(tickers=requested_tickers, period="max")

    missing = [t for t in requested_tickers if t not in closes.columns]
    if missing:
        print(f"Warning: dropped tickers with no data: {', '.join(missing)}")

    if args.benchmark not in closes.columns:
        raise ValueError(
            f"Benchmark {args.benchmark} was not downloaded. "
            f"Choose one of: {', '.join(closes.columns)}"
        )

    summary = build_summary_table(closes=closes, initial_capital=args.initial_capital)
    summary.insert(1, "display_name", summary["ticker"].map(lambda t: TICKER_LABELS.get(t, t)))
    cumulative = build_cumulative_returns(closes)

    summary_csv = OUTPUT_DIR / "horizon_summary.csv"
    summary_html = OUTPUT_DIR / "horizon_summary.html"
    cumulative_csv = OUTPUT_DIR / "cumulative_returns_weekly.csv"
    tsumitate_html = OUTPUT_DIR / "tsumitate_simulation.html"

    source_image = ROOT / "image.png"
    if source_image.exists():
        copy2(source_image, OUTPUT_DIR / "image.png")

    source_image2 = ROOT / "image2.png"
    if source_image2.exists():
        copy2(source_image2, OUTPUT_DIR / "image2.png")

    write_summary_csv(summary, summary_csv)
    cumulative_export = cumulative.reset_index()
    cumulative_export = cumulative_export.rename(columns={cumulative_export.columns[0]: "date"})
    write_summary_csv(cumulative_export, cumulative_csv)
    write_summary_html(
        summary,
        summary_html,
        cumulative_df=cumulative,
        title="短期・中期・長期・超長期 含み益比較ダッシュボード",
        ticker_labels=TICKER_LABELS,
        monthly_contribution=args.monthly_contribution,
    )

    # Major preset universe for the standalone tsumitate simulator.
    presets: list[dict[str, object]] = [
        {"ticker": "ACWI", "label": "オルカン（全世界株）", "annual_return": 0.065, "annual_vol": 0.17},
        {"ticker": "SPY", "label": "S&P500", "annual_return": 0.075, "annual_vol": 0.19},
        {"ticker": "^N225", "label": "日経平均", "annual_return": 0.055, "annual_vol": 0.22},
        {"ticker": "VTI", "label": "米国株式（全体）", "annual_return": 0.072, "annual_vol": 0.18},
        {"ticker": "QQQ", "label": "NASDAQ100", "annual_return": 0.085, "annual_vol": 0.26},
        {"ticker": "VEA", "label": "先進国株（除く米国）", "annual_return": 0.055, "annual_vol": 0.18},
        {"ticker": "VWO", "label": "新興国株", "annual_return": 0.060, "annual_vol": 0.24},
        {"ticker": "EFA", "label": "MSCI EAFE", "annual_return": 0.053, "annual_vol": 0.17},
        {"ticker": "EEM", "label": "MSCI Emerging", "annual_return": 0.062, "annual_vol": 0.25},
        {"ticker": "GLD", "label": "金（ゴールド）", "annual_return": 0.038, "annual_vol": 0.16},
        {"ticker": "AGG", "label": "米国総合債券", "annual_return": 0.028, "annual_vol": 0.07},
        {"ticker": "BND", "label": "米国債券（BND）", "annual_return": 0.027, "annual_vol": 0.06},
        {"ticker": "VNQ", "label": "米国REIT", "annual_return": 0.050, "annual_vol": 0.21},
        {"ticker": "BTC-USD", "label": "ビットコイン", "annual_return": 0.120, "annual_vol": 0.60},
        {"ticker": "6448.T", "label": "ブラザー工業", "annual_return": 0.062, "annual_vol": 0.27},
        {"ticker": "7203.T", "label": "トヨタ", "annual_return": 0.067, "annual_vol": 0.24},
        {"ticker": "6902.T", "label": "DENSO", "annual_return": 0.064, "annual_vol": 0.25},
        {"ticker": "7951.T", "label": "ヤマハ株式会社", "annual_return": 0.058, "annual_vol": 0.23},
        {"ticker": "7974.T", "label": "任天堂", "annual_return": 0.072, "annual_vol": 0.29},
        {"ticker": "9983.T", "label": "ファーストリテイリング", "annual_return": 0.070, "annual_vol": 0.28},
    ]

    # Override default return assumptions with calculated CAGR when available.
    for ticker in summary["ticker"].unique():
        ticker_rows = summary[summary["ticker"] == ticker]
        ultra = ticker_rows[ticker_rows["horizon"] == "ultra_long"]
        long_ = ticker_rows[ticker_rows["horizon"] == "long"]
        base = ultra if not ultra.empty else long_
        if base.empty:
            base = ticker_rows
        cagr = max(-0.95, float(base.iloc[0]["cagr_pct"]) / 100)

        matched = False
        for item in presets:
            if item["ticker"] == ticker:
                item["annual_return"] = cagr
                matched = True
                break

        if not matched:
            presets.append(
                {
                    "ticker": ticker,
                    "label": TICKER_LABELS.get(ticker, ticker),
                    "annual_return": cagr,
                    "annual_vol": 0.20,
                }
            )

    write_tsumitate_simulation_html(
        output_path=tsumitate_html,
        presets=presets,
        monthly_contribution=args.monthly_contribution,
        hero_image="image.png",
        hero_image2="image2.png",
    )

    returns = compute_daily_returns(closes)
    qs.extend_pandas()
    generate_quantstats_reports(returns=returns, benchmark=args.benchmark)

    print(f"Saved: {summary_csv}")
    print(f"Saved: {cumulative_csv}")
    print(f"Saved: {summary_html}")
    print(f"Saved: {tsumitate_html}")
    print(f"Saved: {TEARSHEET_DIR}")


if __name__ == "__main__":
    main()










