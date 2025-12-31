
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import date

@dataclass
class BacktestResult:
    equity_curve: List[Dict[str, float]] # [{"date": "2023-01-01", "value": 1000}, ...]
    metrics: Dict[str, float]
    holdings_history: List[Dict[str, float]] # Optional: daily holdings

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital

    def run_backtest(
        self,
        prices: pd.DataFrame, # Columns = Tickers, Index = Date
        weights: Dict[str, float],
    ) -> BacktestResult:
        """
        Run a static weight backtest.
        Assumes daily rebalancing or buy-and-hold? 
        Let's implement Buy-and-Hold (Fixed Initial Quantity) for simplicity first, 
        or Daily Rebalancing (Fixed Weights).
        
        The plan implied "Fixed Weights" usually means rebalancing. 
        However, for simplicity and typical user expectation of "What if I invested X", 
        Buy-and-Hold is often the default. 
        BUT, 'Optimization' outputs weights. So let's stick to Fixed Weights (Daily Rebalancing) 
        as it's mathematically cleaner for 'Strategy' verification, 
        OR implement both. Let's do **Daily Rebalancing** to match the weights strictly.
        """
        if prices.empty:
            raise ValueError("Price data is empty")
        
        # Ensure weights sum to 1 (normalize)
        total_weight = sum(weights.values())
        norm_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Filter prices to only include tickers in weights
        tickers = list(norm_weights.keys())
        available_tickers = [t for t in tickers if t in prices.columns]
        
        if not available_tickers:
            raise ValueError("No price data found for requested tickers")
            
        df = prices[available_tickers].copy()
        df = df.sort_index()
        
        # Calculate daily returns
        returns = df.pct_change().fillna(0)
        
        # Portfolio Daily Return = Sum(Weight_i * Return_i)
        # We assume rebalancing at the close of every day to maintain target weights.
        portfolio_returns = pd.Series(0.0, index=df.index)
        
        for ticker, weight in norm_weights.items():
            if ticker in returns.columns:
                portfolio_returns += returns[ticker] * weight
        
        # Calculate Cumulative Return (Equity Curve)
        # Equity_t = Equity_{t-1} * (1 + R_t)
        cumulative_returns = (1 + portfolio_returns).cumprod()
        equity_series = self.initial_capital * cumulative_returns
        
        # Metrics
        total_return = (equity_series.iloc[-1] / self.initial_capital) - 1
        
        # Annualized Volatility
        daily_vol = portfolio_returns.std()
        annual_vol = daily_vol * np.sqrt(252)
        
        # Sharpe Ratio (assuming Rf=0 for simplicity in backtest metrics usually, or small constant)
        # We can use the service defaults or just simple calculation here.
        risk_free_daily = 0.05 / 252 # approx 5% annual
        excess_returns = portfolio_returns - risk_free_daily
        sharpe_ratio = (excess_returns.mean() / daily_vol) * np.sqrt(252) if daily_vol > 0 else 0
        
        # Max Drawdown
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Format Results
        curve = []
        for dt, val in equity_series.items():
            curve.append({
                "time": dt.isoformat(), # lightweight-charts compatible
                "value": round(val, 2)
            })
            
        metrics = {
            "total_return": round(total_return, 4),
            "cagr": round((1 + total_return)**(252/len(df)) - 1, 4) if len(df) > 0 else 0,
            "volatility": round(annual_vol, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 4)
        }
        
        return BacktestResult(
            equity_curve=curve,
            metrics=metrics,
            holdings_history=[]
        )
