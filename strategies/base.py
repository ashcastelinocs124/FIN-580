from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, data: pd.DataFrame, params: dict = None, vix_data: pd.Series = None):
        """
        Args:
            data: DataFrame containing 'Close' prices.
            params: Dictionary of parameters for the strategy.
            vix_data: Series containing VIX Close prices for volatility filtering.
        """
        self.data = data.copy()
        self.params = params if params else {}
        self.vix_data = vix_data
        self.signals = None

    @abstractmethod
    def generate_signals(self) -> pd.Series:
        """
        Generates trading signals.
        Returns:
            pd.Series: Series with values 1 (Buy), -1 (Sell), 0 (Hold/Neutral).
        """
        pass
