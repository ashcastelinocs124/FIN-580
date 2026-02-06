import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="SMA Crossover Strategy", layout="wide")

st.title("📈 SMA Crossover Strategy Dashboard")

# Sidebar for Inputs
st.sidebar.header("Strategy Parameters")

ticker = st.sidebar.text_input("Ticker Symbol", value="TSLA")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2025-01-01"))

short_window = st.sidebar.number_input("Short SMA Window", min_value=1, value=50)
long_window = st.sidebar.number_input("Long SMA Window", min_value=1, value=200)

if st.sidebar.button("Run Strategy"):
    with st.spinner("Fetching data and calculating strategy..."):
        try:
            # 1. Fetch Data
            data = yf.download(ticker, start=start_date, end=end_date)
            
            if data.empty:
                st.error("No data found. Please check the ticker symbol or date range.")
            else:
                # Handle MultiIndex if present
                if isinstance(data.columns, pd.MultiIndex):
                     if ticker in data.columns.levels[1]:
                          df = data.xs(ticker, level=1, axis=1)[['Close']].copy()
                     else:
                          # Fallback or just take the first level if structure is different
                          df = data.iloc[:, data.columns.get_level_values(1) == ticker][['Close']].copy() # Try filtering
                          if df.empty:
                               df = data[['Close']].copy() # Last resort
                else:
                    df = data[['Close']].copy()

                if isinstance(df, pd.DataFrame):
                    if df.columns.nlevels > 1:
                        df.columns = df.columns.droplevel(1) # Flatten if needed
                
                # 2. Calculate SMAs
                df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
                df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()

                # 3. Generate Signals
                df['Signal'] = 0
                df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
                
                # 4. Calculate Returns
                df['Daily_Return'] = df['Close'].pct_change()
                df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
                
                df_clean = df.dropna()
                
                df_clean['Cumulative_Market_Return'] = (1 + df_clean['Daily_Return']).cumprod()
                df_clean['Cumulative_Strategy_Return'] = (1 + df_clean['Strategy_Return']).cumprod()
                
                total_market_return = df_clean['Cumulative_Market_Return'].iloc[-1] - 1
                total_strategy_return = df_clean['Cumulative_Strategy_Return'].iloc[-1] - 1

                # Display Key Metrics
                col1, col2 = st.columns(2)
                col1.metric("Total Market Return", f"{total_market_return:.2%}")
                col2.metric("Total Strategy Return", f"{total_strategy_return:.2%}", delta=f"{(total_strategy_return - total_market_return):.2%}")

                # 5. Visualizations
                st.subheader("Price & SMA Crossover")
                fig, ax = plt.subplots(figsize=(14, 7))
                ax.plot(df.index, df['Close'], label='Close Price', alpha=0.5)
                ax.plot(df.index, df['SMA_Short'], label=f'{short_window}-day SMA', color='orange', linestyle='--')
                ax.plot(df.index, df['SMA_Long'], label=f'{long_window}-day SMA', color='green', linestyle='--')
                ax.set_title(f'{ticker} Price Analysis')
                ax.set_xlabel('Date')
                ax.set_ylabel('Price')
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)

                st.subheader("Cumulative Returns Comparison")
                fig2, ax2 = plt.subplots(figsize=(14, 7))
                ax2.plot(df_clean.index, df_clean['Cumulative_Market_Return'], label='Market (Buy & Hold)', color='grey')
                ax2.plot(df_clean.index, df_clean['Cumulative_Strategy_Return'], label='Strategy', color='blue')
                ax2.set_title('Cumulative Returns')
                ax2.legend()
                ax2.grid(True)
                st.pyplot(fig2)

                # 6. Annual Risk Metrics
                st.subheader("Annual Risk Metrics")
                metrics = []
                years = df_clean.index.year.unique()
                
                for year in years:
                    year_data = df_clean[df_clean.index.year == year]
                    if len(year_data) > 0:
                        # Market Metrics
                        market_daily_ret = year_data['Daily_Return']
                        market_std = market_daily_ret.std() * np.sqrt(252)
                        market_sharpe = (market_daily_ret.mean() / market_daily_ret.std()) * np.sqrt(252) if market_daily_ret.std() != 0 else 0
                        market_ret = (1 + market_daily_ret).prod() - 1
                        
                        # Strategy Metrics
                        strategy_daily_ret = year_data['Strategy_Return']
                        strategy_std = strategy_daily_ret.std() * np.sqrt(252)
                        strategy_sharpe = (strategy_daily_ret.mean() / strategy_daily_ret.std()) * np.sqrt(252) if strategy_daily_ret.std() != 0 else 0
                        strategy_ret = (1 + strategy_daily_ret).prod() - 1
                        
                        metrics.append({
                            'Year': year,
                            'Mkt Return': f"{market_ret:.2%}",
                            'Strat Return': f"{strategy_ret:.2%}",
                            'Mkt Std': f"{market_std:.4f}",
                            'Strat Std': f"{strategy_std:.4f}",
                            'Mkt Sharpe': f"{market_sharpe:.4f}",
                            'Strat Sharpe': f"{strategy_sharpe:.4f}"
                        })
                
                st.table(pd.DataFrame(metrics))
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.exception(e)

else:
    st.info("👈 Enter parameters and click 'Run Strategy' to see results.")
