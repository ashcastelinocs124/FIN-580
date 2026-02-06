import pandas as pd
import numpy as np
from data import DataProvider
from strategies import SMAStrategy, RSIStrategy, BollingerStrategy
from execution import execute_strategy

class Backtester:
    def __init__(self, ticker, start_date, end_date):
        self.ticker = ticker
        self.start = start_date
        self.end = end_date
        self.data = pd.DataFrame()
        self.results = pd.DataFrame()

    def run(self, strategy_type, params, use_safety=False):
        # 1. Fetch Data
        self.data = DataProvider.fetch_data(self.ticker, self.start, self.end)
        
        if self.data.empty:
            return {"error": "No data found"}

        # 2. Initialize Strategy
        if strategy_type == 'SMA':
            strat = SMAStrategy(params['fast'], params['slow'])
        elif strategy_type == 'RSI':
            strat = RSIStrategy(params['window'], params['overbought'], params['oversold'])
        elif strategy_type == 'Bollinger':
            strat = BollingerStrategy(params['window'], params['std'])
        else:
            return {"error": "Unknown Strategy"}

        # 3. Generate Signals
        signals = strat.generate_signals(self.data)
        
        # 4. Execute
        self.results = execute_strategy(self.data, signals, use_safety_switch=use_safety)
        
        # 5. Calculate Metrics
        metrics = self._calculate_metrics(self.results)
        
        return {
            "results": self.results,
            "metrics": metrics
        }

    def _calculate_metrics(self, df):
        total_days = (df.index[-1] - df.index[0]).days
        years = total_days / 365.25
        
        total_return = df['equity'].iloc[-1] - 1
        cagr = (df['equity'].iloc[-1]) ** (1/years) - 1 if years > 0 else 0
        
        volatility = df['strategy_return'].std() * np.sqrt(252)
        sharpe = (cagr - 0.02) / volatility if volatility > 0 else 0 # Assuming 2% risk free
        
        max_dd = df['drawdown'].min()
        calmar = cagr / abs(max_dd) if max_dd != 0 else 0
        
        exposure_pct = (df['position_final'] != 0).mean()
        
        return {
            "Total Return": total_return,
            "CAGR": cagr,
            "Volatility": volatility,
            "Sharpe Ratio": sharpe,
            "Max Drawdown": max_dd,
            "Calmar Ratio": calmar,
            "Exposure Time": exposure_pct
        }
