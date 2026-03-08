from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def write_summary_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def _json_records(df: pd.DataFrame) -> str:
    return json.dumps(json.loads(df.to_json(orient="records", date_format="iso")), ensure_ascii=False)


def write_summary_html(
    df: pd.DataFrame,
    output_path: Path,
    cumulative_df: pd.DataFrame,
    title: str = "Horizon Comparison",
    ticker_labels: dict[str, str] | None = None,
    monthly_contribution: float = 100_000,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_json = _json_records(df.copy())

    cum = cumulative_df.copy().reset_index()
    cum = cum.rename(columns={cum.columns[0]: "date"})
    cum["date"] = pd.to_datetime(cum["date"]).dt.strftime("%Y-%m-%d")
    cumulative_json = _json_records(cum)

    labels_json = json.dumps(ticker_labels or {}, ensure_ascii=False)

    template = """<!doctype html>
<html lang="ja" data-theme="preset-a">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Noto Sans JP"', '"Segoe UI"', 'sans-serif']
          },
          boxShadow: {
            card: '0 16px 40px rgba(15, 23, 42, 0.14)'
          }
        }
      }
    }
  </script>
  <style>
    :root {
      --header-h: 68px;
      --bg-grad: linear-gradient(120deg, #f3f7ff 0%, #f9fcff 58%, #ffffff 100%);
      --card: rgba(255,255,255,.86);
      --card-border: rgba(255,255,255,.92);
      --text: #0f172a;
      --muted: #475569;
      --accent: #0284c7;
      --accent-2: #0ea5e9;
      --nav-color: rgba(255,255,255,.95);
      --nav-hover: #bae6fd;
    }

    html[data-theme="preset-b"] {
      --bg-grad: radial-gradient(1000px 460px at 80% -5%, rgba(244,63,94,.2), transparent 55%), radial-gradient(840px 390px at 5% -15%, rgba(16,185,129,.2), transparent 60%), #03050b;
      --card: rgba(12, 16, 27, .78);
      --card-border: rgba(255,255,255,.12);
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #f43f5e;
      --accent-2: #34d399;
      --nav-color: rgba(248,250,252,.93);
      --nav-hover: #fda4af;
    }

    body {
      margin: 0;
      background: var(--bg-grad);
      color: var(--text);
      min-height: 100vh;
    }

    .glass-card {
      background: var(--card);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(9px);
      box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
    }

    .fixed-header {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: var(--header-h);
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 50;
      padding: 0 16px;
      background: linear-gradient(180deg, rgba(0,0,0,.32), rgba(0,0,0,.04));
      backdrop-filter: blur(10px);
      transition: background 280ms ease, box-shadow 280ms ease;
    }

    .fixed-header:hover {
      background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 24%, transparent), rgba(0,0,0,.1));
      box-shadow: 0 6px 28px rgba(0,0,0,.24);
    }

    .nav-link {
      color: var(--nav-color);
      text-decoration: none;
      padding: 8px 12px;
      border-radius: 999px;
      transition: color 220ms ease, background 220ms ease, transform 220ms ease;
    }

    .nav-link:hover {
      color: var(--nav-hover);
      background: rgba(255,255,255,.12);
      transform: translateY(-1px);
    }

    .hamburger {
      display: none;
      width: 42px;
      height: 42px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,.35);
      background: rgba(255,255,255,.12);
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    .hamburger-line,
    .hamburger-line::before,
    .hamburger-line::after {
      content: "";
      display: block;
      width: 20px;
      height: 2px;
      background: #fff;
      transition: transform 200ms ease, top 200ms ease, opacity 200ms ease;
      position: relative;
    }

    .hamburger-line::before { position: absolute; top: -6px; left: 0; }
    .hamburger-line::after { position: absolute; top: 6px; left: 0; }
    .hamburger.active .hamburger-line { opacity: 0; }
    .hamburger.active .hamburger-line::before { top: 0; opacity: 1; transform: rotate(45deg); }
    .hamburger.active .hamburger-line::after { top: 0; opacity: 1; transform: rotate(-45deg); }

    .mobile-panel {
      position: fixed;
      top: var(--header-h);
      left: 12px;
      right: 12px;
      z-index: 49;
      border-radius: 14px;
      opacity: 0;
      transform: translateY(-10px);
      pointer-events: none;
      transition: all 200ms ease;
    }

    .mobile-panel.open {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
    }

    .fade-up { opacity: 0; transform: translateY(16px); }
    .fade-up.in { opacity: 1; transform: translateY(0); transition: all 500ms ease; }

    .theme-btn.active,
    .h-btn.active {
      color: #fff;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      border-color: transparent;
    }

    @media (max-width: 900px) {
      .desktop-nav { display: none; }
      .hamburger { display: inline-flex; }
    }
  </style>
</head>
<body class="font-sans">
  <header class="fixed-header">
    <div class="text-white font-extrabold tracking-wide">投資ダッシュボード</div>
    <nav class="desktop-nav flex items-center gap-2">
      <a href="#overview" class="nav-link">概要</a>
      <a href="#charts" class="nav-link">グラフ</a>
      <a href="#table" class="nav-link">比較表</a>
      <a href="#simulator" class="nav-link">将来シミュレーター</a>
    </nav>
    <button id="hamburger" class="hamburger" aria-label="menu"><span class="hamburger-line"></span></button>
  </header>

  <div id="mobilePanel" class="mobile-panel glass-card p-2">
    <a href="#overview" class="block rounded-xl px-3 py-2">概要</a>
    <a href="#charts" class="block rounded-xl px-3 py-2">グラフ</a>
    <a href="#table" class="block rounded-xl px-3 py-2">比較表</a>
    <a href="#simulator" class="block rounded-xl px-3 py-2">将来シミュレーター</a>
  </div>

  <main class="max-w-7xl mx-auto px-4 pb-20" style="padding-top: calc(var(--header-h) + 22px);">
    <section id="overview" class="glass-card rounded-3xl p-6 md:p-8 fade-up">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 class="text-2xl md:text-4xl font-black">__TITLE__</h1>
          <p class="mt-2" style="color: var(--muted);">オルカン・S&P500・日経平均を、短期/中期/長期/超長期で比較します。</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button class="theme-btn active border px-4 py-2 rounded-full text-sm font-bold" id="themeA">Preset A</button>
          <button class="theme-btn border px-4 py-2 rounded-full text-sm font-bold" id="themeB">Preset B</button>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap gap-2" id="horizonButtons">
        <button class="h-btn active border px-4 py-2 rounded-full text-sm font-bold" data-horizon="short">短期（1年）</button>
        <button class="h-btn border px-4 py-2 rounded-full text-sm font-bold" data-horizon="mid">中期（3年）</button>
        <button class="h-btn border px-4 py-2 rounded-full text-sm font-bold" data-horizon="long">長期（5年）</button>
        <button class="h-btn border px-4 py-2 rounded-full text-sm font-bold" data-horizon="ultra_long">超長期（10年）</button>
      </div>
    </section>

    <section id="charts" class="mt-5 grid grid-cols-1 lg:grid-cols-12 gap-4">
      <article class="glass-card rounded-2xl p-5 lg:col-span-4 fade-up">
        <div class="text-xs font-bold tracking-wide" style="color: var(--muted);">トップ銘柄</div>
        <div id="bestTicker" class="text-3xl font-black mt-2">-</div>
        <div id="bestTickerCaption" class="text-sm mt-1" style="color: var(--muted);">-</div>
      </article>
      <article class="glass-card rounded-2xl p-5 lg:col-span-4 fade-up">
        <div class="text-xs font-bold tracking-wide" style="color: var(--muted);">平均 CAGR</div>
        <div id="avgCagr" class="text-3xl font-black mt-2">-</div>
        <div class="text-sm mt-1" style="color: var(--muted);">選択期間の平均年率</div>
      </article>
      <article class="glass-card rounded-2xl p-5 lg:col-span-4 fade-up">
        <div class="text-xs font-bold tracking-wide" style="color: var(--muted);">平均 最大DD</div>
        <div id="avgDrawdown" class="text-3xl font-black mt-2">-</div>
        <div class="text-sm mt-1" style="color: var(--muted);">ドローダウン絶対値</div>
      </article>

      <article class="glass-card rounded-2xl p-4 lg:col-span-6 fade-up">
        <h3 class="font-extrabold mb-2">含み益率ランキング</h3>
        <div id="barChart" class="h-80"></div>
      </article>
      <article class="glass-card rounded-2xl p-4 lg:col-span-6 fade-up">
        <h3 class="font-extrabold mb-2">リスク・リターン</h3>
        <div id="scatterChart" class="h-80"></div>
      </article>
      <article class="glass-card rounded-2xl p-4 lg:col-span-12 fade-up">
        <h3 class="font-extrabold mb-2">累積リターン推移</h3>
        <div id="lineChart" class="h-96"></div>
      </article>
    </section>

    <section id="table" class="mt-5 fade-up">
      <article class="glass-card rounded-2xl p-5 overflow-hidden">
        <h3 class="font-extrabold mb-3">期間別サマリー</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left border-b" style="border-color: color-mix(in srgb, var(--muted) 30%, transparent); color: var(--muted);">
                <th class="py-2 pr-4">銘柄</th>
                <th class="py-2 pr-4">期間</th>
                <th class="py-2 pr-4">開始日</th>
                <th class="py-2 pr-4">終了日</th>
                <th class="py-2 pr-4">リターン(%)</th>
                <th class="py-2 pr-4">含み益</th>
                <th class="py-2 pr-4">CAGR(%)</th>
                <th class="py-2 pr-4">最大DD(%)</th>
              </tr>
            </thead>
            <tbody id="summaryBody"></tbody>
          </table>
        </div>
      </article>
    </section>

    <section id="simulator" class="mt-5 fade-up">
      <article class="glass-card rounded-2xl p-6">
        <h3 class="font-extrabold text-xl">将来積立シミュレーター</h3>
        <p class="mt-1 text-sm" style="color: var(--muted);">毎月10万円積立を初期値に、1/3/5/10年後の評価額を推計します（過去CAGRベース）。</p>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <label class="block">
            <span class="text-xs font-bold" style="color: var(--muted);">投資先</span>
            <select id="simTicker" class="mt-1 w-full rounded-xl border bg-transparent px-3 py-2"></select>
          </label>
          <label class="block">
            <span class="text-xs font-bold" style="color: var(--muted);">毎月積立額（円）</span>
            <input id="monthlyInput" type="number" min="0" step="1000" value="__MONTHLY__" class="mt-1 w-full rounded-xl border bg-transparent px-3 py-2" />
          </label>
          <div class="flex items-end">
            <button id="runSim" class="w-full rounded-xl px-4 py-2 font-bold text-white" style="background: linear-gradient(135deg, var(--accent), var(--accent-2));">計算する</button>
          </div>
        </div>

        <div id="simCards" class="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3"></div>
      </article>
    </section>
  </main>

  <script>
    const summaryData = __SUMMARY_JSON__;
    const cumulativeData = __CUMULATIVE_JSON__;
    const tickerLabels = __TICKER_LABELS__;

    const horizonYears = { short: 1, mid: 3, long: 5, ultra_long: 10 };
    const horizonLabels = { short: "短期", mid: "中期", long: "長期", ultra_long: "超長期" };
    const simYears = [1, 3, 5, 10];

    const state = {
      horizon: "short",
      theme: localStorage.getItem("theme") || "preset-a",
    };

    const yen = (v) => new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY", maximumFractionDigits: 0 }).format(v);
    const pct = (v) => `${Number(v).toFixed(2)}%`;
    const fmt = (v) => new Intl.NumberFormat("ja-JP").format(Math.round(v));
    const labelOf = (ticker) => tickerLabels[ticker] || ticker;

    function setTheme(theme) {
      state.theme = theme;
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem("theme", theme);
      document.getElementById("themeA").classList.toggle("active", theme === "preset-a");
      document.getElementById("themeB").classList.toggle("active", theme === "preset-b");
      renderAll();
    }

    function getRows() {
      return summaryData.filter((r) => r.horizon === state.horizon);
    }

    function getSeriesForCurrentHorizon() {
      const years = horizonYears[state.horizon];
      if (!cumulativeData.length) return [];
      const latest = new Date(cumulativeData[cumulativeData.length - 1].date);
      const cutoff = new Date(latest);
      cutoff.setFullYear(cutoff.getFullYear() - years);
      return cumulativeData.filter((d) => new Date(d.date) >= cutoff);
    }

    function renderKpi(rows) {
      const sorted = [...rows].sort((a, b) => b.total_return_pct - a.total_return_pct);
      const best = sorted[0];
      const avgCagr = rows.reduce((acc, r) => acc + Number(r.cagr_pct), 0) / Math.max(rows.length, 1);
      const avgDd = rows.reduce((acc, r) => acc + Math.abs(Number(r.max_drawdown_pct)), 0) / Math.max(rows.length, 1);

      document.getElementById("bestTicker").textContent = best ? labelOf(best.ticker) : "-";
      document.getElementById("bestTickerCaption").textContent = best ? `${horizonLabels[state.horizon]}で ${pct(best.total_return_pct)}` : "-";
      document.getElementById("avgCagr").textContent = pct(avgCagr);
      document.getElementById("avgDrawdown").textContent = pct(avgDd);
    }

    function renderTable(rows) {
      const body = document.getElementById("summaryBody");
      body.innerHTML = rows
        .sort((a, b) => b.total_return_pct - a.total_return_pct)
        .map((r) => `
          <tr class="border-b" style="border-color: color-mix(in srgb, var(--muted) 20%, transparent);">
            <td class="py-2 pr-4 font-semibold">${labelOf(r.ticker)}</td>
            <td class="py-2 pr-4">${horizonLabels[r.horizon]}</td>
            <td class="py-2 pr-4">${r.start_date}</td>
            <td class="py-2 pr-4">${r.end_date}</td>
            <td class="py-2 pr-4">${pct(r.total_return_pct)}</td>
            <td class="py-2 pr-4">${yen(r.unrealized_pnl)}</td>
            <td class="py-2 pr-4">${pct(r.cagr_pct)}</td>
            <td class="py-2 pr-4">${pct(Math.abs(r.max_drawdown_pct))}</td>
          </tr>
        `)
        .join("");
    }

    function chartLayout() {
      const dark = state.theme === "preset-b";
      return {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        margin: { l: 45, r: 20, t: 28, b: 42 },
        font: { color: dark ? "#e2e8f0" : "#1e293b" },
      };
    }

    function renderBar(rows) {
      const sorted = [...rows].sort((a, b) => b.total_return_pct - a.total_return_pct);
      Plotly.react("barChart", [{
        type: "bar",
        x: sorted.map((r) => labelOf(r.ticker)),
        y: sorted.map((r) => Number(r.total_return_pct)),
        marker: { color: sorted.map((_, i) => i % 2 === 0 ? "#0ea5e9" : "#10b981") },
        hovertemplate: "%{x}<br>含み益率: %{y:.2f}%<extra></extra>",
      }], chartLayout(), { displayModeBar: false, responsive: true });
    }

    function renderScatter(rows) {
      Plotly.react("scatterChart", [{
        type: "scatter",
        mode: "markers+text",
        x: rows.map((r) => Math.abs(Number(r.max_drawdown_pct))),
        y: rows.map((r) => Number(r.cagr_pct)),
        text: rows.map((r) => labelOf(r.ticker)),
        textposition: "top center",
        marker: {
          size: rows.map((r) => Math.max(14, Math.min(44, Math.abs(Number(r.unrealized_pnl)) / 3000))),
          color: rows.map((r) => Number(r.total_return_pct)),
          colorscale: "Viridis",
          showscale: true,
          opacity: 0.9,
        },
        hovertemplate: "最大DD: %{x:.2f}%<br>CAGR: %{y:.2f}%<extra></extra>",
      }], {
        ...chartLayout(),
        xaxis: { title: "最大DD(%)", zeroline: false },
        yaxis: { title: "CAGR(%)", zeroline: false },
      }, { displayModeBar: false, responsive: true });
    }

    function renderLine() {
      const sliced = getSeriesForCurrentHorizon();
      if (!sliced.length) return;

      const cols = Object.keys(sliced[0]).filter((k) => k !== "date");
      const traces = cols.map((ticker) => ({
        type: "scatter",
        mode: "lines",
        name: labelOf(ticker),
        x: sliced.map((d) => d.date),
        y: sliced.map((d) => Number(d[ticker]) * 100),
        line: { width: 2.5 },
        hovertemplate: `${labelOf(ticker)}<br>%{x}<br>累積: %{y:.2f}%<extra></extra>`,
      }));

      Plotly.react("lineChart", traces, {
        ...chartLayout(),
        xaxis: { title: "日付" },
        yaxis: { title: "累積リターン(%)" },
        legend: { orientation: "h" },
      }, { displayModeBar: false, responsive: true });
    }

    function getCagrByTicker(ticker) {
      const rows = summaryData.filter((r) => r.ticker === ticker);
      const map = new Map(rows.map((r) => [r.horizon, Number(r.cagr_pct) / 100]));
      const fallback = map.get("long") ?? map.get("mid") ?? map.get("short") ?? 0;
      return {
        1: map.get("short") ?? fallback,
        3: map.get("mid") ?? fallback,
        5: map.get("long") ?? fallback,
        10: map.get("ultra_long") ?? fallback,
      };
    }

    function futureValueMonthly(monthly, years, annualRate) {
      const n = years * 12;
      const r = Math.pow(1 + annualRate, 1 / 12) - 1;
      if (Math.abs(r) < 1e-9) return monthly * n;
      return monthly * ((Math.pow(1 + r, n) - 1) / r);
    }

    function renderSimulator() {
      const select = document.getElementById("simTicker");
      const monthlyInput = document.getElementById("monthlyInput");
      const targetTicker = select.value;
      const monthly = Math.max(0, Number(monthlyInput.value || 0));
      const rates = getCagrByTicker(targetTicker);

      const cards = simYears.map((y) => {
        const fv = futureValueMonthly(monthly, y, rates[y]);
        const principal = monthly * y * 12;
        const profit = fv - principal;
        return `
          <div class="rounded-2xl p-4 border" style="border-color: color-mix(in srgb, var(--muted) 24%, transparent); background: color-mix(in srgb, var(--card) 80%, transparent);">
            <div class="text-xs font-bold" style="color: var(--muted);">${y}年後（${labelOf(targetTicker)}）</div>
            <div class="text-xl font-black mt-1">${yen(fv)}</div>
            <div class="text-xs mt-1" style="color: var(--muted);">元本 ${yen(principal)}</div>
            <div class="text-sm mt-1 font-bold" style="color: ${profit >= 0 ? '#22c55e' : '#ef4444'};">含み益見込み ${yen(profit)}</div>
            <div class="text-xs mt-1" style="color: var(--muted);">想定CAGR: ${pct(rates[y] * 100)}</div>
          </div>
        `;
      }).join("");

      document.getElementById("simCards").innerHTML = cards;
    }

    function renderAll() {
      const rows = getRows();
      renderKpi(rows);
      renderTable(rows);
      renderBar(rows);
      renderScatter(rows);
      renderLine();
      renderSimulator();
    }

    function initSelects() {
      const tickers = [...new Set(summaryData.map((r) => r.ticker))];
      const select = document.getElementById("simTicker");
      select.innerHTML = tickers.map((t) => `<option value="${t}">${labelOf(t)}</option>`).join("");
    }

    function initHorizonButtons() {
      document.querySelectorAll("#horizonButtons .h-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.horizon = btn.dataset.horizon;
          document.querySelectorAll("#horizonButtons .h-btn").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          renderAll();
        });
      });
    }

    function initTheme() {
      document.getElementById("themeA").addEventListener("click", () => setTheme("preset-a"));
      document.getElementById("themeB").addEventListener("click", () => setTheme("preset-b"));
      setTheme(state.theme);
    }

    function initSmoothScroll() {
      function smoothScrollTo(targetY, duration = 400) {
        const startY = window.pageYOffset;
        const distance = targetY - startY;
        const start = performance.now();

        function step(now) {
          const t = Math.min(1, (now - start) / duration);
          const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
          window.scrollTo(0, startY + distance * eased);
          if (t < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      }

      document.querySelectorAll('a[href^="#"]').forEach((a) => {
        a.addEventListener("click", (e) => {
          const target = document.querySelector(a.getAttribute("href"));
          if (!target) return;
          e.preventDefault();
          const y = target.getBoundingClientRect().top + window.pageYOffset - 72;
          smoothScrollTo(y, 400);
        });
      });
    }

    function initMobileMenu() {
      const button = document.getElementById("hamburger");
      const panel = document.getElementById("mobilePanel");
      button.addEventListener("click", () => {
        button.classList.toggle("active");
        panel.classList.toggle("open");
      });

      panel.querySelectorAll("a").forEach((a) => {
        a.addEventListener("click", () => {
          panel.classList.remove("open");
          button.classList.remove("active");
        });
      });
    }

    function initSimulatorControls() {
      document.getElementById("runSim").addEventListener("click", renderSimulator);
      document.getElementById("simTicker").addEventListener("change", renderSimulator);
      document.getElementById("monthlyInput").addEventListener("input", renderSimulator);
    }

    function initReveal() {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("in");
        });
      }, { threshold: 0.12 });
      document.querySelectorAll(".fade-up").forEach((el) => observer.observe(el));
    }

    initSelects();
    initHorizonButtons();
    initTheme();
    initSmoothScroll();
    initMobileMenu();
    initSimulatorControls();
    initReveal();
    renderAll();
  </script>
</body>
</html>
"""

    html = (
        template.replace("__TITLE__", title)
        .replace("__SUMMARY_JSON__", summary_json)
        .replace("__CUMULATIVE_JSON__", cumulative_json)
        .replace("__TICKER_LABELS__", labels_json)
        .replace("__MONTHLY__", str(int(monthly_contribution)))
    )
    output_path.write_text(html, encoding="utf-8")

def write_tsumitate_simulation_html(
    output_path: Path,
    presets: list[dict[str, object]],
    monthly_contribution: float = 100_000,
    hero_image: str = "image.png",
    hero_image2: str = "image2.png",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    presets_json = json.dumps(presets, ensure_ascii=False)

    template = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>積立投資シミュレーション</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Noto Sans JP"', '"Segoe UI"', 'sans-serif']
          }
        }
      }
    };
  </script>
  <style>
    :root {
      --bg: #ffffff;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #64748b;
      --accent: #0284c7;
      --accent-2: #22c55e;
      --accent-3: #f43f5e;
    }

    body {
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }


    .glass {
      background: var(--panel);
      border: 1px solid var(--border);
      box-shadow: 0 16px 40px rgba(15, 23, 42, .08);
      transition: transform .28s ease, box-shadow .28s ease;
    }

    .glass:hover {
      transform: translateY(-2px);
      box-shadow: 0 22px 50px rgba(15, 23, 42, .12);
    }

    .control {
      width: 100%;
      border: 1px solid #cbd5e1;
      border-radius: .85rem;
      padding: .58rem .75rem;
      font-size: 16px;
      background: #fff;
      color: #0f172a;
    }

    .control:focus {
      outline: none;
      border-color: rgba(2,132,199,.9);
      box-shadow: 0 0 0 3px rgba(2,132,199,.16);
    }

    .mode-chip {
      border: 1px solid #d1d5db;
      border-radius: 999px;
      padding: .42rem .76rem;
      font-size: .8rem;
      font-weight: 700;
      color: #334155;
      background: #fff;
      transition: all .2s ease;
      cursor: pointer;
    }

    .mode-chip.active {
      color: #fff;
      border-color: transparent;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      box-shadow: 0 10px 24px rgba(2,132,199,.24);
    }

    .range {
      accent-color: var(--accent);
      width: 100%;
      cursor: pointer;
    }

    .hero-image-wrap {
      position: fixed;
      top: 16px;
      right: 16px;
      z-index: 50;
      width: min(24vw, 240px);
      cursor: pointer;
      animation: floaty 3.2s ease-in-out infinite;
      transition: transform .22s ease;
    }

    .hero-image-wrap:hover { transform: scale(1.02); }

    .hero-image-wrap img {
      width: 100%;
      height: auto;
      display: block;
      border: none;
      outline: none;
      box-shadow: none;
      background: transparent;
    }

    @keyframes floaty {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-7px); }
    }

    .scene-transition {
      position: fixed;
      inset: 0;
      z-index: 999;
      background: #fff;
      display: grid;
      place-items: center;
      opacity: 0;
      pointer-events: none;
      transition: opacity .5s ease;
    }

    .scene-transition.active {
      opacity: 1;
      pointer-events: auto;
    }

    .scene-transition img {
      width: min(88vw, 760px);
      height: auto;
      opacity: 0;
      transform: scale(.98);
      transition: opacity .5s ease, transform .5s ease;
    }

    .scene-transition.active img {
      opacity: 1;
      transform: scale(1);
    }

    .app-shell {
      transition: opacity .5s ease, transform .5s ease;
      opacity: 1;
      transform: scale(1);
      position: relative;
      z-index: 1;
    }

    .app-shell.leaving {
      opacity: .15;
      transform: scale(.985);
    }

    @media (max-width: 980px) {
      .hero-image-wrap { width: 150px; top: 10px; right: 10px; }
    }

    @media (max-width: 900px) {
      .hero-image-wrap { display: none; }
    }
  </style>
</head>
<body class="font-sans">
  <button id="heroImageWrap" class="hero-image-wrap" aria-label="image transition">
    <img id="heroImage" src="__HERO_IMAGE__" alt="hero" />
  </button>

  <div id="sceneTransition" class="scene-transition">
    <img id="heroImage2" src="__HERO_IMAGE2__" alt="hero scene" />
  </div>

  <main id="appShell" class="app-shell max-w-7xl mx-auto px-3 sm:px-4 py-5 sm:py-7 md:py-9">
    <header class="mb-5">
      <h1 class="text-2xl md:text-4xl font-black tracking-tight">積立投資シミュレーション</h1>
      <p class="mt-2 text-slate-500">条件を変えると自動で計算が反映</p>
    </header>

    <section class="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <article class="glass rounded-2xl p-5 lg:col-span-4">
        <h2 class="text-lg font-black">入力条件</h2>

        <label class="block mt-4">
          <span class="text-xs font-bold text-slate-500">投資対象プリセット</span>
          <select id="presetSelect" class="control mt-1"></select>
        </label>

        <div class="mt-4">
          <div class="text-xs font-bold text-slate-500 mb-2">計算モード</div>
          <div class="flex flex-wrap gap-2" id="modeChips">
            <button class="mode-chip active" data-mode="future_value">将来いくら</button>
            <button class="mode-chip" data-mode="required_monthly">必要な積立額</button>
            <button class="mode-chip" data-mode="years_to_goal">何年で到達</button>
            <button class="mode-chip" data-mode="required_initial">必要な初期額</button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-3 mt-4">
          <label class="block">
            <span class="text-xs font-bold text-slate-500">初期投資額（円）</span>
            <input id="initial" class="control mt-1" type="number" min="0" step="10000" value="0" />
          </label>
          <label class="block">
            <span class="text-xs font-bold text-slate-500">毎月積立額（円）</span>
            <input id="monthly" class="control mt-1" type="number" min="0" step="1000" value="__MONTHLY__" />
          </label>
          <label class="block">
            <span class="text-xs font-bold text-slate-500">運用年数（年）</span>
            <input id="years" class="control mt-1" type="number" min="1" max="60" value="10" />
          </label>
          <label class="block">
            <span class="text-xs font-bold text-slate-500">目標金額（円）</span>
            <input id="goal" class="control mt-1" type="number" min="0" step="100000" value="20000000" />
          </label>

          <label class="block">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500">想定リターン（年率%）</span>
              <span id="annualReturnValue" class="text-xs text-sky-600 font-bold">6.00%</span>
            </div>
            <input id="annualReturn" class="control mt-1" type="number" step="0.1" value="6.0" />
            <input id="annualReturnRange" class="range mt-2" type="range" min="-10" max="30" step="0.1" value="6.0" />
          </label>

          <label class="block">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500">リスク（年率標準偏差%）</span>
              <span id="annualVolValue" class="text-xs text-emerald-600 font-bold">18.00%</span>
            </div>
            <input id="annualVol" class="control mt-1" type="number" step="0.1" min="0" value="18.0" />
            <input id="annualVolRange" class="range mt-2" type="range" min="0" max="80" step="0.1" value="18.0" />
          </label>
        </div>
      </article>

      <article class="glass rounded-2xl p-5 lg:col-span-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <h2 class="text-lg font-black">シミュレーション結果</h2>
          <div class="text-xs text-slate-500">モンテカルロ: 1,500パス</div>
        </div>

        <div id="resultMain" class="mt-3 text-3xl md:text-4xl font-black">-</div>
        <div id="resultSub" class="text-sm text-slate-500 mt-1">-</div>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-4 gap-3">
          <div class="rounded-xl p-3 border border-slate-200 bg-slate-50">
            <div class="text-xs font-bold text-slate-500">元本合計</div>
            <div id="principalOut" class="mt-1 text-lg font-black">-</div>
          </div>
          <div class="rounded-xl p-3 border border-slate-200 bg-slate-50">
            <div class="text-xs font-bold text-slate-500">評価額（中央値）</div>
            <div id="medianOut" class="mt-1 text-lg font-black">-</div>
          </div>
          <div class="rounded-xl p-3 border border-slate-200 bg-slate-50">
            <div class="text-xs font-bold text-slate-500">利益（中央値）</div>
            <div id="profitOut" class="mt-1 text-lg font-black">-</div>
          </div>
          <div class="rounded-xl p-3 border border-slate-200 bg-slate-50">
            <div class="text-xs font-bold text-slate-500">目標達成確率</div>
            <div id="goalProbOut" class="mt-1 text-lg font-black">-</div>
          </div>
        </div>

        <div class="mt-4">
          <div id="chart" class="h-[320px] md:h-96"></div>
        </div>

        <p class="mt-4 text-xs text-slate-500 leading-relaxed">
          試算は簡易モデルです。将来の運用成果を保証するものではありません。税金・手数料・為替・投資タイミング差などは簡略化しています。
        </p>
      </article>
    </section>
  </main>

  <script>
    const presets = __PRESETS_JSON__;
    let stateMode = "future_value";

    const fmtYen = (v) => new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY", maximumFractionDigits: 0 }).format(v);
    const pct = (v) => `${Number(v).toFixed(2)}%`;

    function futureValue(initial, monthly, years, annualReturn) {
      const n = Math.max(1, Math.round(years * 12));
      const r = Math.pow(1 + annualReturn, 1 / 12) - 1;
      if (Math.abs(r) < 1e-12) return initial + monthly * n;
      return initial * Math.pow(1 + r, n) + monthly * ((Math.pow(1 + r, n) - 1) / r);
    }

    function requiredMonthly(target, initial, years, annualReturn) {
      const n = Math.max(1, Math.round(years * 12));
      const r = Math.pow(1 + annualReturn, 1 / 12) - 1;
      if (Math.abs(r) < 1e-12) return Math.max(0, (target - initial) / n);
      const futureInitial = initial * Math.pow(1 + r, n);
      return Math.max(0, (target - futureInitial) * r / (Math.pow(1 + r, n) - 1));
    }

    function requiredInitial(target, monthly, years, annualReturn) {
      const n = Math.max(1, Math.round(years * 12));
      const r = Math.pow(1 + annualReturn, 1 / 12) - 1;
      if (Math.abs(r) < 1e-12) return Math.max(0, target - monthly * n);
      const fvMonthly = monthly * ((Math.pow(1 + r, n) - 1) / r);
      return Math.max(0, (target - fvMonthly) / Math.pow(1 + r, n));
    }

    function yearsToGoal(target, initial, monthly, annualReturn, maxYears = 60) {
      for (let y = 1; y <= maxYears; y += 1) {
        if (futureValue(initial, monthly, y, annualReturn) >= target) return y;
      }
      return null;
    }

    function randnBM() {
      let u = 0, v = 0;
      while (u === 0) u = Math.random();
      while (v === 0) v = Math.random();
      return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    }

    function monteCarloPaths(initial, monthly, years, annualReturn, annualVol, paths = 1500) {
      const months = Math.max(1, Math.round(years * 12));
      const m = annualReturn / 12;
      const s = annualVol / Math.sqrt(12);
      const snapshots = [];

      for (let p = 0; p < paths; p += 1) {
        let value = initial;
        const series = [value];
        for (let t = 1; t <= months; t += 1) {
          const shock = randnBM();
          const rt = m + s * shock;
          value = value * (1 + rt) + monthly;
          if (value < 0) value = 0;
          series.push(value);
        }
        snapshots.push(series);
      }

      return { snapshots, months };
    }

    function percentile(arr, p) {
      const sorted = [...arr].sort((a, b) => a - b);
      const idx = Math.min(sorted.length - 1, Math.max(0, Math.floor((sorted.length - 1) * p)));
      return sorted[idx];
    }

    function drawChart(initial, monthly, years, annualReturn, annualVol, goal) {
      const { snapshots, months } = monteCarloPaths(initial, monthly, years, annualReturn, annualVol);
      const x = Array.from({ length: months + 1 }, (_, i) => i / 12);
      const p10 = [], p50 = [], p90 = [];

      for (let i = 0; i <= months; i += 1) {
        const vals = snapshots.map((s) => s[i]);
        p10.push(percentile(vals, 0.10));
        p50.push(percentile(vals, 0.50));
        p90.push(percentile(vals, 0.90));
      }

      const deterministic = x.map((t) => futureValue(initial, monthly, t, annualReturn));
      const finals = snapshots.map((s) => s[s.length - 1]);
      const goalProb = finals.filter((v) => v >= goal).length / finals.length;

      Plotly.react("chart", [
        { x, y: p90, mode: "lines", name: "上位10%", line: { color: "#22c55e", width: 2.3 } },
        { x, y: p50, mode: "lines", name: "中央値", line: { color: "#0284c7", width: 3.2 } },
        { x, y: p10, mode: "lines", name: "下位10%", line: { color: "#f43f5e", width: 2.3 } },
        { x, y: deterministic, mode: "lines", name: "期待値ベース", line: { color: "#64748b", dash: "dot", width: 2 } },
        { x, y: x.map(() => goal), mode: "lines", name: "目標金額", line: { color: "#eab308", dash: "dash", width: 1.8 } },
      ], {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        margin: { l: 54, r: 20, t: 22, b: 42 },
        font: { color: "#334155" },
        xaxis: { title: "経過年数", gridcolor: "rgba(148,163,184,.35)" },
        yaxis: { title: "評価額（円）", tickformat: ",.0f", gridcolor: "rgba(148,163,184,.35)" },
        legend: { orientation: "h" },
      }, { displayModeBar: false, responsive: true });

      return { median: p50[p50.length - 1], goalProb };
    }

    function syncRanges() {
      const rInput = document.getElementById("annualReturn");
      const rRange = document.getElementById("annualReturnRange");
      const vInput = document.getElementById("annualVol");
      const vRange = document.getElementById("annualVolRange");

      rRange.value = rInput.value;
      vRange.value = vInput.value;
      document.getElementById("annualReturnValue").textContent = `${Number(rInput.value).toFixed(2)}%`;
      document.getElementById("annualVolValue").textContent = `${Number(vInput.value).toFixed(2)}%`;
    }

    function calc() {
      const initial = Math.max(0, Number(document.getElementById("initial").value || 0));
      const monthly = Math.max(0, Number(document.getElementById("monthly").value || 0));
      const years = Math.max(1, Number(document.getElementById("years").value || 1));
      const goal = Math.max(0, Number(document.getElementById("goal").value || 0));
      const annualReturn = Number(document.getElementById("annualReturn").value || 0) / 100;
      const annualVol = Math.max(0, Number(document.getElementById("annualVol").value || 0)) / 100;

      let mainText = "-";
      let subText = "-";
      let simYears = years;

      if (stateMode === "future_value") {
        const value = futureValue(initial, monthly, years, annualReturn);
        mainText = fmtYen(value);
        subText = `${years}年後の想定評価額（期待値ベース）`;
      } else if (stateMode === "required_monthly") {
        const req = requiredMonthly(goal, initial, years, annualReturn);
        mainText = fmtYen(req);
        subText = `${fmtYen(goal)}を${years}年で目指すための毎月積立額`;
      } else if (stateMode === "years_to_goal") {
        const needYears = yearsToGoal(goal, initial, monthly, annualReturn);
        mainText = needYears ? `${needYears}年` : "60年以上";
        subText = `${fmtYen(goal)}到達までの目安年数`;
        simYears = needYears || 60;
      } else {
        const reqInit = requiredInitial(goal, monthly, years, annualReturn);
        mainText = fmtYen(reqInit);
        subText = `${fmtYen(goal)}を${years}年で目指すための初期投資額`;
      }

      const principal = initial + monthly * Math.round(simYears * 12);
      const mc = drawChart(initial, monthly, simYears, annualReturn, annualVol, goal);
      const median = mc.median;

      document.getElementById("resultMain").textContent = mainText;
      document.getElementById("resultSub").textContent = subText;
      document.getElementById("principalOut").textContent = fmtYen(principal);
      document.getElementById("medianOut").textContent = fmtYen(median);
      document.getElementById("profitOut").textContent = fmtYen(median - principal);
      document.getElementById("goalProbOut").textContent = pct(mc.goalProb * 100);

      syncRanges();
    }

    function initPresets() {
      const select = document.getElementById("presetSelect");
      if (!presets.length) {
        select.innerHTML = '<option value="none">標準</option>';
        return;
      }

      select.innerHTML = presets
        .map((p, idx) => `<option value="${idx}">${p.label}（年率 ${pct(Number(p.annual_return) * 100)} / リスク ${pct(Number(p.annual_vol) * 100)}）</option>`)
        .join("");

      const apply = (idx) => {
        const p = presets[idx];
        if (!p) return;
        document.getElementById("annualReturn").value = (Number(p.annual_return) * 100).toFixed(2);
        document.getElementById("annualVol").value = (Number(p.annual_vol) * 100).toFixed(2);
      };

      apply(0);
      select.addEventListener("change", () => {
        apply(Number(select.value));
        calc();
      });
    }

    function initModeChips() {
      document.querySelectorAll("#modeChips .mode-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
          stateMode = chip.dataset.mode;
          document.querySelectorAll("#modeChips .mode-chip").forEach((c) => c.classList.remove("active"));
          chip.classList.add("active");
          calc();
        });
      });
    }

    function initAutoBindings() {
      const pairs = [["annualReturn", "annualReturnRange"], ["annualVol", "annualVolRange"]];

      pairs.forEach(([inputId, rangeId]) => {
        const input = document.getElementById(inputId);
        const range = document.getElementById(rangeId);

        input.addEventListener("input", () => {
          range.value = input.value;
          calc();
        });

        range.addEventListener("input", () => {
          input.value = range.value;
          calc();
        });
      });

      ["initial", "monthly", "years", "goal"].forEach((id) => {
        document.getElementById(id).addEventListener("input", calc);
      });
    }

    function initHeroTransition() {
      const hero = document.getElementById("heroImageWrap");
      const image = document.getElementById("heroImage");
      const image2 = document.getElementById("heroImage2");
      const scene = document.getElementById("sceneTransition");
      const app = document.getElementById("appShell");

      let triggered = false;

      image.addEventListener("error", () => { hero.style.display = "none"; });
      image2.addEventListener("error", () => { scene.style.display = "none"; });

      hero.addEventListener("click", () => {
        if (triggered) return;
        triggered = true;

        app.classList.add("leaving");
        scene.classList.add("active");

        setTimeout(() => {
          setTimeout(() => {
            const tryClose = () => {
              window.open("", "_self");
              window.close();
              setTimeout(() => {
                if (!window.closed) {
                  location.href = "about:blank";
                }
              }, 250);
            };
            tryClose();
          }, 3000);
        }, 500);
      });
    }

    initPresets();
    initModeChips();
    initAutoBindings();
    initHeroTransition();
    calc();
  </script>
</body>
</html>
"""

    html = (
        template.replace("__PRESETS_JSON__", presets_json)
        .replace("__MONTHLY__", str(int(monthly_contribution)))
        .replace("__HERO_IMAGE__", hero_image)
        .replace("__HERO_IMAGE2__", hero_image2)
    )
    output_path.write_text(html, encoding="utf-8")





