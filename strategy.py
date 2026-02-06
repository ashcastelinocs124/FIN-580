import pandas as pd
import numpy as np

class SectorMomentumStrategy:
    def __init__(self, prices: pd.DataFrame, comparison_asset: str = 'SPY', 
                 lookback_period: int = 252, n_top: int = 3):
        """
        Args:
            prices: DataFrame of adjusted close prices (columns are tickers, index is date).
            comparison_asset: Ticker to use for regime filter (e.g., SPY).
            lookback_period: Days to calculate momentum (e.g., 252 for 12 months).
            n_top: Number of top sectors to select.
        """
        self.prices = prices
        self.comparison_asset = comparison_asset
        self.lookback_period = lookback_period
        self.n_top = n_top
        
    def generate_signals(self) -> pd.DataFrame:
        """
        Generates trading signals (1 for buy, 0 for hold/cash).
        Returns a DataFrame of weights (0 to 1) for each asset.
        """
        # 1. Calculate Momentum (Return over lookback)
        # Using 1-month lag to avoid short-term reversals is common, but we will do simple return first
        # momentum = P_t / P_{t-lookback} - 1
        momentum = self.prices.pct_change(self.lookback_period)
        
        # 2. Trend Filter (Price > 200 SMA)
        # We generally check the trend of the asset itself or the broad market
        sma_200 = self.prices.rolling(window=200).mean()
        trend_positive = self.prices > sma_200
        
        # 3. Selection
        # We want to select top N assets that have positive momentum AND are in an uptrend
        # Create a ranking df
        
        # Filter: If momentum < 0 or trend is negative, set momentum to -inf to avoid selection
        valid_momentum = momentum.copy()
        
        # Condition: Asset must have positive momentum and be above its own 200 SMA
        # (Some variations use SPY > 200 SMA as a general market filter)
        mask = (valid_momentum > 0) & (trend_positive)
        valid_momentum[~mask] = -np.inf
        
        # Rank assets daily (axis=1)
        # method='min' means if 2 tie for 3rd, both get 3rd. We want descending rank.
        ranks = valid_momentum.rank(axis=1, ascending=False, method='first')
        
        # Create signals
        signals = pd.DataFrame(0, index=self.prices.index, columns=self.prices.columns)
        signals[ranks <= self.n_top] = 1.0 / self.n_top
        
        # Handling the case where fewer than n_top assets are valid
        # The remaining allocation effectively goes to "Cash" (returns = 0 in this simplified model)
        # Or we could allocate it completely to the valid ones (equal weight among selected).
        # Here we stick to fixed weight per slot (1/n_top). Unused slots = Cash.
        
        # Rebalance only at month end? 
        # For simplicity in this vectorized vector, we compute daily but realistic strategies rebalance monthly.
        # Let's resample signals to month end to simulate monthly rebalancing
        
        return signals

    def get_monthly_rebalanced_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        Takes daily signals and enforces monthly rebalancing logic.
        """
        # Resample to month end, taking the last value
        monthly_signals = signals.resample('M').last()
        
        # Forward fill these signals to daily timeframe
        daily_signals_from_monthly = monthly_signals.reindex(signals.index).ffill()
        
        # Shift by 1 day to avoid lookahead bias (signal calculated at close T, trade at open/close T+1)
        # In a vector backtest using Close-to-Close returns, shifting signals by 1 is standard.
        return daily_signals_from_monthly.shift(1).fillna(0)
