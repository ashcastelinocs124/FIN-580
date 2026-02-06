import sys
import os
import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backtester import Backtester

def run_uber_backtest():
    ticker = "UBER"
    # UBER Surge Period: 2023 start to present (2025 early/mid)
    start = datetime.date(2023, 1, 1)
    end = datetime.date(2025, 12, 31) 
    
    print(f"--- UBER BACKTEST (Mean Reversion vs Trend) 2023-2025 ---")
    
    # 1. RSI Strategy (Mean Reversion)
    # Buy when beaten down (<30), Sell when hyped (>70)
    # Theory: Fails in strong trends because "Overbought" stays overbought.
    params_rsi = {'window': 14, 'overbought': 70, 'oversold': 30}
    bt_rsi = Backtester(ticker, start, end)
    res_rsi = bt_rsi.run("RSI", params_rsi, use_safety=False)
    
    # 2. Bollinger Strategy (Mean Reversion)
    # Buy Low Band, Sell High Band
    params_bb = {'window': 20, 'std': 2.0}
    bt_bb = Backtester(ticker, start, end)
    res_bb = bt_bb.run("Bollinger", params_bb, use_safety=False)

    # 3. Buy & Hold Benchmark (from RSI result, same data)
    # Calculate Buy & Hold Return manually from data to be sure
    data = res_rsi['results']
    if data.empty:
        print("Error: No Data")
        return

    bnh_return = (data['close'].iloc[-1] / data['close'].iloc[0]) - 1
    
    # Print Results
    print(f"{'Metric':<20} | {'Buy & Hold':<15} | {'RSI (MR)':<15} | {'Bollinger (MR)':<15}")
    print("-" * 75)
    print(f"{'Total Return':<20} | {bnh_return:.2%}          | {res_rsi['metrics']['Total Return']:.2%}          | {res_bb['metrics']['Total Return']:.2%}")
    print(f"{'Sharpe Ratio':<20} | {'N/A':<15} | {res_rsi['metrics']['Sharpe Ratio']:.2f}            | {res_bb['metrics']['Sharpe Ratio']:.2f}")
    print(f"{'Exposure Time':<20} | {'100%':<15} | {res_rsi['metrics']['Exposure Time']:.0%}             | {res_bb['metrics']['Exposure Time']:.0%}")
    
    print("\nAnalysis:")
    if res_rsi['metrics']['Total Return'] < bnh_return:
        print("-> Mean Reversion UNDERPERFORMED. The strong trend caused early exits (selling winners).")
    else:
        print("-> Mean Reversion OUTPERFORMED. Volatility was high enough to profit from dips.")

if __name__ == "__main__":
    run_uber_backtest()
