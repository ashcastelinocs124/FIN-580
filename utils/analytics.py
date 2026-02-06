import numpy as np
import pandas as pd

def calculate_advanced_metrics(daily_returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> dict:
    """
    Calculates a comprehensive suite of risk and performance metrics.
    
    Args:
        daily_returns: Series of daily percentage returns.
        risk_free_rate: Annualized risk-free rate (decimal).
        periods_per_year: Trading days per year (default 252).
        
    Returns:
        Dictionary containing calculated metrics.
    """
    if daily_returns.empty:
        return {}

    # Basic Metrics
    total_return = (1 + daily_returns).prod() - 1
    cagr = (1 + total_return) ** (periods_per_year / len(daily_returns)) - 1
    volatility = daily_returns.std() * np.sqrt(periods_per_year)
    
    # Adjust for risk-free rate
    excess_returns = daily_returns - (risk_free_rate / periods_per_year)
    
    # Sharpe Ratio
    sharpe_ratio = 0.0
    if volatility > 0:
        sharpe_ratio = (daily_returns.mean() * periods_per_year - risk_free_rate) / volatility
        
    # Sortino Ratio
    downside_returns = daily_returns[daily_returns < 0]
    downside_volatility = downside_returns.std() * np.sqrt(periods_per_year)
    sortino_ratio = 0.0
    if downside_volatility > 0:
        sortino_ratio = (daily_returns.mean() * periods_per_year - risk_free_rate) / downside_volatility
        
    # Drawdown Metrics
    cumulative_returns = (1 + daily_returns).cumprod()
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min()
    
    # Calmar Ratio
    calmar_ratio = 0.0
    if max_drawdown < 0:
        calmar_ratio = cagr / abs(max_drawdown)
        
    # Value at Risk (VaR) & CVaR (Historical)
    var_95 = np.percentile(daily_returns, 5)
    cvar_95 = daily_returns[daily_returns <= var_95].mean()
    
    # Win Rate / Profit Factor
    wins = daily_returns[daily_returns > 0]
    losses = daily_returns[daily_returns < 0]
    win_rate = len(wins) / len(daily_returns) if len(daily_returns) > 0 else 0
    
    avg_win = wins.mean() if not wins.empty else 0
    avg_loss = losses.mean() if not losses.empty else 0
    profit_factor = abs(wins.sum() / losses.sum()) if not losses.empty and losses.sum() != 0 else np.inf

    return {
        "Total Return": total_return,
        "CAGR": cagr,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe_ratio,
        "Sortino Ratio": sortino_ratio,
        "Max Drawdown": max_drawdown,
        "Calmar Ratio": calmar_ratio,
        "VaR 95%": var_95,
        "CVaR 95%": cvar_95,
        "Win Rate": win_rate,
        "Profit Factor": profit_factor,
        "Avg Win": avg_win,
        "Avg Loss": avg_loss
    }

def calculate_drawdown_series(daily_returns: pd.Series) -> pd.Series:
    """Returns the drawdown series for plotting."""
    cum_rets = (1 + daily_returns).cumprod()
    peak = cum_rets.cummax()
    return (cum_rets - peak) / peak
