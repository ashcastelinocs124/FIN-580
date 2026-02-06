import pandas as pd
import numpy as np
from enum import Enum
from indicators import calculate_atr

class SafetyState(Enum):
    NORMAL = "Normal"
    RISK_OFF = "Risk Off"
    COOLDOWN = "Cooldown"

class SafetySwitch:
    """
    Manages the risk state of the portfolio.
    Implements a State Machine: NORMAL -> RISK_OFF -> COOLDOWN -> NORMAL.
    """
    def __init__(self, atr_window=14, volatility_threshold=3.0, drawdown_threshold=0.15, cooldown_period=20):
        self.atr_window = atr_window
        self.vol_thresh_mult = volatility_threshold # Multiplier of "normal" volatility
        self.dd_limit = drawdown_threshold
        self.cooldown_bar_count = cooldown_period
        
        self.state = SafetyState.NORMAL
        self.days_in_state = 0
        self.baseline_atr = None

    def update(self, current_bar, current_idx, full_data):
        """
        Updates the safety state based on current market conditions.
        Crucial: ONLY uses data available up to current_idx.
        """
        # Calculate context
        if current_idx < 50: # Warmup
            return 1.0

        # Calculate dynamic volatility baseline (using long window)
        # We simulate "what we knew then" by looking back
        # Ideally passed in, but for simplicity we calculate on slice
        # Optimization: Pre-calculate these columns in Backtester
        
        # Check Triggers
        triggers = False
        
        # 1. Volatility Trigger
        current_atr = current_bar['atr']
        long_term_atr = p_atr = full_data['atr'].iloc[current_idx-50:current_idx].mean() # proxy for baseline
        
        if current_atr > (long_term_atr * self.vol_thresh_mult):
            triggers = True
            
        # 2. Crash Trigger (Drop from recent high)
        recent_high = full_data['close'].iloc[current_idx-20:current_idx].max()
        current_dd = (recent_high - current_bar['close']) / recent_high
        if current_dd > self.dd_limit:
            triggers = True

        # State Transitions
        if self.state == SafetyState.NORMAL:
            if triggers:
                self.state = SafetyState.RISK_OFF
                self.days_in_state = 0
                
        elif self.state == SafetyState.RISK_OFF:
            # Stay in Risk Off until triggers clear? 
            # Simplified: Stay for fixed time or untill Volatility subsides
            if not triggers:
                self.state = SafetyState.COOLDOWN
                self.days_in_state = 0
                
        elif self.state == SafetyState.COOLDOWN:
            self.days_in_state += 1
            if self.days_in_state >= self.cooldown_bar_count:
                self.state = SafetyState.NORMAL
                self.days_in_state = 0

        # Return Exposure Multiplier
        if self.state == SafetyState.RISK_OFF:
            return 0.0
        elif self.state == SafetyState.COOLDOWN:
            return 0.5 # Partial exposure
        else:
            return 1.0

def execute_strategy(price_data: pd.DataFrame, signal_data: pd.DataFrame, use_safety_switch=True) -> pd.DataFrame:
    """
    Simulates execution with strict lookahead bias prevention.
    """
    df = price_data.copy()
    
    # 1. Merge Signals (and Indicators)
    # We want to keep any extra columns from signal_data (like 'fast_sma', 'upper', etc.)
    new_cols = signal_data.columns.difference(df.columns)
    df = pd.concat([df, signal_data[new_cols]], axis=1)
    
    # Ensure raw_signal exists (it should be in signal_data)
    if 'signal' in df.columns:
        df['raw_signal'] = df['signal']
    else:
        # Fallback if signal wasn't merged for some reason
        df['raw_signal'] = signal_data['signal']
    
    # 2. Strict Shift: Decision at T affects position at T+1
    df['position_target'] = df['raw_signal'].shift(1).fillna(0)
    
    # 3. Calculate Volatility for Safety Switch
    if use_safety_switch:
        df['atr'] = calculate_atr(df['high'], df['low'], df['close'], 14)
        safety = SafetySwitch()
        safety_multipliers = []
        safety_states = []
        
        # Iterative loop needed for SafetySwitch state dependence
        # (Vectorization hard for state machines)
        for i in range(len(df)):
            if i < 50: 
                safety_multipliers.append(1.0)
                safety_states.append("Warmup")
                continue
                
            bar = df.iloc[i]
            mult = safety.update(bar, i, df)
            safety_multipliers.append(mult)
            safety_states.append(safety.state.value)
            
        df['safety_mult'] = safety_multipliers
        df['safety_state'] = safety_states
        
        # Apply Safety Switch to decision made YESTERDAY (which executes TODAY)
        # Actually, if we are in RISK_OFF today, we sell today. 
        # So we modify the position target for today based on today's safety state?
        # No, Safety Switch triggers at Close T. So T+1 we are out.
        # The loop above calculates state at T.
        # So we shift safety multiplier too.
        
        df['safety_mult_applied'] = df['safety_mult'].shift(1).fillna(1.0)
        df['position_final'] = df['position_target'] * df['safety_mult_applied']
        
    else:
        df['position_final'] = df['position_target']
        df['safety_state'] = "Disabled"
    
    # 4. Calculate Returns
    df['market_return'] = df['close'].pct_change()
    df['strategy_return'] = df['market_return'] * df['position_final'].shift(1) # Position held from T allows capturing return at T -> Wait.
    # Standard: Position determined at T (close) or T+1 (open).
    # Here: 'position_final' is the position we wake up with at T.
    # If we shift signal(1), then signal at T-1 becomes position at T.
    # Return at T is (Close_T - Close_T-1) / Close_T-1 * Position_T.
    # So: strategy_return = market_return * position_final.
    
    # Let's verify:
    # T=0: Signal=1.
    # T=1: position_target = Signal(T=0) = 1.
    #      market_ret = (C1-C0)/C0.
    #      If we bought at C0, we get this return.
    #      So returns = market_return * position_target.
    
    # BUT wait, the vector shift above:
    # df['position_target'] = df['raw_signal'].shift(1)
    # Row T has position from T-1.
    # Row T has market_return (T vs T-1).
    # So yes, direct multiplication works.
    
    df['strategy_return'] = df['market_return'] * df['position_final']
    
    # 5. Equity Curve
    df['equity'] = (1 + df['strategy_return'].fillna(0)).cumprod()
    df['drawdown'] = df['equity'] / df['equity'].cummax() - 1
    
    return df
