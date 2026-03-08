# portfolio-horizon-analyzer

`yfinance + vectorbt + QuantStats` で、短期・中期・長期・超長期の含み益比較と、リッチな日本語ダッシュボードを作る構成です。

## 現在の比較対象（デフォルト）

- オルカン（代理）: `ACWI`
- S&P500: `SPY`
- 日経平均: `^N225`

## ディレクトリ構成

```text
Codex/
├─ data/
├─ outputs/
│  └─ tearsheets/
├─ scripts/
│  └─ run_analysis.py
├─ src/
│  ├─ analysis.py
│  ├─ config.py
│  ├─ data_loader.py
│  └─ reporting.py
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 実行

```powershell
python scripts\run_analysis.py
```

オプション例:

```powershell
python scripts\run_analysis.py --tickers ACWI SPY ^N225 --benchmark SPY --initial-capital 100000 --monthly-contribution 100000
```

## 出力

- `outputs/horizon_summary.csv`
- `outputs/cumulative_returns_weekly.csv`
- `outputs/horizon_summary.html`
- `outputs/tearsheets/*.html`

## UIでできること

- 期間切替: 短期(1年) / 中期(3年) / 長期(5年) / 超長期(10年)
- テーマ切替: Preset A（白基調）/ Preset B（ダーク基調）
- 固定ヘッダー、0.4秒スムーズスクロール、200msモバイルハンバーガー
- 3種類のグラフ（ランキング、散布図、累積推移）
- ページ末尾の将来積立シミュレーター（毎月10万円初期値）

## GitHub 共有リンクを作る手順

```powershell
git init
git add .
git commit -m "Add rich Japanese dashboard with 10y horizon and simulator"
git remote add origin https://github.com/<your-account>/<repo-name>.git
git branch -M main
git push -u origin main
```

共有リンク: `https://github.com/<your-account>/<repo-name>`
