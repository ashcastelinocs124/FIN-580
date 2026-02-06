import yfinance as yf
import pandas as pd
import datetime

class DataProvider:
    """
    Abstraction for fetching and cleaning market data.
    Currently uses yfinance, but designed to be swappable.
    """
    @staticmethod
    def fetch_data(ticker: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        """
        Fetches historical data for a given ticker.
        
        Args:
            ticker: Symbol (e.g., 'SPY', 'UBER')
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            pd.DataFrame: Cleaned OHLCV data
        """
        try:
            # yfinance expects string dates in YYYY-MM-DD
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                return pd.DataFrame()
                
            # Flatten multi-level columns if present (common in recent yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Ensure index is DatetimeIndex
            df.index = pd.to_datetime(df.index)
            
            # Basic cleaning
            df = df.dropna()
            
            # Standardize column names
            df.columns = [c.lower() for c in df.columns]
            
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()
