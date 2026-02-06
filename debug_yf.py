import yfinance as yf
print("yfinance version:", yf.__version__)
data = yf.download(['SPY', 'XLK'], start='2020-01-01', end='2020-01-10', progress=False)
print("\nData Columns:", data.columns)
print("\nData Head:\n", data.head())
print("\nAccessing Adj Close directly...")
try:
    print(data['Adj Close'].head())
except Exception as e:
    print(f"Error: {e}")
