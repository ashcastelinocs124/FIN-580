import pandas as pd
import numpy as np
from .base import BaseStrategy
from utils.indicators import calculate_bollinger_bands

class BollingerBandBreakout(BaseStrategy):
    def __init__(self, data: pd.DataFrame, params: dict = None, vix_data: pd.Series = None):
        super().__init__(data, params, vix_data)
        self.window = self.params.get('window', 20)
        self.num_std = self.params.get('num_std', 2.0)

    def generate_signals(self) -> pd.Series:
        """
        Bollinger Band Breakout:
        Buy when price > upper band.
        Sell when price < lower band.
        """
        # Calculate indicators
        close = self.data['Close']
        upper, lower, _ = calculate_bollinger_bands(close, window=self.window, num_std=self.num_std)
        
        signals = pd.Series(0, index=close.index)
        
        # Vectorized signal generation
        # Buy condition
        signals[close > upper] = 1
        # Sell condition
        signals[close < lower] = -1
        
        # Forward fill signals to maintain position
        # If signal is 0 (between bands), we keep previous position
        signals = signals.replace(0, np.nan).ffill().fillna(0)
        
        # Volatility Filter: Exit if VIX > 30
        if self.vix_data is not None:
            # Align VIX data to close index
            vix = self.vix_data.reindex(close.index).ffill()
            signals[vix > 30] = 0
        
        return signals
