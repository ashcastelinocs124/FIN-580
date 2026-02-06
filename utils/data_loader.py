import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_market_data(tickers: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches historical market data for multiple tickers.
    Handles MultiIndex flattening and error checking.
    """
    if not tickers:
        return pd.DataFrame()
        
    try:
        # Download data
        # auto_adjust=True handles splits and dividends
        df = yf.download(tickers, start=start_date, end=end_date, progress=False, group_by='ticker', auto_adjust=True)
        
        if df.empty:
            return pd.DataFrame()

        # If only one ticker, yfinance returns flattened columns or single level columns depending on version
        # If multiple tickers, it returns MultiIndex (Ticker, OHLCV)
        
        # Normalize to standard format: MultiIndex (Ticker, Date) or clean DataFrame
        # For this system, we want a dict of DataFrames or a MultiIndex DataFrame where columns are fields
        
        # Let's standardize: If single ticker, ensure it looks like the dict format or handle distinct logic
        # Actually, for the backtester, a Dictionary {Ticker: DataFrame} is often easiest to work with
        
        data_dict = {}
        
        if len(tickers) == 1:
            ticker = tickers[0]
            # Handling yfinance potential multi-level column output for single ticker
            if isinstance(df.columns, pd.MultiIndex):
                 df = df.xs(ticker, axis=1, level=0, drop_level=True)
            data_dict[ticker] = df
        else:
            # Multi-ticker
            for ticker in tickers:
                try:
                    # Extract dataframe for specific ticker from MultiIndex
                    # yfinance uses column level 0 as Ticker usually if group_by='ticker'
                    ticker_df = df[ticker].copy()
                    
                    # Drop rows where all cols are NaN (e.g. standard trading day mismatch)
                    ticker_df.dropna(how='all', inplace=True)
                    
                    if not ticker_df.empty:
                        data_dict[ticker] = ticker_df
                except KeyError:
                    continue
                    
        return data_dict

    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

def fetch_benchmark_data(benchmark_ticker: str, start_date: str, end_date: str) -> pd.Series:
    """Fetches benchmark close prices."""
    data = fetch_market_data([benchmark_ticker], start_date, end_date)
    if benchmark_ticker in data:
        return data[benchmark_ticker]['Close']
    return pd.Series()
