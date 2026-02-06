import streamlit as st
import yfinance as yf
import pandas as pd
from duckduckgo_search import DDGS
from textblob import TextBlob
import plotly.graph_objects as go
import time

def analyst_agent():
    """
    Analyst Agent: Searches for FOMC headlines and determines Hawkish/Dovish tilt.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("FOMC Federal Reserve news headlines", max_results=5))
        
        if not results:
            return "No recent FOMC news found.", 0.0, []

        headlines = [r['title'] for r in results]
        combined_text = " ".join(headlines).lower()
        
        # Simple Keyword scoring
        hawkish_terms = ["hike", "raise", "tighten", "inflation", "hawkish", "aggressive"]
        dovish_terms = ["cut", "lower", "ease", "stimulus", "dovish", "soft landing", "pause"]
        
        hawk_score = sum(combined_text.count(t) for t in hawkish_terms)
        dove_score = sum(combined_text.count(t) for t in dovish_terms)
        
        # TextBlob for general sentiment context
        blob_score = TextBlob(combined_text).sentiment.polarity
        
        if hawk_score > dove_score:
            tilt = "Hawkish 🦅"
            score = -0.5 # Negative for risk assets
            summary = f"Detected {hawk_score} hawkish terms vs {dove_score} dovish terms. Sentiment leans Hawkish."
        elif dove_score > hawk_score:
            tilt = "Dovish 🕊️"
            score = 0.5 # Positive for risk assets
            summary = f"Detected {dove_score} dovish terms vs {hawk_score} hawkish terms. Sentiment leans Dovish."
        else:
            tilt = "Neutral ⚖️"
            score = 0.0
            summary = "Balanced flow of news. No strong directional tilt detected."
            
        return f"**{tilt}**: {summary}", score, headlines
        
    except Exception as e:
        return f"Error grabbing news: {str(e)}", 0.0, []

def quant_agent(ticker="SPY"):
    """
    Quant Agent: Calculates 200-day MA for SPY via yfinance.
    """
    try:
        data = yf.download(ticker, period="1y", progress=False)
        if data.empty:
             return "No data found for SPY.", 0.0, 0, 0

        # Create copy to avoid slice warnings
        df = data[["Close"]].copy() 
        df["MA_200"] = df["Close"].rolling(window=200).mean()
        
        last_close = float(df["Close"].iloc[-1])
        last_ma = float(df["MA_200"].iloc[-1])
        
        if pd.isna(last_ma):
             return "Not enough data for 200MA.", 0.0, last_close, 0
        
        diff_pct = (last_close - last_ma) / last_ma
        
        if last_close > last_ma:
            trend = "Bullish 🐂"
            score = 0.8  # Strong buy signal context
            summary = f"Price (${last_close:.2f}) is **ABOVE** the 200-day MA (${last_ma:.2f}) by {diff_pct:.1%}."
        else:
            trend = "Bearish 🐻"
            score = -0.8 # Sell signal
            summary = f"Price (${last_close:.2f}) is **BELOW** the 200-day MA (${last_ma:.2f}) by {diff_pct:.1%}."
            
        return f"**{trend}**: {summary}", score, last_close, last_ma
        
    except Exception as e:
        return f"Quant computation failed: {str(e)}", 0.0, 0, 0

def risk_guardian():
    """
    Risk Guardian: Searches for Black Swan terms.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("global geopolitical crisis war conflict breaking news", max_results=5))
            
        if not results:
             return "No risk news found (Good news?).", 0.0, []

        headlines = [r['title'] for r in results]
        combined_text = " ".join(headlines).lower()
        
        risk_terms = ["war", "invasion", "nuclear", "terrorism", "collapse", "pandemic", "lockdown", "crisis"]
        
        risk_hits = [t for t in risk_terms if t in combined_text]
        risk_count = len(risk_hits)
        
        if risk_count > 2:
            status = "Elevated Risk ⚠️"
            score = -0.9 # High danger
            summary = f"Detected {risk_count} potential Black Swan triggers: {', '.join(risk_hits)}."
        elif risk_count > 0:
            status = "Moderate Caution ✋"
            score = -0.3
            summary = f"Some geopolitical mentions found: {', '.join(risk_hits)}."
        else:
            status = "Stable 🛡️"
            score = 0.2 # Slight positive bias for stability
            summary = "No immediate 'Black Swan' keywords found in top headlines."
            
        return f"**{status}**: {summary}", score, headlines

    except Exception as e:
        return f"Risk check failed: {str(e)}", 0.0, []

def render_war_room():
    st.markdown("## 🌍 Global Macro War Room")
    
    # 1. Trigger Buttons to Simulate Agents
    col_btn, col_status = st.columns([1, 4])
    with col_btn:
        run_agents = st.button("🚨 CONVENE WAR ROOM", type="primary", use_container_width=True)
    
    if run_agents:
        with st.status("📡 Connecting to Global Nodes...", expanded=True) as status:
            
            st.write("🕵️ **Analyst Agent** is scanning FOMC wires...")
            analyst_msg, analyst_score, analyst_data = analyst_agent()
            time.sleep(1) # Dramatic pause
            
            st.write("🔢 **Quant Agent** is crunching $SPY algorithms...")
            quant_msg, quant_score, quant_data, quant_ma = quant_agent()
            time.sleep(1)
            
            st.write("🛡️ **Risk Guardian** is sweeping for Black Swans...")
            risk_msg, risk_score, risk_data = risk_guardian()
            time.sleep(1)
            
            status.update(label="✅ Agents have reported in!", state="complete", expanded=False)
        
        # Store in session state to persist
        st.session_state['war_room_results'] = {
            'analyst': (analyst_msg, analyst_score, analyst_data),
            'quant': (quant_msg, quant_score, quant_data, quant_ma),
            'risk': (risk_msg, risk_score, risk_data)
        }
    
    # Render UI if results exist
    if 'war_room_results' in st.session_state:
        results = st.session_state['war_room_results']
        
        # Unpack
        a_msg, a_score, a_data = results['analyst']
        q_msg, q_score, q_data, q_ma = results['quant']
        r_msg, r_score, r_data = results['risk']
        
        # --- 2. THE CHAT TRANSCRIPT ---
        st.markdown("### 💬 Agent Consensus Protocol")
        
        chat_container = st.container()
        with chat_container:
            # Render chat bubbles
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #3b82f6;">
                <strong>🕵️ Analyst Agent:</strong> <br> {a_msg}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #8b5cf6;">
                <strong>🔢 Quant Agent:</strong> <br> {q_msg}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #ef4444;">
                <strong>🛡️ Risk Guardian:</strong> <br> {r_msg}
            </div>
            """, unsafe_allow_html=True)

        # --- 3. DECISION CONSOLE & GAUGE ---
        st.markdown("---")
        st.markdown("### 🎛️ Decision Console")
        
        # Calculate Consensus
        # Scores: -1 (Bearish) to +1 (Bullish) roughly
        # Total Score [-3 to 3] -> Map to 0-100%
        # Analyst score (-0.5 to 0.5)
        # Quant score (-0.8 to 0.8)
        # Risk score (-0.9 to 0.2)
        
        total_score = a_score + q_score + r_score
        # Max possible roughly: 0.5 + 0.8 + 0.2 = 1.5
        # Min possible roughly: -0.5 - 0.8 - 0.9 = -2.2
        # Normalize to 0-100 (50 is neutral)
        
        # Simple map: 0 score = 50%. +1.5 = 100%. -1.5 = 0%
        confidence = 50 + (total_score * 33) 
        confidence = max(0, min(100, confidence))
        
        # Determine Agreement
        # Disagree if signs are mixed?
        # A simple disagreement check: if one is strongly positive (>0.3) and another strongly negative (<-0.3)
        scores = [a_score, q_score, r_score]
        bulls = [s for s in scores if s > 0.3]
        bears = [s for s in scores if s < -0.3]
        
        disagreement = len(bulls) > 0 and len(bears) > 0
        
        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = confidence,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Confidence Gauge (3D)", 'font': {'size': 24, 'color': "white"}},
            number = {'suffix': "%", 'font': {'color': "white"}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "rgba(0,0,0,0)"}, # Hide default bar, use threshold or steps
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 40], 'color': '#ef4444'},
                    {'range': [40, 60], 'color': 'gray'},
                    {'range': [60, 100], 'color': '#10b981'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': confidence
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor = "#0f172a",
            font = {'color': "white", 'family': "Inter"},
            height = 300
        )
        
        c1, c2 = st.columns([2, 1])
        with c1:
             st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown("#### Execution Status")
            if disagreement:
                st.warning("⚠️ AGENTS DISAGREE")
                st.caption("Positions conflict. Automatic execution disabled.")
                st.button("⛔ EXECUTE BLOCKED", disabled=True, use_container_width=True)
            else:
                st.success("✅ CONSENSUS REACHED")
                st.caption(f"Ready to execute with {confidence:.1f}% confidence.")
                if st.button("🚀 EXECUTE TRADES", type="primary", use_container_width=True):
                    st.toast("Orders sent to exchange!", icon="💸")

