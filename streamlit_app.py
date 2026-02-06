import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Internal Engine Imports
from utils.data_loader import fetch_market_data, fetch_benchmark_data
from strategies.backtester import Backtester

# --- THEME CONFIGURATION ---
st.set_page_config(
    page_title="Quant Engine | Professional",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

from war_room import render_war_room

# --- NAVIGATION ---
mode = st.sidebar.radio("Navigation", ["Quant Engine", "Global Macro War Room"], index=0)

THEME = {
    "bg_color": "#0f172a",
    "component_bg": "#1e293b",
    "text_color": "#f8fafc",
    "accent_color": "#3b82f6",
    "success_color": "#10b981", 
    "danger_color": "#ef4444",
    "chart_bg": "#0f172a",
    "grid_color": "#334155"
}

# Apply Custom CSS
custom_css = f"""
<style>
    /* Main Background */
    .stApp {{
        background-color: {THEME['bg_color']};
        color: {THEME['text_color']};
        font-family: 'Inter', system-ui, sans-serif;
    }}
    
    /* Sidebar */
    .stSidebar {{
        background-color: {THEME['component_bg']};
        border-right: 1px solid {THEME['grid_color']};
    }}
    
    /* Headers - Force White */
    h1, h2, h3, h4, h5, h6 {{
        color: white !important;
        font-weight: 700 !important;
    }}
    
    /* Input Labels (Sidebar & Main) */
    .stMarkdown label, .stSelectbox label, .stMultiSelect label, .stNumberInput label, .stDateInput label, .stSlider label {{
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }}
    
    /* Tabs - Improve Contrast */
    button[data-baseweb="tab"] > div {{
        color: #cbd5e1 !important; /* Light Grey */
        font-weight: 600;
        font-size: 1rem;
    }}
    button[data-baseweb="tab"][aria-selected="true"] > div {{
        color: {THEME['accent_color']} !important;
        border-bottom-color: {THEME['accent_color']} !important;
    }}
    
    /* Metrics */
    div[data-testid="stMetricValue"] {{
        font-size: 1.6rem !important;
        font-weight: 700;
        color: white;
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 0.9rem !important;
        color: #94a3b8;
        font-weight: 500;
    }}
    .metric-card {{
        background-color: {THEME['component_bg']};
        border: 1px solid {THEME['grid_color']};
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    /* Expander Headers */
    /* Expander Headers */
    .streamlit-expanderHeader {{
        color: white !important;
        font-weight: 700 !important;
        background-color: {THEME['component_bg']} !important;
    }}
    .streamlit-expanderHeader p {{
        font-size: 1.1rem !important;
    }}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

if mode == "Global Macro War Room":
    render_war_room()

else:
    # --- SESSION STATE INITIALIZATION ---
    if 'runs' not in st.session_state:
        st.session_state['runs'] = {} # History of runs: {run_id: result_dict}

    if 'presets' not in st.session_state:
        st.session_state['presets'] = {
            "Default Mean Reversion": {"window": 20, "num_std": 2.0},
            "Fast Trend": {"window": 10, "num_std": 1.5},
            "Slow Trend": {"window": 50, "num_std": 2.5}
        }

    # --- SIDEBAR CONFIGURATION ---
    st.sidebar.markdown("## ⚙️ Configuration")

    # 1. Backtest Settings
    with st.sidebar.expander("📅 Backtest Settings", expanded=True):
        start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
        end_date = st.date_input("End Date", pd.to_datetime("today"))
        
        # Portfolio Universe
        tickers = st.multiselect(
            "Universe",
            ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "SPY", "QQQ", "UBER", "BTC-USD"],
            default=["AAPL"]
        )
        
        benchmark_ticker = st.selectbox("Benchmark", ["SPY", "QQQ"], index=0)
        
        initial_capital = st.number_input("Initial Capital ($)", value=100000.0, step=10000.0)
        transaction_cost_bps = st.slider("Transaction Cost (bps)", 0, 50, 5)

    # 2. Strategy Settings
    with st.sidebar.expander("♟️ Strategy Logic", expanded=True):
        strategy_name = st.selectbox(
            "Strategy Model",
            ["Bollinger Band Breakout", "Mean Reversion", "RSI Momentum"]
        )
        
        # Dynamic Parameters based on Strategy
        params = {}
        if strategy_name in ["Bollinger Band Breakout", "Mean Reversion"]:
            params['window'] = st.number_input("Lookback Window", value=20, min_value=5, max_value=200)
            params['num_std'] = st.number_input("Std Dev Threshold", value=2.0, min_value=0.5, max_value=4.0, step=0.1)
        elif strategy_name == "RSI Momentum":
            params['window'] = st.number_input("RSI Window", value=14, min_value=5)
            params['buy_threshold'] = st.slider("Buy Threshold", 10, 50, 30)
            params['sell_threshold'] = st.slider("Sell Threshold", 50, 90, 70)
            
        use_vix_filter = st.checkbox("Volatility Filter (VIX > 30)", value=True)

    # 3. Actions
    st.sidebar.markdown("---")
    col_run, col_save = st.sidebar.columns(2)
    run_pressed = col_run.button("RUN ANALYSIS", type="primary", use_container_width=True)
    save_preset = col_save.button("Save Preset", use_container_width=True)

    if save_preset:
        preset_name = f"{strategy_name} - {len(st.session_state['presets'])+1}"
        st.session_state['presets'][preset_name] = params
        st.sidebar.success(f"Saved: {preset_name}")

    # --- MAIN ANALYSIS ENGINE ---

    if run_pressed:
        if not tickers:
            st.error("Please select at least one asset.")
            st.stop()
            
        with st.spinner("Initializing Data Engine..."):
            # 1. Fetch Data
            market_data_dict = fetch_market_data(tickers, start_date, end_date)
            
            # 2. Fetch VIX if needed
            vix_series = None
            if use_vix_filter:
                vix_df = fetch_market_data(["^VIX"], start_date, end_date)
                if "^VIX" in vix_df:
                    vix_series = vix_df["^VIX"]['Close']

            # 3. Fetch Benchmark
            benchmark_series = fetch_benchmark_data(benchmark_ticker, start_date, end_date)

        if not market_data_dict:
             st.error("Failed to load market data.")
             st.stop()

        with st.spinner("Running Backtest Simulation..."):
            # 4. Run Backtest
            backtester = Backtester(
                tickers=tickers,
                strategy_name=strategy_name,
                strategy_params=params,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                transaction_cost_bps=transaction_cost_bps
            )
            
            results = backtester.run(market_data_dict, vix_data=vix_series)
            
            # Save run to session state for comparison
            run_id = f"{strategy_name}_{datetime.now().strftime('%H:%M:%S')}"
            st.session_state['runs'][run_id] = {
                "results": results,
                "config": {
                    "tickers": tickers,
                    "strategy": strategy_name,
                    "params": params
                },
                "benchmark": benchmark_series
            }
            st.session_state['current_run'] = run_id

    # --- DASHBOARD RENDERER ---

    if 'current_run' in st.session_state:
        run_id = st.session_state['current_run']
        run_data = st.session_state['runs'][run_id]
        results = run_data['results']
        config = run_data['config']
        benchmark_data = run_data['benchmark']
        
        st.markdown(f"# 📊 Institutional Analytics: {config['strategy']}")
        st.caption(f"Run ID: {run_id} | Universe: {', '.join(config['tickers'])} | Capital: ${initial_capital:,.0f}")
        
        # --- 1. HERO METRICS ---
        # Display Portfolio Metrics if >1 ticker, else Trade Metrics for the single ticker
        main_key = 'Portfolio' if len(config['tickers']) > 1 else config['tickers'][0]
        metrics = results[main_key]['metrics']
        
        cols = st.columns(6)
        
        def metric_card(col, label, value, fmt="{:.2%}", delta=None, delta_color="normal"):
            with col:
                st.metric(label, fmt.format(value), delta, delta_color=delta_color)
                
        metric_card(cols[0], "Total Return", metrics['Total Return'])
        metric_card(cols[1], "Ann. Volatility", metrics['Volatility'])
        metric_card(cols[2], "Sharpe Ratio", metrics['Sharpe Ratio'], fmt="{:.2f}")
        metric_card(cols[3], "Max Drawdown", metrics['Max Drawdown'], delta_color="inverse")
        metric_card(cols[4], "Win Rate", metrics['Win Rate'])
        metric_card(cols[5], "Profit Factor", metrics['Profit Factor'], fmt="{:.2f}")

        st.markdown("---")

        # --- 2. CHARTING TABS ---
        tab_price, tab_equity, tab_drawdown, tab_dist, tab_compare = st.tabs([
            "📈 Price & Signals", "💰 Equity Curve", "📉 Drawdown", "📊 Distribution", "⚖️ Comparison"
        ])
        
        # A. Price Chart
        with tab_price:
            selected_ticker = st.selectbox("Select Asset", config['tickers'], key="price_chart_select")
            if selected_ticker in results:
                asset_res = results[selected_ticker]
                price_df = asset_res['visuals']['price']
                signals = asset_res['visuals']['signals']
                
                # Create Candlestick
                fig = go.Figure()
                
                # Candles is tricky since we only have Close in the backtest result 'visuals' dict from backtester.py
                # But we cached the full data in market_data_dict during the run... 
                # WAIT: backtester logic primarily used `df` which had OHLC. 
                # Currently `results[ticker]['visuals']['price']` is just Close.
                # Ideally we want full OHLC. For now, let's plot Line Chart of Close if we don't have OHLC handy in session state.
                # To fix this properly, Backtester should arguably store the OHLC dataframe ref or we re-fetch from cache.
                # Let's use Line Chart for Close and Markers for simplicity in this turn, or re-fetch from cache if possible.
                # Actually, `st.cache_data` makes re-calling fetch cheap.
                
                # Re-fetch for full OHLC (Instant)
                full_data = fetch_market_data([selected_ticker], start_date, end_date)[selected_ticker]
                
                fig.add_trace(go.Candlestick(
                    x=full_data.index,
                    open=full_data['Open'], high=full_data['High'],
                    low=full_data['Low'], close=full_data['Close'],
                    name=selected_ticker
                ))
                
                # Add Buy Markers
                buy_signals = full_data.loc[signals == 1]
                fig.add_trace(go.Scatter(
                    x=buy_signals.index, y=buy_signals['Close']*0.98,
                    mode='markers', marker_symbol='triangle-up', marker_color='#10b981', marker_size=10,
                    name='Buy Signal'
                ))
                
                # Add Sell Markers
                sell_signals = full_data.loc[signals == -1]
                fig.add_trace(go.Scatter(
                    x=sell_signals.index, y=sell_signals['Close']*1.02,
                    mode='markers', marker_symbol='triangle-down', marker_color='#ef4444', marker_size=10,
                    name='Sell Signal'
                ))
                
                fig.update_layout(
                    title=f"{selected_ticker} Price Action",
                    xaxis_title="Date", yaxis_title="Price",
                    template="plotly_dark",
                    paper_bgcolor=THEME['component_bg'],
                    plot_bgcolor=THEME['chart_bg'],
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

        # B. Equity Chart
        with tab_equity:
            fig_eq = go.Figure()
            
            # Portfolio Equity
            port_equity = results['Portfolio']['visuals']['equity']
            fig_eq.add_trace(go.Scatter(
                x=port_equity.index, y=port_equity,
                mode='lines', name='Strategy Portfolio',
                line=dict(color=THEME['accent_color'], width=2)
            ))
            
            # Benchmark Equity (Normalized to Portfolio Initial Capital)
            if not benchmark_data.empty:
                bench_norm = (benchmark_data / benchmark_data.iloc[0]) * initial_capital
                # Reindex to match portfolio dates
                bench_norm = bench_norm.reindex(port_equity.index).ffill()
                fig_eq.add_trace(go.Scatter(
                    x=bench_norm.index, y=bench_norm,
                    mode='lines', name=f'Benchmark ({benchmark_ticker})',
                    line=dict(color='#94a3b8', width=1, dash='dash')
                ))
                
            fig_eq.update_layout(
                title="Portfolio Equity Curve vs Benchmark",
                template="plotly_dark",
                paper_bgcolor=THEME['component_bg'],
                plot_bgcolor=THEME['chart_bg'],
                height=500
            )
            st.plotly_chart(fig_eq, use_container_width=True)

        # C. Drawdown Chart
        with tab_drawdown:
            dd_series = results['Portfolio']['visuals']['drawdown']
            fig_dd = px.area(
                x=dd_series.index, y=dd_series * 100, # Convert to %
                title="Portfolio Drawdown (%)",
                labels={'x': 'Date', 'y': 'Drawdown %'},
                color_discrete_sequence=[THEME['danger_color']]
            )
            fig_dd.update_layout(
                template="plotly_dark",
                paper_bgcolor=THEME['component_bg'],
                plot_bgcolor=THEME['chart_bg']
            )
            st.plotly_chart(fig_dd, use_container_width=True)
            
        # D. Distribution
        with tab_dist:
            # Calculate daily returns from equity
            daily_rets = port_equity.pct_change().dropna()
            fig_dist = px.histogram(
                daily_rets, nbins=50, 
                title="Return Distribution",
                labels={'value': 'Daily Return'},
                color_discrete_sequence=[THEME['accent_color']]
            )
            fig_dist.update_layout(template="plotly_dark", paper_bgcolor=THEME['component_bg'], plot_bgcolor=THEME['chart_bg'])
            st.plotly_chart(fig_dist, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Skewness", f"{daily_rets.skew():.2f}")
            col2.metric("Kurtosis", f"{daily_rets.kurtosis():.2f}")
            col3.metric("VaR (95%)", f"{np.percentile(daily_rets, 5):.2%}")

        # E. Comparison
        with tab_compare:
            st.markdown("### Scenario Analysis")
            all_runs = list(st.session_state['runs'].keys())
            if len(all_runs) > 1:
                run_a = st.selectbox("Baseline Run", all_runs, index=0)
                run_b = st.selectbox("Comparison Run", all_runs, index=min(1, len(all_runs)-1))
                
                res_a = st.session_state['runs'][run_a]['results']['Portfolio']['metrics']
                res_b = st.session_state['runs'][run_b]['results']['Portfolio']['metrics']
                
                comp_df = pd.DataFrame([res_a, res_b], index=[run_a, run_b]).T
                st.table(comp_df)
            else:
                st.info("Run another analysis to compare scenarios.")

        st.markdown("---")

        # --- 3. ANALYTICS TABLES ---
        st.markdown("### Detailed Performance Analysis")
        
        # Prepare DataFrame for all assets in the universe of this run
        perf_data = []
        for t in config['tickers']:
            if t in results:
                m = results[t]['metrics']
                m['Ticker'] = t
                perf_data.append(m)
                
        # Add Portfolio row
        port_m = results['Portfolio']['metrics']
        port_m['Ticker'] = "PORTFOLIO"
        perf_data.append(port_m)
        
        perf_df = pd.DataFrame(perf_data).set_index("Ticker")
        
        # Formatting
        format_mapping = {
            'Total Return': "{:.2%}", 'CAGR': "{:.2%}", 'Volatility': "{:.2%}",
            'Sharpe Ratio': "{:.2f}", 'Sortino Ratio': "{:.2f}", 'Max Drawdown': "{:.2%}",
            'Win Rate': "{:.2%}", 'Profit Factor': "{:.2f}"
        }
        
        st.dataframe(
            perf_df.style.format(format_mapping).background_gradient(cmap='RdYlGn', subset=['Total Return', 'Sharpe Ratio']),
            use_container_width=True
        )

    elif not run_pressed:
        st.info("👈 Configure your strategy in the sidebar and click 'RUN ANALYSIS' to begin.")
        
        # Landing Page Teaser
        st.markdown("""
        ### Welcome to the Institutional Quant Engine
        
        **Capabilities:**
        *   **Multi-Asset Backtesting:** Simulate portfolios across equities, crypto, and ETFs.
        *   **Advanced Risk Metrics:** Analyze VaR, Sharpe, Sortino, and Tail Risk.
        *   **Scenario Management:** Compare different strategies and parameter sets side-by-side.
        *   **Institutional Visualization:** Professional-grade charting and reporting.
        """)
