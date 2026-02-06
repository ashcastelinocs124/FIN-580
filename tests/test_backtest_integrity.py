import unittest
import pandas as pd
import numpy as np
import sys
import os
from unittest.mock import MagicMock

# Mock yfinance before importing modules that use it
sys.modules['yfinance'] = MagicMock()

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtester import Backtester
from indicators import calculate_sma
from strategies import SMAStrategy
from execution import execute_strategy, SafetySwitch, SafetyState

class TestBacktestIntegrity(unittest.TestCase):
    
    def setUp(self):
        # Sample Data
        dates = pd.date_range(start="2020-01-01", periods=100, freq='D')
        prices = list(np.linspace(100, 150, 60)) + list(np.linspace(150, 100, 40))
        self.sample_data = pd.DataFrame({'close': prices, 'open': prices, 'high': prices, 'low': prices}, index=dates)

        # Volatile Data
        prices_v = [100.0] * 50
        # Massive Volatility spike to ensure trigger (Baseline ~10, New ~100)
        prices_v += [100.0 + (50 if i % 2 == 0 else -50) for i in range(50)]
        self.volatile_data = pd.DataFrame({'close': prices_v, 'open': prices_v, 
                                           'high': [p + 5 for p in prices_v], 
                                           'low': [p - 5 for p in prices_v]}, index=dates)

    def test_sma_signal_generation(self):
        strat = SMAStrategy(fast_window=10, slow_window=20)
        signals = strat.generate_signals(self.sample_data)
        
        self.assertTrue('signal' in signals.columns)
        self.assertTrue(signals['signal'].isin([1, 0, -1]).all())
        self.assertEqual(signals['signal'].iloc[-1], -1)

    def test_lookahead_bias_prevention(self):
        # Create manual signals: 1 at index 10
        self.sample_data['signal'] = 0
        self.sample_data.iloc[10, self.sample_data.columns.get_loc('signal')] = 1
        
        # Run execution
        results = execute_strategy(self.sample_data, self.sample_data[['signal']], use_safety_switch=False)
        
        # Check Index 10: Signal=1. Position should be 0 (shift).
        self.assertEqual(results.iloc[10]['raw_signal'], 1)
        self.assertEqual(results.iloc[10]['position_final'], 0) # Assumes prev 0
        
        # Check Index 11: Position should be 1.
        self.assertEqual(results.iloc[11]['position_final'], 1)
        
        expected_ret = results.iloc[11]['market_return'] * 1
        self.assertAlmostEqual(results.iloc[11]['strategy_return'], expected_ret)

    def test_safety_switch_trigger(self):
        self.volatile_data['signal'] = 1
        # Needed: calculate ATR on the data before passing? 
        # execute_strategy calculates ATR internally if use_safety=True
        
        results = execute_strategy(self.volatile_data, self.volatile_data[['signal']], use_safety_switch=True)
        
        # Check if we successfully entered RISK_OFF state
        risk_off_rows = results[results['safety_state'] == 'Risk Off']
        self.assertFalse(risk_off_rows.empty, "Safety switch did not trigger on volatile data")
        
        if not risk_off_rows.empty:
            # Get integer location of first trigger
            row_idx = results.index.get_loc(risk_off_rows.index[0])
            
            # Verify trigger set mult to 0 at T
            self.assertEqual(results.iloc[row_idx]['safety_mult'], 0.0)
            
            # Verify position is cut at T+1 (if available)
            if row_idx + 1 < len(results):
                self.assertEqual(results.iloc[row_idx + 1]['position_final'], 0.0)

if __name__ == '__main__':
    unittest.main()
