import pandas as pd
import numpy as np
from .base import BaseStrategy
from utils.indicators import calculate_bollinger_bands

class MeanReversion(BaseStrategy):
    def __init__(self, data: pd.DataFrame, params: dict = None, vix_data: pd.Series = None):
        super().__init__(data, params, vix_data)
        self.window = self.params.get('window', 20)
        self.num_std = self.params.get('num_std', 2.0)

    def generate_signals(self) -> pd.Series:
        """
        Mean Reversion:
        Buy when price < lower band.
        Sell at the midline.
        
        Interpretation: Long-only strategy.
        Entry: Price < Lower Band -> Long (1)
        Exit: Price >= Midline (SMA) -> Flat (0)
        """
        close = self.data['Close']
        _, lower, mid = calculate_bollinger_bands(close, window=self.window, num_std=self.num_std)
        
        # Initialize signal series
        signals = pd.Series(np.nan, index=close.index)
        
        # Entry Condition
        signals[close < lower] = 1.0
        
        # Exit Condition
        signals[close >= mid] = 0.0
        
        # Forward fill to hold position between entry and exit
        # Fill first nans with 0
        signals = signals.ffill().fillna(0)
        
        # Volatility Filter: Exit if VIX > 30
        if self.vix_data is not None:
            vix = self.vix_data.reindex(close.index).ffill()
            signals[vix > 30] = 0
            
        return signals
