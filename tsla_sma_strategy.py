import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_strategy():
    # 1. Fetch AAPL data (2020-2024)
    # End date is exclusive in yfinance, so we use 2025-01-01 to include all of 2024
    print("Fetching TSLA data...")
    ticker = "TSLA"
    start_date = "2020-01-01"
    end_date = "2025-01-01"
    
    data = yf.download(ticker, start=start_date, end=end_date)
    
    if data.empty:
        print("No data fetched. Check your internet connection or ticker symbol.")
        return

    # Ensure we are working with the 'Close' price and handle MultiIndex if present
    if isinstance(data.columns, pd.MultiIndex):
         data = data.xs(ticker, level=1, axis=1) if ticker in data.columns.levels[1] else data
         # If xs didn't work as expected or structure is different, fail safe to just using 'Close' if available
         if 'Close' in data.columns:
             df = data[['Close']].copy()
         else:
             # Fallback for simple structure
             df = data.copy()
    else:
        df = data[['Close']].copy()

    # 2. Calculate 50-day and 200-day SMAs
    print("Calculating SMAs...")
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    # 3. Generate 'Signal' column: 1 when 50 > 200, else 0
    df['Signal'] = 0
    df.loc[df['SMA50'] > df['SMA200'], 'Signal'] = 1

    # 4. Plot the price with SMAs overlayed
    print("Generating plot...")
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['Close'], label='TSLA Close Price', alpha=0.5)
    plt.plot(df.index, df['SMA50'], label='50-day SMA', color='orange', linestyle='--')
    plt.plot(df.index, df['SMA200'], label='200-day SMA', color='green', linestyle='--')
    
    # Optional: Highlight signal changes maybe? For now just plotting as requested.
    
    plt.title('TSLA Stock Price with 50 & 200 Day SMAs (2020-2024)')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid(True)
    
    output_file = 'strategy_performance.png'
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    
    # 5. Calculate Returns
    # Calculate daily returns
    df['Daily_Return'] = df['Close'].pct_change()
    
    # Shift signal by 1 because we trade based on the signal generated at the close of yesterday
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
    
    # Calculate Cumulative Returns
    # We drop the first NaN value created by pct_change and shift
    df = df.dropna()
    
    df['Cumulative_Market_Return'] = (1 + df['Daily_Return']).cumprod()
    df['Cumulative_Strategy_Return'] = (1 + df['Strategy_Return']).cumprod()
    
    total_market_return = df['Cumulative_Market_Return'].iloc[-1] - 1
    total_strategy_return = df['Cumulative_Strategy_Return'].iloc[-1] - 1
    
    print(f"\nTotal Market Return: {total_market_return:.2%}")
    print(f"Total Strategy Return: {total_strategy_return:.2%}")
    
    # 6. Calculate Annual Statistics
    print("\nAnnual Risk Metrics:")
    metrics = []
    years = df.index.year.unique()
    
    for year in years:
        year_data = df[df.index.year == year]
        
        # Market Metrics
        market_daily_ret = year_data['Daily_Return']
        market_std = market_daily_ret.std() * np.sqrt(252)
        market_sharpe = (market_daily_ret.mean() / market_daily_ret.std()) * np.sqrt(252)
        market_ret = (1 + market_daily_ret).prod() - 1
        
        # Strategy Metrics
        strategy_daily_ret = year_data['Strategy_Return']
        strategy_std = strategy_daily_ret.std() * np.sqrt(252)
        strategy_sharpe = (strategy_daily_ret.mean() / strategy_daily_ret.std()) * np.sqrt(252)
        strategy_ret = (1 + strategy_daily_ret).prod() - 1
        
        metrics.append({
            'Year': year,
            'Mkt Return': market_ret,
            'Strat Return': strategy_ret,
            'Mkt Std': market_std,
            'Strat Std': strategy_std,
            'Mkt Sharpe': market_sharpe,
            'Strat Sharpe': strategy_sharpe
        })
        
    metrics_df = pd.DataFrame(metrics)
    # Format for clean printing
    pd.options.display.float_format = '{:.4f}'.format
    print(metrics_df.to_string(index=False))
    
    print("\nRecent Data & Signals:")
    print(df.tail())

if __name__ == "__main__":
    run_strategy()
