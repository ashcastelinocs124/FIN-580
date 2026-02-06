import pandas as pd
import numpy as np
from strategies.base import BaseStrategy
from strategies import BollingerBandBreakout, MeanReversion, RSIMomentum
from utils.analytics import calculate_advanced_metrics

class Backtester:
    def __init__(self, tickers: list, strategy_name: str, strategy_params: dict, start_date, end_date, weights: dict = None, initial_capital: float = 100000.0, transaction_cost_bps: float = 0.0):
        self.tickers = tickers
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        self.start_date = start_date
        self.end_date = end_date
        self.weights = weights if weights else {t: 1.0/len(tickers) for t in tickers}
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost_bps / 10000.0
        self.results = {}
        self.portfolio_equity = None
        self.portfolio_returns = None

    def _get_strategy_class(self, name):
        if name == "Bollinger Band Breakout":
            return BollingerBandBreakout
        elif name == "Mean Reversion":
            return MeanReversion
        elif name == "RSI Momentum":
            return RSIMomentum
        else:
            raise ValueError(f"Unknown strategy: {name}")

    def run(self, data_dict: dict, vix_data: pd.Series = None):
        """
        Runs the backtest for all tickers and aggregates results.
        """
        StrategyClass = self._get_strategy_class(self.strategy_name)
        
        equity_curves = pd.DataFrame()
        trade_logs = []
        
        for ticker in self.tickers:
            if ticker not in data_dict:
                continue
                
            df = data_dict[ticker]
            
            # Instantiate Strategy
            strategy = StrategyClass(df, params=self.strategy_params, vix_data=vix_data)
            signals = strategy.generate_signals()
            
            # Asset returns
            close_prices = df['Close']
            daily_rets = close_prices.pct_change().fillna(0)
            
            # Shift signals to avoid lookahead bias
            # Signal at T triggers trade at T+1 Close (Simplified)
            # Or Signal at T triggers trade at T+1 Open... 
            # For this vectorized engine, we use T+1 Close assumption as per original logic
            positions = signals.shift(1).fillna(0)
            
            # Transaction Costs
            trades = positions.diff().abs().fillna(0)
            costs = trades * self.transaction_cost
            
            # Strategy Returns = (Position * Asset Returns) - Costs
            strat_rets = (positions * daily_rets) - costs
            
            # Equity Curve for this asset (Normalized)
            asset_equity = (1 + strat_rets).cumprod()
            asset_equity.name = ticker
            
            # Align dates
            equity_curves = pd.concat([equity_curves, asset_equity], axis=1)
            
            # Record Metrics for this asset
            self.results[ticker] = {
                "metrics": calculate_advanced_metrics(strat_rets),
                "visuals": {
                    "equity": asset_equity,
                    "signals": signals,
                    "price": close_prices,
                    "drawdown": calculate_drawdown_series(strat_rets)
                },
                "params": self.strategy_params # snapshot
            }
            
            # Simplified Trade Logging (Vectorized is tricky for exact trade list, approximating)
            # A trade is a change in position.
            # 0 -> 1 (Buy), 1 -> 0 (Exit), 1 -> -1 (Flip), etc.
            # This is complex to robustly log in vectorized without loop, 
            # but for "Tables" requirement we need it.
            # We will implement a quick trade extractor helper if needed later.

        # Portfolio Aggregation
        # Weighted sum of returns?
        # Rebalanced daily? Simplified: Fixed weight rebalancing daily
        # Portfolio Ret = Sum(Weight_i * Ret_i)
        
        # Align all returns to the same index
        combined_rets = pd.DataFrame()
        for ticker in self.tickers:
            if ticker in self.results:
                # Re-calculate strat_rets from equity curve to ensure alignment
                # Or store strat_rets in results
                pass
        
        # Better: Recalculate portfolio weighted returns
        # Fill NA with 0 for days specific asset didn't trade
        weighted_returns = pd.Series(0, index=equity_curves.index)
        
        for ticker, weight in self.weights.items():
            if ticker in equity_curves.columns:
                # Back out returns from equity curve: (Eq_t / Eq_t-1) - 1
                asset_rets = equity_curves[ticker].pct_change().fillna(0)
                weighted_returns += asset_rets * weight
                
        self.portfolio_returns = weighted_returns
        self.portfolio_equity = (1 + weighted_returns).cumprod() * self.initial_capital
        
        self.results['Portfolio'] = {
            "metrics": calculate_advanced_metrics(weighted_returns),
            "visuals": {
                "equity": self.portfolio_equity,
                "drawdown": calculate_drawdown_series(weighted_returns)
            }
        }
        
        return self.results

def calculate_drawdown_series(returns):
    cum = (1 + returns).cumprod()
    peak = cum.cummax()
    return (cum - peak) / peak
