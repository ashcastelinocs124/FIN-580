import yfinance as yf
import pandas as pd
from typing import List

def get_data(tickers: List[str], start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Downloads historical adjusted close prices for a list of tickers.
    
    Args:
        tickers: List of ticker symbols (e.g., ['SPY', 'XLK']).
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD). Defaults to today.
        
    Returns:
        DataFrame containing Adjusted Close prices.
    """
    print(f"Downloading data for {len(tickers)} tickers from {start_date}...")
    try:
        # yfinance v1.0+ typically returns 'Close' which is auto-adjusted if auto_adjust=True (default often)
        # We request 'Close' column. 
        df = yf.download(tickers, start=start_date, end=end_date, progress=False)
        
        # Check if 'Adj Close' exists, if so use it, otherwise use 'Close'
        if 'Adj Close' in df.columns.get_level_values(0):
            data = df['Adj Close']
        else:
            data = df['Close']
        
        # If only one ticker is downloaded, yf returns a Series or single-col DF depending on version
        # Ensure we always return a DataFrame
        if isinstance(data, pd.Series):
            data = data.to_frame()
            
        # Drop tickers with no data (if any)
        data.dropna(axis=1, how='all', inplace=True)
        
        return data
    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test
    df = get_data(['SPY', 'AAPL'], '2020-01-01')
    print(df.head())
