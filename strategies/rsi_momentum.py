import pandas as pd
import numpy as np
from .base import BaseStrategy
from utils.indicators import calculate_rsi

class RSIMomentum(BaseStrategy):
    def __init__(self, data: pd.DataFrame, params: dict = None, vix_data: pd.Series = None):
        super().__init__(data, params, vix_data)
        self.window = self.params.get('window', 14)
        self.buy_threshold = self.params.get('buy_threshold', 30)
        self.sell_threshold = self.params.get('sell_threshold', 70)

    def generate_signals(self) -> pd.Series:
        """
        RSI Momentum:
        Buy at RSI < 30.
        Sell at RSI > 70.
        
        Interpretation:
        Signal = 1 (Long) when RSI < 30 (Oversold)
        Signal = -1 (Short) when RSI > 70 (Overbought)
        """
        close = self.data['Close']
        rsi = calculate_rsi(close, window=self.window)
        
        signals = pd.Series(np.nan, index=close.index)
        
        # Buy Condition
        signals[rsi < self.buy_threshold] = 1.0
        
        # Sell Condition
        signals[rsi > self.sell_threshold] = -1.0
        
        # Forward fill
        signals = signals.ffill().fillna(0)
        
        # Volatility Filter: Exit if VIX > 30
        if self.vix_data is not None:
            vix = self.vix_data.reindex(close.index).ffill()
            signals[vix > 30] = 0
        
        return signals
