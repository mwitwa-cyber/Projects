# backend/app/services/actuarial/cm2_portfolio.py
"""
CM2 Module: Investment Performance & Risk

Robust implementation of Modern Portfolio Theory, risk metrics, and optimizer
with adjustments for frontier markets. Includes type hints, docstrings, and error handling.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import minimize
from scipy.stats import norm


@dataclass
class PortfolioMetrics:
    """
    Container for portfolio performance metrics.
    Attributes:
        expected_return (float): Portfolio expected return
        volatility (float): Portfolio volatility
        sharpe_ratio (float): Sharpe ratio
        weights (Dict[str, float]): Asset weights
    """
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: Dict[str, float]


class CovarianceEstimator:
    """
    Covariance matrix estimation with frontier market adjustments.
    """
    @staticmethod
    def ledoit_wolf_shrinkage(returns: pd.DataFrame) -> np.ndarray:
        """
        Ledoit-Wolf shrinkage estimator: Σ_shrunk = δF + (1-δ)S
        Args:
            returns (pd.DataFrame): Asset returns
        Returns:
            np.ndarray: Shrunk covariance matrix
        """
        if returns.empty:
            raise ValueError("Returns DataFrame is empty.")
        S = returns.cov().values
        n, p = returns.shape
        mean_var = np.trace(S) / p
        F = mean_var * np.eye(p)
        delta = min(1.0, (n - 2) / (n * (p + 1))) if n > 2 else 1.0
        Sigma = delta * F + (1 - delta) * S
        return Sigma

    @staticmethod
    def nearest_correlation_matrix(cov_matrix: np.ndarray) -> np.ndarray:
        """
        Higham's algorithm for nearest PSD matrix
        Args:
            cov_matrix (np.ndarray): Covariance matrix
        Returns:
            np.ndarray: Nearest positive semi-definite covariance matrix
        """
        std_devs = np.sqrt(np.diag(cov_matrix))
        outer_std = np.outer(std_devs, std_devs)
        corr = cov_matrix / outer_std
        eigenvalues, eigenvectors = np.linalg.eigh(corr)
        eigenvalues[eigenvalues < 0] = 1e-6
        corr_fixed = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        cov_fixed = corr_fixed * outer_std
        return cov_fixed

class BetaEstimator:
    """Beta estimation with adjustments for thin trading."""
    
    @staticmethod
    def standard_beta(
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> float:
        """Standard OLS beta: β = Cov(R_i, R_m) / Var(R_m)"""
        covariance = asset_returns.cov(market_returns)
        market_variance = market_returns.var()
        return covariance / market_variance
    
    @staticmethod
    def scholes_williams_beta(
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> float:
        """Scholes-Williams adjusted beta for thin trading"""
        df = pd.DataFrame({
            'asset': asset_returns,
            'market': market_returns
        }).dropna()
        
        # Three regressions
        beta_0 = BetaEstimator.standard_beta(df['asset'], df['market'])
        beta_lag = df['asset'].cov(df['market'].shift(1)) / df['market'].shift(1).var()
        beta_lead = df['asset'].cov(df['market'].shift(-1)) / df['market'].shift(-1).var()
        
        # Market autocorrelation
        rho_m = df['market'].autocorr(lag=1)
        
        # Adjusted beta
        beta_sw = (beta_lag + beta_0 + beta_lead) / (1 + 2 * rho_m)
        return beta_sw


class PortfolioOptimizer:
    """Modern Portfolio Theory optimization."""
    
    def __init__(
        self,
        returns: pd.DataFrame,
        risk_free_rate: float = 0.20
    ):
        self.returns = returns
        self.risk_free_rate = risk_free_rate
        self.mean_returns = returns.mean()
        self.cov_matrix = CovarianceEstimator.ledoit_wolf_shrinkage(returns)
        self.n_assets = len(returns.columns)
    
    def portfolio_performance(
        self,
        weights: np.ndarray
    ) -> Tuple[float, float, float]:
        """Calculate portfolio return, volatility, and Sharpe ratio"""
        returns = np.dot(weights, self.mean_returns)
        volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        sharpe = (returns - self.risk_free_rate) / volatility
        return returns, volatility, sharpe
    
    def max_sharpe_ratio(self) -> PortfolioMetrics:
        """Maximize Sharpe ratio (Tangency Portfolio)"""
        def neg_sharpe(weights):
            ret, vol, sharpe = self.portfolio_performance(weights)
            return -sharpe
        
        cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        init_weights = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            neg_sharpe,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        if not result.success:
            raise ValueError("Optimization failed to converge")
        
        optimal_weights = result.x
        ret, vol, sharpe = self.portfolio_performance(optimal_weights)
        
        return PortfolioMetrics(
            expected_return=ret,
            volatility=vol,
            sharpe_ratio=sharpe,
            weights={asset: w for asset, w in zip(self.returns.columns, optimal_weights)}
        )
    
    def min_volatility(
        self,
        target_return: Optional[float] = None
    ) -> PortfolioMetrics:
        """Minimize portfolio volatility"""
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(self.cov_matrix, weights))
        
        cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        
        if target_return is not None:
            cons.append({
                'type': 'eq',
                'fun': lambda w: np.dot(w, self.mean_returns) - target_return
            })
        
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        init_weights = np.array([1/self.n_assets] * self.n_assets)
        
        result = minimize(
            portfolio_variance,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        if not result.success:
            raise ValueError("Optimization failed")
        
        optimal_weights = result.x
        ret, vol, sharpe = self.portfolio_performance(optimal_weights)
        
        return PortfolioMetrics(
            expected_return=ret,
            volatility=vol,
            sharpe_ratio=sharpe,
            weights={asset: w for asset, w in zip(self.returns.columns, optimal_weights)}
        )
    
    def efficient_frontier(
        self,
        n_points: int = 100
    ) -> List[Tuple[float, float]]:
        """Generate efficient frontier points"""
        min_ret = self.mean_returns.min()
        max_ret = self.mean_returns.max()
        target_returns = np.linspace(min_ret, max_ret, n_points)
        
        frontier = []
        for target in target_returns:
            try:
                metrics = self.min_volatility(target_return=target)
                frontier.append((metrics.volatility, metrics.expected_return))
            except ValueError:
                continue
        
        return frontier


class RiskMetrics:
    """Risk measurement tools."""
    
    @staticmethod
    def value_at_risk(
        returns: pd.Series,
        confidence_level: float = 0.99,
        method: str = "historical"
    ) -> float:
        """Calculate Value at Risk (VaR)"""
        if method == "historical":
            var = np.percentile(returns, (1 - confidence_level) * 100)
        elif method == "parametric":
            mean = returns.mean()
            std = returns.std()
            z_score = norm.ppf(1 - confidence_level)
            var = mean + z_score * std
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return -var
    
    @staticmethod
    def conditional_var(
        returns: pd.Series,
        confidence_level: float = 0.99
    ) -> float:
        """Calculate CVaR (Expected Shortfall)"""
        var = RiskMetrics.value_at_risk(returns, confidence_level, "historical")
        threshold = -var
        tail_losses = returns[returns <= threshold]
        
        if len(tail_losses) == 0:
            return var
        
        return -tail_losses.mean()
    
    @staticmethod
    def tracking_error(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """Calculate tracking error: TE = std(R_p - R_b)"""
        active_returns = portfolio_returns - benchmark_returns
        return active_returns.std()
