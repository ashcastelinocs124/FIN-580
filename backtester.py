import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, prices: pd.DataFrame, signals: pd.DataFrame, initial_capital: float = 10000.0):
        """
        Args:
            prices: DataFrame of asset prices.
            signals: DataFrame of weights (0 to 1).
            initial_capital: Starting portfolio value.
        """
        self.prices = prices
        self.signals = signals
        self.initial_capital = initial_capital
        
    def run(self) -> pd.Series:
        """
        Runs the backtest and returns the portfolio value series.
        """
        # Calculate daily returns of the assets
        asset_returns = self.prices.pct_change().fillna(0)
        
        # Portfolio return = sum(weight * asset_return)
        # Note: signals are already shifted in strategy.py to align with returns
        strategy_returns = (self.signals * asset_returns).sum(axis=1)
        
        # Calculate Equity Curve
        # (1 + r).cumprod()
        equity_curve = self.initial_capital * (1 + strategy_returns).cumprod()
        
        return equity_curve

    def get_stats(self, equity_curve: pd.Series):
        """
        Returns basic stats. Quantstats handles the heavy lifting usually.
        """
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        return {
            "Total Return": total_return,
            "Final Value": equity_curve.iloc[-1]
        }
