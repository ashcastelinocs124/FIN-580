import sys
import os
import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backtester import Backtester

def run_stress_test():
    ticker = "SPY"
    start = datetime.date(2019, 1, 1)
    end = datetime.date(2020, 12, 31)
    
    # Standard Params
    params = {'fast': 50, 'slow': 200}
    strategy = "SMA"
    
    print(f"--- STRESS TEST 2020: {ticker} ({strategy}) ---")
    
    # 1. Run WITHOUT Safety
    bt_no_safe = Backtester(ticker, start, end)
    res_no_safe = bt_no_safe.run(strategy, params, use_safety=False)
    dd_no_safe = res_no_safe['metrics']['Max Drawdown']
    
    # 2. Run WITH Safety
    bt_safe = Backtester(ticker, start, end)
    res_safe = bt_safe.run(strategy, params, use_safety=True)
    dd_safe = res_safe['metrics']['Max Drawdown']
    
    print(f"Max Drawdown (No Safety): {dd_no_safe:.2%}")
    print(f"Max Drawdown (With Safety): {dd_safe:.2%}")
    print(f"Improvement: {(dd_safe - dd_no_safe):.2%}")

if __name__ == "__main__":
    run_stress_test()
