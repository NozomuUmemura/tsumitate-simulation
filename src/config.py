from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Horizon:
    name: str
    years: int


DEFAULT_HORIZONS: tuple[Horizon, ...] = (
    Horizon(name="short", years=1),
    Horizon(name="mid", years=3),
    Horizon(name="long", years=5),
    Horizon(name="ultra_long", years=10),
)

# 実データ用ティッカー（画面表示名は TICKER_LABELS を使用）
DEFAULT_TICKERS: tuple[str, ...] = (
    "ACWI",   # オルカンの代理（全世界株）
    "SPY",    # S&P500
    "^N225",  # 日経平均
)

TICKER_LABELS: dict[str, str] = {
    "ACWI": "オルカン",
    "SPY": "S&P500",
    "^N225": "日経平均",
}

DEFAULT_BENCHMARK = "SPY"
DEFAULT_INITIAL_CAPITAL = 100_000  # 円建て想定の初期元本（任意）
DEFAULT_MONTHLY_CONTRIBUTION = 100_000

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "outputs"
TEARSHEET_DIR = OUTPUT_DIR / "tearsheets"

TODAY = date.today()
