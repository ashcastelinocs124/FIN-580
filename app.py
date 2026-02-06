import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backtester import Backtester

# --- Config ---
st.set_page_config(layout="wide", page_title="Antigravity Quant", page_icon="📈")

# --- Load CSS ---
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- Header ---
st.title("Antigravity Quant Dashboard")
st.markdown("""
> [!WARNING]
> **Research Only**: Market data is delayed. Do not use for live trading.
""")

# --- Sidebar ---
st.sidebar.header("Configuration")

ticker = st.sidebar.text_input("Ticker", "SPY")

start_date = st.sidebar.date_input("Start Date", datetime.date(2018, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.date.today())

# Strategy Selection
strategy_type = st.sidebar.selectbox("Strategy", ["SMA", "RSI", "Bollinger"])

params = {}
if strategy_type == "SMA":
    params['fast'] = st.sidebar.slider("Fast Window", 10, 100, 50)
    params['slow'] = st.sidebar.slider("Slow Window", 50, 300, 200)
elif strategy_type == "RSI":
    params['window'] = st.sidebar.slider("RSI Window", 5, 30, 14)
    params['overbought'] = st.sidebar.slider("Overbought", 50, 90, 70)
    params['oversold'] = st.sidebar.slider("Oversold", 10, 50, 30)
elif strategy_type == "Bollinger":
    params['window'] = st.sidebar.slider("Window", 10, 50, 20)
    params['std'] = st.sidebar.slider("Std Dev", 1.0, 3.0, 2.0)

# Safety Switch
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Safety Switch")
use_safety = st.sidebar.toggle("Enable Safety Switch", value=True)

if use_safety:
    st.sidebar.info("Protects capital during high volatility.")

# --- Execution ---
if st.button("Run Simulation", type="primary"):
    with st.spinner("Running Backtest..."):
        backtester = Backtester(ticker, start_date, end_date)
        outcome = backtester.run(strategy_type, params, use_safety=use_safety)

        if "error" in outcome:
            st.error(outcome['error'])
        else:
            results = outcome['results']
            metrics = outcome['metrics']

            # --- Metrics Row ---
            st.markdown("### Performance Metrics")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Return", f"{metrics['Total Return']:.2%}")
            c2.metric("CAGR", f"{metrics['CAGR']:.2%}")
            c3.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
            c4.metric("Descaled Calmar", f"{metrics['Calmar Ratio']:.2f}")

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
            c6.metric("Volatility", f"{metrics['Volatility']:.2%}")
            c7.metric("Exposure Time", f"{metrics['Exposure Time']:.0%}")
            c8.metric("Safety Active", "Yes" if use_safety else "No")

            # --- Charts ---
            st.markdown("---")
            
            # Chart 1: Price & Technicals
            fig_price = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                      vertical_spacing=0.03, subplot_titles=(f"{ticker} Price", "Signals"),
                                      row_heights=[0.7, 0.3])

            # Candlestick
            fig_price.add_trace(go.Candlestick(x=results.index,
                                               open=results['open'], high=results['high'],
                                               low=results['low'], close=results['close'],
                                               name="Price"), row=1, col=1)

            # Strategy Overlays
            if strategy_type == "SMA":
                fig_price.add_trace(go.Scatter(x=results.index, y=results['fast_sma'], name="Fast SMA", line=dict(color='orange')), row=1, col=1)
                fig_price.add_trace(go.Scatter(x=results.index, y=results['slow_sma'], name="Slow SMA", line=dict(color='blue')), row=1, col=1)
            elif strategy_type == "Bollinger":
                fig_price.add_trace(go.Scatter(x=results.index, y=results['upper'], name="Upper BB", line=dict(color='gray', dash='dash')), row=1, col=1)
                fig_price.add_trace(go.Scatter(x=results.index, y=results['lower'], name="Lower BB", line=dict(color='gray', dash='dash')), row=1, col=1)

            # Safety Background
            if use_safety:
                # Highlight Risk Off periods
                # This is tricky in plotly efficiently, but let's try a simple scatter of Safety State
                risk_off = results[results['safety_state'] == 'Risk Off']
                if not risk_off.empty:
                    fig_price.add_trace(go.Scatter(x=risk_off.index, y=risk_off['close'], mode='markers', 
                                                   marker=dict(color='red', symbol='x', size=5),
                                                   name="Safety Triggered"), row=1, col=1)

            # Equity Curve
            fig_equity = go.Figure()
            fig_equity.add_trace(go.Scatter(x=results.index, y=results['equity'], name="Strategy Equity", 
                                            line=dict(color='#38bdf8', width=2)))
            
            # Benchmark (Buy & Hold)
            benchmark_equity = (1 + results['market_return']).cumprod()
            fig_equity.add_trace(go.Scatter(x=results.index, y=benchmark_equity, name="Buy & Hold", 
                                            line=dict(color='#94a3b8', dash='dot')))

            fig_equity.update_layout(title="Equity Curve", template="plotly_dark", 
                                     paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

            fig_price.update_layout(title="Technical Analysis", template="plotly_dark", xaxis_rangeslider_visible=False,
                                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600)

            st.plotly_chart(fig_price, use_container_width=True)
            st.plotly_chart(fig_equity, use_container_width=True)
            
            # Trades Table (Sample)
            with st.expander("Latest Data View"):
                st.dataframe(results.tail(20))

