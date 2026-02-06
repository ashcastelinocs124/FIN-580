import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategies import BollingerBandBreakout, MeanReversion, RSIMomentum

def generate_mock_data(n=200, seed=42):
    np.random.seed(seed)
    initial_price = 100
    returns = np.random.normal(0, 0.02, n)
    prices = initial_price * (1 + returns).cumprod()
    
    dates = pd.date_range(start='2023-01-01', periods=n, freq='D')
    df = pd.DataFrame({'Close': prices}, index=dates)
    return df

def run_verification():
    print("Generating Mock Data...")
    df = generate_mock_data(n=300)
    print(f"Data shape: {df.shape}")
    print(df.head())
    print("-" * 30)

    strategies = [
        ("Bollinger Band Breakout", BollingerBandBreakout(df)),
        ("Mean Reversion", MeanReversion(df)),
        ("RSI Momentum", RSIMomentum(df))
    ]

    for name, strategy in strategies:
        print(f"Running {name}...")
        try:
            signals = strategy.generate_signals()
            print(f"Signals generated. Signal distribution:")
            print(signals.value_counts())
            print(f"Latest Signal: {signals.iloc[-1]}")
            
            # Simple check
            if signals.isnull().any():
                print("WARNING: NaNs found in signals (after fillna??)")
            
            print("OK")
            print("-" * 30)
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_verification()
