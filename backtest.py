#!/usr/bin/env python3
"""
Portfolio Backtesting Engine
=============================
Backtests a portfolio of stocks over historical data and compares
against S&P 500 (SPY). Supports CLI usage and module import.

Dependencies:
    pip install yfinance tabulate numpy

Usage:
    python backtest.py --tickers TEAM,INTU,DOCU --weights 0.4,0.3,0.3 --period 2y
    python backtest.py --tickers TEAM,INTU,DOCU --period 6m
    python backtest.py --tickers ANET,FCX,XOM --start 2024-01-01 --end 2026-02-20

Import:
    from backtest import backtest
    results = backtest(["TEAM", "INTU", "DOCU"], weights=[0.4, 0.3, 0.3], period="2y")
"""

import argparse
import datetime
import math
import sys
import warnings

import numpy as np
import yfinance as yf
from tabulate import tabulate

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"

BENCHMARK = "SPY"
RISK_FREE_RATE = 0.045  # ~4.5% annualized (current T-bill)
TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_prices(tickers, period=None, start=None, end=None):
    """Download adjusted close prices for tickers + benchmark.
    Returns a DataFrame with tickers as columns and dates as index."""
    all_tickers = list(tickers) + [BENCHMARK]

    kwargs = {"progress": False, "threads": True, "auto_adjust": True}
    if start and end:
        kwargs["start"] = start
        kwargs["end"] = end
    else:
        kwargs["period"] = period or "2y"

    raw = yf.download(all_tickers, **kwargs)

    # Extract Close prices
    if isinstance(raw.columns, __import__("pandas").MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]].copy()
        prices.columns = all_tickers

    prices = prices.dropna(how="all").ffill()
    return prices


# ---------------------------------------------------------------------------
# Portfolio simulation
# ---------------------------------------------------------------------------

def simulate_portfolio(prices, tickers, weights):
    """Compute daily portfolio and benchmark returns.
    Returns dict with portfolio_returns, benchmark_returns, cumulative series."""
    # Daily returns for each ticker
    returns = prices[tickers].pct_change().dropna()
    bench_returns = prices[BENCHMARK].pct_change().dropna()

    # Align dates
    common = returns.index.intersection(bench_returns.index)
    returns = returns.loc[common]
    bench_returns = bench_returns.loc[common]

    # Weighted portfolio return
    w = np.array(weights)
    portfolio_daily = (returns * w).sum(axis=1)

    # Cumulative returns (growth of $1)
    portfolio_cum = (1 + portfolio_daily).cumprod()
    benchmark_cum = (1 + bench_returns).cumprod()

    # Per-ticker cumulative
    ticker_cum = (1 + returns).cumprod()

    return {
        "portfolio_daily": portfolio_daily,
        "benchmark_daily": bench_returns,
        "portfolio_cum": portfolio_cum,
        "benchmark_cum": benchmark_cum,
        "ticker_cum": ticker_cum,
        "ticker_daily": returns,
        "dates": common,
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(sim):
    """Compute all performance metrics from simulation results."""
    p = sim["portfolio_daily"]
    b = sim["benchmark_daily"]
    n_days = len(p)
    n_years = n_days / TRADING_DAYS

    # Total return
    total_return = float(sim["portfolio_cum"].iloc[-1]) - 1
    bench_total = float(sim["benchmark_cum"].iloc[-1]) - 1

    # Annualized return
    ann_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
    bench_ann = (1 + bench_total) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Volatility (annualized)
    volatility = float(p.std()) * math.sqrt(TRADING_DAYS)
    bench_vol = float(b.std()) * math.sqrt(TRADING_DAYS)

    # Sharpe ratio
    sharpe = (ann_return - RISK_FREE_RATE) / volatility if volatility > 0 else 0

    # Sortino ratio (downside deviation)
    downside = p[p < 0]
    downside_std = float(downside.std()) * math.sqrt(TRADING_DAYS) if len(downside) > 0 else 0
    sortino = (ann_return - RISK_FREE_RATE) / downside_std if downside_std > 0 else 0

    # Max drawdown
    cum = sim["portfolio_cum"]
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    max_dd = float(drawdown.min())
    dd_end_idx = drawdown.idxmin()
    dd_start_idx = cum.loc[:dd_end_idx].idxmax()

    bench_cum = sim["benchmark_cum"]
    bench_running_max = bench_cum.cummax()
    bench_dd = (bench_cum - bench_running_max) / bench_running_max
    bench_max_dd = float(bench_dd.min())

    # Monthly returns for win rate
    monthly = p.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    win_rate = float((monthly > 0).sum()) / len(monthly) if len(monthly) > 0 else 0

    # Beta
    cov = np.cov(p.values, b.values)
    beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0

    # Alpha (Jensen's)
    alpha = ann_return - (RISK_FREE_RATE + beta * (bench_ann - RISK_FREE_RATE))

    # Best/worst day
    best_day = float(p.max())
    worst_day = float(p.min())
    best_day_date = p.idxmax()
    worst_day_date = p.idxmin()

    return {
        "total_return": total_return,
        "bench_total": bench_total,
        "ann_return": ann_return,
        "bench_ann": bench_ann,
        "volatility": volatility,
        "bench_vol": bench_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "bench_max_dd": bench_max_dd,
        "dd_start": dd_start_idx,
        "dd_end": dd_end_idx,
        "win_rate": win_rate,
        "beta": beta,
        "alpha": alpha,
        "best_day": best_day,
        "best_day_date": best_day_date,
        "worst_day": worst_day,
        "worst_day_date": worst_day_date,
        "n_days": n_days,
        "n_years": n_years,
        "drawdown_series": drawdown,
        "monthly_returns": monthly,
    }


def compute_monthly_table(sim):
    """Build a year x month returns table."""
    p = sim["portfolio_daily"]
    monthly = p.resample("ME").apply(lambda x: (1 + x).prod() - 1)

    rows = {}
    for date, ret in monthly.items():
        year = date.year
        month = date.month
        if year not in rows:
            rows[year] = [None] * 12
        rows[year][month - 1] = ret

    # Yearly total
    yearly = p.resample("YE").apply(lambda x: (1 + x).prod() - 1)
    for date, ret in yearly.items():
        year = date.year
        if year in rows:
            rows[year].append(ret)

    return rows


def compute_per_ticker_metrics(sim, tickers, weights):
    """Return per-ticker performance breakdown."""
    results = []
    for i, ticker in enumerate(tickers):
        daily = sim["ticker_daily"][ticker]
        total = float(sim["ticker_cum"][ticker].iloc[-1]) - 1
        vol = float(daily.std()) * math.sqrt(TRADING_DAYS)
        results.append({
            "ticker": ticker,
            "weight": weights[i],
            "total_return": total,
            "volatility": vol,
            "contribution": total * weights[i],
        })
    return results


# ---------------------------------------------------------------------------
# Formatting & display
# ---------------------------------------------------------------------------

def colour_pct(val, bold_threshold=None):
    if val is None:
        return f"{DIM}N/A{RESET}"
    s = f"{val:+.1%}"
    if val > 0:
        c = f"{GREEN}{BOLD}" if bold_threshold and val > bold_threshold else GREEN
    elif val < 0:
        c = f"{RED}{BOLD}" if bold_threshold and val < bold_threshold else RED
    else:
        c = WHITE
    return f"{c}{s}{RESET}"


def colour_ratio(val, good_threshold=1.0):
    s = f"{val:.2f}"
    if val >= good_threshold:
        return f"{GREEN}{s}{RESET}"
    elif val >= 0:
        return f"{YELLOW}{s}{RESET}"
    else:
        return f"{RED}{s}{RESET}"


def print_header(title):
    print()
    print(f"{BOLD}{CYAN}{'=' * 72}{RESET}")
    print(f"{BOLD}{CYAN}   {title}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 72}{RESET}")
    print()


def print_section(title):
    print(f"{BOLD}{MAGENTA}--- {title} ---{RESET}")
    print()


def print_scorecard(metrics):
    """Print the main performance scorecard."""
    print_section("PERFORMANCE SCORECARD")

    rows = [
        ["Total Return", colour_pct(metrics["total_return"], 0.1),
         colour_pct(metrics["bench_total"], 0.1), "Portfolio vs SPY cumulative"],
        ["Annualized Return", colour_pct(metrics["ann_return"]),
         colour_pct(metrics["bench_ann"]), "CAGR over backtest period"],
        ["Volatility (ann.)", f"{metrics['volatility']:.1%}",
         f"{metrics['bench_vol']:.1%}", "Lower = less risk"],
        ["Sharpe Ratio", colour_ratio(metrics["sharpe"]),
         "—", f">{GREEN}1.0{RESET} is good, >{GREEN}2.0{RESET} is great"],
        ["Sortino Ratio", colour_ratio(metrics["sortino"]),
         "—", "Like Sharpe but only penalizes downside"],
        ["Max Drawdown", colour_pct(metrics["max_drawdown"], -0.2),
         colour_pct(metrics["bench_max_dd"], -0.2), "Worst peak-to-trough"],
        ["Beta", f"{metrics['beta']:.2f}",
         "1.00", ">1 = more volatile than market"],
        ["Alpha (Jensen's)", colour_pct(metrics["alpha"]),
         "—", "Excess return vs beta-adjusted benchmark"],
        ["Win Rate (monthly)", f"{metrics['win_rate']:.0%}",
         "—", "% of months with positive returns"],
        ["Trading Days", f"{metrics['n_days']}",
         f"{metrics['n_days']}", f"~{metrics['n_years']:.1f} years"],
    ]

    print(tabulate(rows,
                   headers=["Metric", "Portfolio", "S&P 500", "Note"],
                   tablefmt="simple",
                   colalign=("left", "right", "right", "left")))
    print()

    # Best/worst days
    print(f"  {GREEN}Best day:  {metrics['best_day']:+.2%} "
          f"({metrics['best_day_date'].strftime('%Y-%m-%d')}){RESET}")
    print(f"  {RED}Worst day: {metrics['worst_day']:+.2%} "
          f"({metrics['worst_day_date'].strftime('%Y-%m-%d')}){RESET}")
    print()


def print_ticker_breakdown(ticker_metrics):
    """Print per-ticker performance table."""
    print_section("PER-TICKER BREAKDOWN")

    rows = []
    for t in sorted(ticker_metrics, key=lambda x: -x["total_return"]):
        rows.append([
            f"{BOLD}{t['ticker']}{RESET}",
            f"{t['weight']:.0%}",
            colour_pct(t["total_return"]),
            f"{t['volatility']:.1%}",
            colour_pct(t["contribution"]),
        ])

    print(tabulate(rows,
                   headers=["Ticker", "Weight", "Total Return", "Volatility", "Contribution"],
                   tablefmt="simple",
                   colalign=("left", "right", "right", "right", "right")))
    print()


def print_monthly_table(monthly_data):
    """Print year x month returns heatmap."""
    print_section("MONTHLY RETURNS")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "YEAR"]

    rows = []
    for year in sorted(monthly_data.keys()):
        row = [f"{BOLD}{year}{RESET}"]
        data = monthly_data[year]
        for val in data[:12]:
            if val is None:
                row.append(f"{DIM}—{RESET}")
            else:
                row.append(colour_pct(val))
        # Year total
        if len(data) > 12 and data[12] is not None:
            row.append(colour_pct(data[12], 0.1))
        else:
            # Calculate from monthly
            valid = [v for v in data[:12] if v is not None]
            if valid:
                yr_total = 1
                for v in valid:
                    yr_total *= (1 + v)
                yr_total -= 1
                row.append(colour_pct(yr_total, 0.1))
            else:
                row.append(f"{DIM}—{RESET}")
        rows.append(row)

    print(tabulate(rows, headers=["Year"] + months, tablefmt="simple",
                   colalign=tuple(["left"] + ["right"] * 13)))
    print()


def print_drawdown_chart(dd_series, width=68):
    """Print an ASCII drawdown chart."""
    print_section("DRAWDOWN CHART")

    if len(dd_series) == 0:
        print(f"  {DIM}No drawdown data{RESET}")
        return

    # Resample to weekly for readability
    weekly_dd = dd_series.resample("W").min()
    if len(weekly_dd) > width:
        # Sample evenly
        indices = np.linspace(0, len(weekly_dd) - 1, width, dtype=int)
        weekly_dd = weekly_dd.iloc[indices]

    max_dd = abs(float(weekly_dd.min()))
    if max_dd == 0:
        max_dd = 0.01  # avoid division by zero

    height = 10
    chart_rows = []

    for row in range(height):
        threshold = -max_dd * (1 - row / height)
        line = ""
        for val in weekly_dd.values:
            if val <= threshold:
                line += f"{RED}█{RESET}"
            else:
                line += " "
        chart_rows.append(line)

    # Print with y-axis labels
    for i, row_str in enumerate(chart_rows):
        pct = -max_dd * (1 - i / height)
        label = f"{pct:>7.1%}"
        print(f"  {DIM}{label}{RESET} │{row_str}│")

    # X-axis
    print(f"  {'':>7} └{'─' * len(weekly_dd)}┘")

    start_date = weekly_dd.index[0].strftime("%Y-%m")
    end_date = weekly_dd.index[-1].strftime("%Y-%m")
    padding = len(weekly_dd) - len(start_date) - len(end_date)
    if padding < 1:
        padding = 1
    print(f"  {'':>8} {DIM}{start_date}{' ' * padding}{end_date}{RESET}")
    print()


def print_equity_curve(portfolio_cum, benchmark_cum, width=68):
    """Print ASCII equity curve (growth of $1)."""
    print_section("EQUITY CURVE (Growth of $1)")

    # Resample to weekly
    p_weekly = portfolio_cum.resample("W").last()
    b_weekly = benchmark_cum.resample("W").last()

    if len(p_weekly) > width:
        indices = np.linspace(0, len(p_weekly) - 1, width, dtype=int)
        p_weekly = p_weekly.iloc[indices]
        b_weekly = b_weekly.iloc[indices]

    all_vals = list(p_weekly.values) + list(b_weekly.values)
    y_min = min(all_vals)
    y_max = max(all_vals)
    y_range = y_max - y_min
    if y_range == 0:
        y_range = 0.01

    height = 12

    # Build character grid
    grid = [[" " for _ in range(len(p_weekly))] for _ in range(height)]

    for col in range(len(p_weekly)):
        # Portfolio point
        p_row = int((p_weekly.values[col] - y_min) / y_range * (height - 1))
        p_row = min(max(p_row, 0), height - 1)
        grid[height - 1 - p_row][col] = f"{GREEN}●{RESET}"

        # Benchmark point
        b_row = int((b_weekly.values[col] - y_min) / y_range * (height - 1))
        b_row = min(max(b_row, 0), height - 1)
        if grid[height - 1 - b_row][col] == " ":
            grid[height - 1 - b_row][col] = f"{YELLOW}·{RESET}"

    for i, row in enumerate(grid):
        y_val = y_max - (i / (height - 1)) * y_range
        label = f"${y_val:.2f}"
        print(f"  {DIM}{label:>7}{RESET} │{''.join(row)}│")

    print(f"  {'':>7} └{'─' * len(p_weekly)}┘")

    start_date = p_weekly.index[0].strftime("%Y-%m")
    end_date = p_weekly.index[-1].strftime("%Y-%m")
    padding = len(p_weekly) - len(start_date) - len(end_date)
    if padding < 1:
        padding = 1
    print(f"  {'':>8} {DIM}{start_date}{' ' * padding}{end_date}{RESET}")
    print(f"  {'':>8} {GREEN}● Portfolio{RESET}  {YELLOW}· S&P 500 (SPY){RESET}")
    print()


# ---------------------------------------------------------------------------
# Main backtest function (importable)
# ---------------------------------------------------------------------------

def backtest(tickers, weights=None, period="2y", start=None, end=None, silent=False):
    """Run a full backtest and return results dict.

    Args:
        tickers: List of ticker symbols
        weights: Portfolio weights (must sum to 1). None = equal weight.
        period: yfinance period string ("6m", "1y", "2y", "5y")
        start/end: Date strings "YYYY-MM-DD" (overrides period)
        silent: If True, don't print anything

    Returns:
        Dict with metrics, simulation data, and per-ticker breakdown.
    """
    if weights is None:
        weights = [1.0 / len(tickers)] * len(tickers)

    assert len(weights) == len(tickers), "Weights must match number of tickers"
    assert abs(sum(weights) - 1.0) < 0.01, f"Weights must sum to 1.0, got {sum(weights)}"

    if not silent:
        print_header("PORTFOLIO BACKTEST")
        print(f"  {BOLD}Tickers:{RESET}  {', '.join(tickers)}")
        print(f"  {BOLD}Weights:{RESET}  {', '.join(f'{w:.0%}' for w in weights)}")
        if start and end:
            print(f"  {BOLD}Period:{RESET}   {start} to {end}")
        else:
            print(f"  {BOLD}Period:{RESET}   {period}")
        print(f"  {BOLD}Benchmark:{RESET} S&P 500 (SPY)")
        print(f"  {BOLD}Risk-free:{RESET} {RISK_FREE_RATE:.1%} (T-bill)")
        print()

    # Fetch data
    if not silent:
        print(f"  Fetching historical data...", end="", flush=True)
    prices = fetch_prices(tickers, period=period, start=start, end=end)
    if not silent:
        print(f" done. ({len(prices)} trading days)")
        print()

    # Check we have data for all tickers
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        print(f"  {RED}Missing data for: {', '.join(missing)}{RESET}")
        return None

    # Simulate
    sim = simulate_portfolio(prices, tickers, weights)
    metrics = compute_metrics(sim)
    monthly_data = compute_monthly_table(sim)
    ticker_breakdown = compute_per_ticker_metrics(sim, tickers, weights)

    if not silent:
        print_scorecard(metrics)
        print_ticker_breakdown(ticker_breakdown)
        print_equity_curve(sim["portfolio_cum"], sim["benchmark_cum"])
        print_drawdown_chart(metrics["drawdown_series"])
        print_monthly_table(monthly_data)

        # Final verdict
        print_section("VERDICT")
        beat_market = metrics["total_return"] > metrics["bench_total"]
        good_sharpe = metrics["sharpe"] > 1.0
        low_dd = metrics["max_drawdown"] > -0.2

        if beat_market:
            print(f"  {GREEN}✓ Beat S&P 500 by "
                  f"{metrics['total_return'] - metrics['bench_total']:+.1%}{RESET}")
        else:
            print(f"  {RED}✗ Underperformed S&P 500 by "
                  f"{metrics['total_return'] - metrics['bench_total']:+.1%}{RESET}")

        if good_sharpe:
            print(f"  {GREEN}✓ Sharpe ratio {metrics['sharpe']:.2f} "
                  f"(good risk-adjusted returns){RESET}")
        else:
            print(f"  {YELLOW}~ Sharpe ratio {metrics['sharpe']:.2f} "
                  f"(below 1.0 threshold){RESET}")

        if low_dd:
            print(f"  {GREEN}✓ Max drawdown {metrics['max_drawdown']:.1%} "
                  f"(manageable){RESET}")
        else:
            print(f"  {RED}✗ Max drawdown {metrics['max_drawdown']:.1%} "
                  f"(significant){RESET}")

        print(f"  {BOLD}Alpha: {metrics['alpha']:+.2%} | Beta: {metrics['beta']:.2f} | "
              f"Win rate: {metrics['win_rate']:.0%}{RESET}")
        print()

    return {
        "metrics": metrics,
        "simulation": sim,
        "ticker_breakdown": ticker_breakdown,
        "monthly_data": monthly_data,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Backtest a portfolio of stocks against S&P 500",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python backtest.py --tickers TEAM,INTU,DOCU --weights 0.4,0.3,0.3 --period 2y
  python backtest.py --tickers ANET,FCX,XOM --period 1y
  python backtest.py --tickers TEAM,DOCU --start 2024-06-01 --end 2026-02-20
""")
    parser.add_argument("--tickers", "-t", required=True,
                        help="Comma-separated ticker symbols")
    parser.add_argument("--weights", "-w", default=None,
                        help="Comma-separated weights (must sum to 1). Default: equal weight")
    parser.add_argument("--period", "-p", default="2y",
                        help="Lookback period: 6m, 1y, 2y, 5y (default: 2y)")
    parser.add_argument("--start", "-s", default=None,
                        help="Start date YYYY-MM-DD (overrides --period)")
    parser.add_argument("--end", "-e", default=None,
                        help="End date YYYY-MM-DD (overrides --period)")

    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]

    weights = None
    if args.weights:
        weights = [float(w.strip()) for w in args.weights.split(",")]
        if len(weights) != len(tickers):
            print(f"{RED}Error: Number of weights ({len(weights)}) must match "
                  f"tickers ({len(tickers)}){RESET}")
            sys.exit(1)

    start = args.start if args.start else None
    end = args.end if args.end else None
    period = args.period if not start else None

    result = backtest(tickers, weights=weights, period=period, start=start, end=end)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
