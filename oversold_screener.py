#!/usr/bin/env python3
"""
Oversold Small-Cap Tech Screener
=================================
Screens a watchlist of small/mid-cap tech stocks for oversold conditions
after a tech selloff. Computes technical and fundamental signals and ranks
each ticker by a composite "Oversold Score" (0-7).

Dependencies:
    pip install yfinance tabulate

Usage:
    python oversold_screener.py                  # default watchlist
    python oversold_screener.py ANET INOD MOD    # custom tickers
"""

import sys
import time
import datetime
import warnings

import numpy as np
import yfinance as yf
from tabulate import tabulate

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
MAGENTA = "\033[95m"


def red(s):    return f"{RED}{s}{RESET}"
def green(s):  return f"{GREEN}{s}{RESET}"
def yellow(s): return f"{YELLOW}{s}{RESET}"
def bold(s):   return f"{BOLD}{s}{RESET}"
def dim(s):    return f"{DIM}{s}{RESET}"


def colour_pct(val, invert=False):
    if val is None:
        return dim("N/A")
    sign = "+" if val >= 0 else ""
    colour = (RED if val >= 0 else GREEN) if invert else (GREEN if val >= 0 else RED)
    return f"{colour}{sign}{val:.1f}%{RESET}"


# ---------------------------------------------------------------------------
# Technical indicator calculations
# ---------------------------------------------------------------------------

def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def detect_bullish_divergence(prices, histogram, lookback=10):
    if len(prices) < lookback + 1 or len(histogram) < lookback + 1:
        return False
    recent_prices = prices.iloc[-lookback:]
    recent_hist = histogram.iloc[-lookback:]
    price_falling = recent_prices.iloc[-1] < recent_prices.iloc[0]
    hist_min = recent_hist.min()
    hist_now = recent_hist.iloc[-1]
    histogram_narrowing = (hist_min < 0) and (hist_now > hist_min)
    return price_falling and histogram_narrowing


def volume_declining_on_down_days(df, lookback=10):
    if len(df) < lookback * 2:
        return False
    recent = df.iloc[-lookback:]
    prior = df.iloc[-lookback * 2: -lookback]
    recent_down = recent[recent["Close"] < recent["Open"]]
    prior_down = prior[prior["Close"] < prior["Open"]]
    if len(recent_down) == 0 or len(prior_down) == 0:
        return False
    return recent_down["Volume"].mean() < prior_down["Volume"].mean()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

SP500_FWD_PE = 21.5


def format_score_bar(score, max_score=7):
    filled = score
    empty = max_score - score
    if score >= 5:
        colour = GREEN
    elif score >= 3:
        colour = YELLOW
    else:
        colour = RED
    return f"{colour}{'█' * filled}{DIM}{'░' * empty}{RESET} {colour}{score}/{max_score}{RESET}"


def format_rsi(rsi, flag):
    if rsi is None:
        return dim("N/A")
    if rsi < 20:
        return f"{RED}{BOLD}{rsi:.1f} {flag}{RESET}"
    elif rsi < 30:
        return f"{RED}{rsi:.1f} {flag}{RESET}"
    elif rsi < 40:
        return f"{YELLOW}{rsi:.1f} Approaching{RESET}"
    elif rsi > 70:
        return f"{GREEN}{rsi:.1f} OVERBOUGHT{RESET}"
    else:
        return f"{rsi:.1f}"


def format_pe(pe):
    if pe is None:
        return dim("N/A")
    colour = GREEN if pe < SP500_FWD_PE else (YELLOW if pe < SP500_FWD_PE * 1.5 else RED)
    return f"{colour}{pe:.1f}x{RESET}"


def format_analyst(rating, pct_upside):
    if rating is None and pct_upside is None:
        return dim("N/A")
    parts = []
    if rating:
        buy_ratings = {"buy", "strong_buy", "strongbuy", "outperform", "overweight"}
        colour = GREEN if rating.lower().replace(" ", "_") in buy_ratings else YELLOW
        parts.append(f"{colour}{rating.upper()}{RESET}")
    if pct_upside is not None:
        parts.append(colour_pct(pct_upside))
    return " ".join(parts)


def format_vol_ratio(ratio):
    if ratio is None:
        return dim("N/A")
    if ratio > 1.5:
        return f"{RED}{BOLD}{ratio:.2f}x SPIKE{RESET}"
    elif ratio > 1.2:
        return f"{YELLOW}{ratio:.2f}x{RESET}"
    else:
        return f"{ratio:.2f}x"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_TICKERS = ["ANET", "INOD", "MOD", "PATH", "DOCU", "INTU", "TEAM",
                   "NBIS", "SMCI", "CRDO", "VRT"]

BUY_RATINGS = {"buy", "strong_buy", "strongbuy", "outperform", "overweight"}


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_TICKERS
    tickers = [t.upper() for t in tickers]

    print()
    print(f"{BOLD}{CYAN}{'=' * 72}{RESET}")
    print(f"{BOLD}{CYAN}   OVERSOLD SMALL-CAP TECH SCREENER{RESET}")
    print(f"{BOLD}{CYAN}   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 72}{RESET}")
    print()
    print(f"  Screening {BOLD}{len(tickers)}{RESET} tickers: {', '.join(tickers)}")
    print(f"  Benchmark Forward P/E: S&P 500 ~{SP500_FWD_PE}x")
    print()

    # --- Batch download all price data in one call ---
    print(f"  Fetching price data (batch)...", end="", flush=True)
    raw = yf.download(tickers, period="1y", group_by="ticker", progress=False, threads=True)
    print(f" done.")

    # yfinance with group_by='ticker' always returns multi-level columns
    single_ticker = False

    # --- Fetch fundamental data per ticker ---
    infos = {}
    for i, ticker in enumerate(tickers):
        sys.stdout.write(f"\r  Fetching fundamentals... [{i+1}/{len(tickers)}] {ticker:<6}")
        sys.stdout.flush()
        try:
            infos[ticker] = yf.Ticker(ticker).info or {}
        except Exception:
            infos[ticker] = {}
        time.sleep(0.2)  # gentle rate limiting
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()

    # --- Analyse each ticker ---
    results = []
    for ticker in tickers:
        r = {
            "ticker": ticker, "price": None, "pct_off_high": None,
            "rsi": None, "rsi_flag": "", "macd_divergence": False,
            "pct_vs_ma200": None, "fwd_pe": None,
            "vol_ratio": None, "vol_declining_down": False,
            "analyst_rating": None, "pct_upside": None,
            "fwd_earnings_positive": None,
            "score": 0, "score_details": [],
        }

        try:
            # Extract this ticker's data from the batch download
            if single_ticker:
                df = raw.copy()
            else:
                df = raw[ticker].copy()

            df = df.dropna(subset=["Close"])
            if len(df) < 30:
                results.append(r)
                continue

            close = df["Close"]
            current_price = float(close.iloc[-1])
            high_52w = float(close.max())
            r["price"] = current_price
            r["pct_off_high"] = ((current_price - high_52w) / high_52w) * 100

            # RSI
            rsi_series = compute_rsi(close)
            rsi_val = float(rsi_series.iloc[-1])
            r["rsi"] = rsi_val
            if rsi_val < 20:
                r["rsi_flag"] = "EXTREMELY OVERSOLD"
            elif rsi_val < 30:
                r["rsi_flag"] = "OVERSOLD"

            # MACD
            _, _, histogram = compute_macd(close)
            r["macd_divergence"] = detect_bullish_divergence(close, histogram)

            # 200-day MA
            if len(close) >= 200:
                ma200 = float(close.rolling(200).mean().iloc[-1])
            else:
                ma200 = float(close.mean())
            r["pct_vs_ma200"] = ((current_price - ma200) / ma200) * 100

            # Volume
            vol = df["Volume"]
            vol_5d = float(vol.iloc[-5:].mean())
            vol_30d = float(vol.iloc[-30:].mean())
            if vol_30d > 0:
                r["vol_ratio"] = vol_5d / vol_30d
            r["vol_declining_down"] = volume_declining_on_down_days(df)

            # Fundamentals from info
            info = infos.get(ticker, {})
            fwd_pe = info.get("forwardPE")
            if fwd_pe and fwd_pe > 0:
                r["fwd_pe"] = fwd_pe
            elif info.get("forwardEps") and info["forwardEps"] > 0:
                r["fwd_pe"] = current_price / info["forwardEps"]

            fwd_eps = info.get("forwardEps")
            if fwd_eps is not None:
                r["fwd_earnings_positive"] = fwd_eps > 0

            target = info.get("targetMeanPrice")
            if target and target > 0:
                r["pct_upside"] = ((target - current_price) / current_price) * 100

            rec = info.get("recommendationKey", "")
            r["analyst_rating"] = rec if rec else None

            # --- Oversold Score (0-7) ---
            score = 0
            details = []

            if r["rsi"] is not None and r["rsi"] < 30:
                score += 1; details.append("RSI<30")
            if r["fwd_pe"] is not None and 0 < r["fwd_pe"] < 15:
                score += 1; details.append("PE<15")
            if r["pct_vs_ma200"] is not None and r["pct_vs_ma200"] < 0:
                score += 1; details.append("<200MA")
            if r["macd_divergence"]:
                score += 1; details.append("MACD Div")
            if r["analyst_rating"] and r["analyst_rating"].lower().replace(" ", "_") in BUY_RATINGS:
                score += 1; details.append("Buy rated")
            if r["fwd_earnings_positive"]:
                score += 1; details.append("Fwd EPS+")
            if r["vol_declining_down"]:
                score += 1; details.append("Vol exhaust")

            r["score"] = score
            r["score_details"] = details

        except Exception as e:
            r["rsi_flag"] = f"Error: {e}"

        results.append(r)

    # Sort by score desc, then RSI asc
    results.sort(key=lambda x: (-x["score"], x["rsi"] if x["rsi"] is not None else 999))

    # -----------------------------------------------------------------------
    # Table 1: Price & Technical Overview
    # -----------------------------------------------------------------------
    print(f"{BOLD}{MAGENTA}--- PRICE & TECHNICAL OVERVIEW ---{RESET}")
    print()
    rows_tech = []
    for r in results:
        rows_tech.append([
            f"{BOLD}{r['ticker']}{RESET}",
            f"${r['price']:.2f}" if r["price"] else dim("N/A"),
            colour_pct(r["pct_off_high"]) if r["pct_off_high"] is not None else dim("N/A"),
            format_rsi(r["rsi"], r["rsi_flag"]),
            green("YES") if r["macd_divergence"] else dim("no"),
            colour_pct(r["pct_vs_ma200"]) if r["pct_vs_ma200"] is not None else dim("N/A"),
        ])
    print(tabulate(rows_tech,
                   headers=["Ticker", "Price", "% Off High", "RSI (14d)", "MACD Div", "vs 200MA"],
                   tablefmt="simple", colalign=("left", "right", "right", "left", "center", "right")))
    print()

    # -----------------------------------------------------------------------
    # Table 2: Fundamental & Volume
    # -----------------------------------------------------------------------
    print(f"{BOLD}{MAGENTA}--- FUNDAMENTAL & VOLUME ANALYSIS ---{RESET}")
    print()
    rows_fund = []
    for r in results:
        rows_fund.append([
            f"{BOLD}{r['ticker']}{RESET}",
            format_pe(r["fwd_pe"]),
            green("YES") if r["fwd_earnings_positive"] else (
                red("NO") if r["fwd_earnings_positive"] is False else dim("N/A")),
            format_vol_ratio(r["vol_ratio"]),
            green("YES") if r["vol_declining_down"] else dim("no"),
            format_analyst(r["analyst_rating"], r["pct_upside"]),
        ])
    print(tabulate(rows_fund,
                   headers=["Ticker", "Fwd P/E", "Fwd EPS+", "Vol 5d/30d", "Vol Exhaust", "Analyst"],
                   tablefmt="simple", colalign=("left", "right", "center", "right", "center", "left")))
    print()

    # -----------------------------------------------------------------------
    # Table 3: Oversold Score Ranking
    # -----------------------------------------------------------------------
    print(f"{BOLD}{MAGENTA}--- OVERSOLD SCORE RANKING ---{RESET}")
    print()
    rows_score = []
    for r in results:
        details_str = ", ".join(r["score_details"]) if r["score_details"] else dim("none")
        rows_score.append([
            f"{BOLD}{r['ticker']}{RESET}",
            format_score_bar(r["score"]),
            details_str,
            f"${r['price']:.2f}" if r["price"] else dim("N/A"),
            colour_pct(r["pct_off_high"]) if r["pct_off_high"] is not None else dim("N/A"),
        ])
    print(tabulate(rows_score,
                   headers=["Ticker", "Score", "Signals Triggered", "Price", "% Off High"],
                   tablefmt="simple", colalign=("left", "left", "left", "right", "right")))
    print()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print(f"{BOLD}{CYAN}{'=' * 72}{RESET}")
    print(f"{BOLD}{CYAN}   KEY TAKEAWAYS{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 72}{RESET}")
    print()

    top = [r for r in results if r["score"] >= 4]
    watchable = [r for r in results if 2 <= r["score"] < 4]
    avoid = [r for r in results if r["score"] < 2]

    if top:
        print(f"  {GREEN}{BOLD}HIGH CONVICTION OVERSOLD (score >= 4):{RESET}")
        for r in top:
            signals = ", ".join(r["score_details"])
            rsi_str = f"{r['rsi']:.1f}" if r["rsi"] is not None else "N/A"
            print(f"    {GREEN}>>  {r['ticker']:<6} Score {r['score']}/7  "
                  f"RSI {rsi_str}  |  {signals}{RESET}")
        print()

    if watchable:
        print(f"  {YELLOW}{BOLD}WATCHLIST (score 2-3):{RESET}")
        for r in watchable:
            signals = ", ".join(r["score_details"])
            rsi_str = f"{r['rsi']:.1f}" if r["rsi"] is not None else "N/A"
            print(f"    {YELLOW}--  {r['ticker']:<6} Score {r['score']}/7  "
                  f"RSI {rsi_str}  |  {signals}{RESET}")
        print()

    if avoid:
        print(f"  {RED}{BOLD}NOT YET OVERSOLD (score 0-1):{RESET}")
        for r in avoid:
            rsi_str = f"{r['rsi']:.1f}" if r["rsi"] is not None else "N/A"
            print(f"    {DIM}    {r['ticker']:<6} Score {r['score']}/7  RSI {rsi_str}{RESET}")
        print()

    # Volume capitulation
    vol_spikes = [r for r in results if r["vol_ratio"] and r["vol_ratio"] > 1.5]
    if vol_spikes:
        print(f"  {RED}{BOLD}VOLUME SPIKE (possible capitulation):{RESET}")
        for r in vol_spikes:
            print(f"    {RED}!!  {r['ticker']:<6} 5d/30d vol ratio: {r['vol_ratio']:.2f}x{RESET}")
        print()

    # RSI oversold
    deep_oversold = [r for r in results if r["rsi"] is not None and r["rsi"] < 30]
    if deep_oversold:
        print(f"  {RED}{BOLD}RSI OVERSOLD (<30):{RESET}")
        for r in deep_oversold:
            print(f"    {RED}!!  {r['ticker']:<6} RSI = {r['rsi']:.1f}{RESET}")
        print()

    # Biggest analyst upside
    with_upside = sorted([r for r in results if r["pct_upside"] is not None],
                         key=lambda x: -x["pct_upside"])
    if with_upside:
        print(f"  {BOLD}BIGGEST ANALYST UPSIDE:{RESET}")
        for r in with_upside[:5]:
            colour = GREEN if r["pct_upside"] > 20 else YELLOW
            print(f"    {colour}>>  {r['ticker']:<6} "
                  f"({'+' if r['pct_upside'] > 0 else ''}{r['pct_upside']:.1f}% upside){RESET}")
        print()

    print(f"  {DIM}Disclaimer: This is a screening tool, not financial advice.")
    print(f"  Always do your own due diligence before making investment decisions.{RESET}")
    print()


if __name__ == "__main__":
    main()
