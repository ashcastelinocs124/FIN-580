import pandas as pd
import numpy as np

def calculate_sma(series: pd.Series, window: int = 20) -> pd.Series:
    """Calculates Simple Moving Average."""
    return series.rolling(window=window).mean()

def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """
    Calculates Bollinger Bands.
    Returns: upper_band, lower_band, mid_band (SMA)
    """
    mid_band = series.rolling(window=window).mean()
    std_dev = series.rolling(window=window).std()
    
    upper_band = mid_band + (std_dev * num_std)
    lower_band = mid_band - (std_dev * num_std)
    
    return upper_band, lower_band, mid_band

def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI).
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    # Use exponential moving average for RSI (standard Wilder's smoothing)
    # Alternatively simple average can be used: avg_gain = gain.rolling(window=window).mean()
    # But Wilder's is more standard. We'll use pandas ewm with com=(window-1).
    
    avg_gain = gain.ewm(com=window-1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window-1, min_periods=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
