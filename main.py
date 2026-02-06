import pandas as pd
import data_loader
import strategy
import backtester
import quantstats as qs
import matplotlib.pyplot as plt
import os
import webbrowser

# Define Universe
# SPDR Sector ETFs + Benchmark (SPY) + Safe Asset (IEF/SHY - not used in simple version but good to have)
TICKERS = [
    'SPY', # Benchmark
    'XLK', 'XLV', 'XLF', 'XLY', 'XLP', 'XLE', 'XLI', 'XLB', 'XLRE', 'XLU', 'XLC' 
]

START_DATE = '2010-01-01'

def main():
    print("Step 1: Loading Data...")
    prices = data_loader.get_data(TICKERS, START_DATE)
    
    if prices.empty:
        print("No data found. Exiting.")
        return

    # Separate Benchmark
    spy_prices = prices[['SPY']]
    sector_prices = prices.drop(columns=['SPY'])
    
    # Handle missing data (forward fill)
    sector_prices.ffill(inplace=True)
    spy_prices.ffill(inplace=True)

    print("Step 2: Generating Signals...")
    strat = strategy.SectorMomentumStrategy(sector_prices, comparison_asset='SPY', lookback_period=126, n_top=3) # 126 days ~ 6 months
    raw_signals = strat.generate_signals()
    final_signals = strat.get_monthly_rebalanced_signals(raw_signals)
    
    print("Step 3: Running Backtest...")
    bt = backtester.Backtester(sector_prices, final_signals)
    portfolio_value = bt.run()
    
    # Calculate returns series for QuantStats
    portfolio_returns = portfolio_value.pct_change().dropna()
    benchmark_returns = spy_prices['SPY'].pct_change().dropna()
    
    # Align dates
    common_index = portfolio_returns.index.intersection(benchmark_returns.index)
    portfolio_returns = portfolio_returns.loc[common_index]
    benchmark_returns = benchmark_returns.loc[common_index]
    
    print("Step 4: Generating Report...")
    # Print summary to console
    print("\n--- Performance Summary ---")
    qs.reports.metrics(portfolio_returns, benchmark=benchmark_returns)
    
    # Generate HTML report
    report_file = "strategy_report.html"
    qs.reports.html(portfolio_returns, benchmark=benchmark_returns, output=report_file, title="Sector Rotation Strategy vs S&P 500")
    print(f"\nReport saved to {os.path.abspath(report_file)}")
    
    # Attempt to open report
    # webbrowser.open('file://' + os.path.abspath(report_file))

if __name__ == "__main__":
    main()
