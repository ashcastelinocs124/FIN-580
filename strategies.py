import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from indicators import calculate_sma, calculate_rsi, calculate_bollinger_bands

class StrategyBase(ABC):
    """
    Abstract Base Class for all strategies.
    Enforces standard interface for signal generation.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates trading signals.
        Returns DataFrame with 'signal' column (-1: Sell, 0: Hold, 1: Buy).
        """
        pass

class SMAStrategy(StrategyBase):
    def __init__(self, fast_window: int = 50, slow_window: int = 200):
        super().__init__("SMA Crossover")
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['fast_sma'] = calculate_sma(df['close'], self.fast_window)
        df['slow_sma'] = calculate_sma(df['close'], self.slow_window)
        
        df['signal'] = 0
        df.loc[df['fast_sma'] > df['slow_sma'], 'signal'] = 1
        df.loc[df['fast_sma'] < df['slow_sma'], 'signal'] = -1 # Or 0 if long-only
        
        return df

class RSIStrategy(StrategyBase):
    def __init__(self, window: int = 14, overbought: int = 70, oversold: int = 30):
        super().__init__("RSI Mean Reversion")
        self.window = window
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['rsi'] = calculate_rsi(df['close'], self.window)
        
        df['signal'] = 0
        # Buy when Oversold
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1
        # Sell when Overbought
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1
        
        return df

class BollingerStrategy(StrategyBase):
    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__("Bollinger Mean Reversion")
        self.window = window
        self.num_std = num_std

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        upper, sma, lower = calculate_bollinger_bands(df['close'], self.window, self.num_std)
        df['upper'] = upper
        df['lower'] = lower
        
        df['signal'] = 0
        # Buy when price below lower band
        df.loc[df['close'] < df['lower'], 'signal'] = 1
        # Sell when price above upper band
        df.loc[df['close'] > df['upper'], 'signal'] = -1
        
        return df
