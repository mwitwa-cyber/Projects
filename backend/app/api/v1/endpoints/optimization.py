"""Portfolio optimization endpoints - CM2 module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from app.services.actuarial import PortfolioOptimizer, RiskMetrics

router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request model for portfolio optimization."""
    returns_data: Dict[str, List[float]] = Field(..., description="Asset returns as dict")
    objective: str = Field("max_sharpe", description="Optimization objective")
    risk_free_rate: float = Field(0.20, description="Risk-free rate")
    target_return: Optional[float] = Field(None, description="Target return for min-vol")


class PortfolioWeightsResponse(BaseModel):
    """Portfolio weights response."""
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    objective: str


class EfficientFrontierRequest(BaseModel):
    """Request for efficient frontier generation."""
    returns_data: Dict[str, List[float]]
    risk_free_rate: float = Field(0.20)
    n_points: int = Field(50, ge=10, le=200)


@router.post("/optimize", response_model=PortfolioWeightsResponse)
async def optimize_portfolio(request: OptimizationRequest):
    """
    Optimize portfolio using Modern Portfolio Theory.
    
    Objectives:
    - max_sharpe: Maximize Sharpe ratio (Tangency Portfolio)
    - min_vol: Minimize volatility
    - equal_weight: Equal weight allocation
    """
    try:
        # Convert to DataFrame
        returns_df = pd.DataFrame(request.returns_data)
        
        if returns_df.empty or len(returns_df) < 2:
            raise ValueError("Insufficient return data provided")
        
        # Handle equal weight separately (no optimization needed)
        if request.objective == "equal_weight":
            n_assets = len(returns_df.columns)
            equal_weights = {col: 1.0 / n_assets for col in returns_df.columns}
            
            # Calculate metrics for equal weight portfolio
            mean_returns = returns_df.mean()
            cov_matrix = returns_df.cov()
            weights_array = np.array([equal_weights[col] for col in returns_df.columns])
            
            port_return = np.dot(weights_array, mean_returns)
            port_vol = np.sqrt(np.dot(weights_array.T, np.dot(cov_matrix, weights_array)))
            sharpe = (port_return - request.risk_free_rate) / port_vol if port_vol > 0 else 0
            
            return PortfolioWeightsResponse(
                weights={k: round(v, 4) for k, v in equal_weights.items()},
                expected_return=round(float(port_return), 6),
                volatility=round(float(port_vol), 6),
                sharpe_ratio=round(float(sharpe), 4),
                objective=request.objective
            )
        
        # Initialize optimizer
        optimizer = PortfolioOptimizer(
            returns=returns_df,
            risk_free_rate=request.risk_free_rate
        )
        
        # Optimize based on objective
        if request.objective == "max_sharpe":
            result = optimizer.max_sharpe_ratio()
        elif request.objective == "min_vol":
            result = optimizer.min_volatility(target_return=request.target_return)
        else:
            raise ValueError(f"Unknown objective: {request.objective}")
        
        return PortfolioWeightsResponse(
            weights={k: round(v, 4) for k, v in result.weights.items()},
            expected_return=round(result.expected_return, 6),
            volatility=round(result.volatility, 6),
            sharpe_ratio=round(result.sharpe_ratio, 4),
            objective=request.objective
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/efficient-frontier")
async def generate_frontier(request: EfficientFrontierRequest):
    """Generate efficient frontier points."""
    try:
        returns_df = pd.DataFrame(request.returns_data)
        
        if returns_df.empty:
            raise ValueError("No return data provided")
        
        optimizer = PortfolioOptimizer(
            returns=returns_df,
            risk_free_rate=request.risk_free_rate
        )
        
        frontier = optimizer.efficient_frontier(n_points=request.n_points)
        
        return {
            "frontier": [
                {"volatility": round(vol, 6), "return": round(ret, 6)}
                for vol, ret in frontier
            ],
            "n_points": len(frontier),
            "assets": list(returns_df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


from fastapi import Query, Body
from pydantic import BaseModel, Field

class VaRRequest(BaseModel):
    returns: List[float] = Field(..., description="Return series")
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.99, description="Confidence level")
    method: str = Field(default="historical", description="VaR method: historical, parametric, or monte_carlo")

@router.post("/risk/var")
async def calculate_var(request: VaRRequest):
    """Calculate Value at Risk (VaR)."""
    try:
        returns_series = pd.Series(request.returns)
        
        if len(returns_series) < 30:
            raise ValueError("Minimum 30 observations required for VaR")
        
        var = RiskMetrics.value_at_risk(
            returns_series,
            confidence_level=request.confidence_level,
            method=request.method
        )
        
        return {
            "var": round(var, 6),
            "var_value": round(var, 6),
            "confidence_level": request.confidence_level,
            "method": request.method,
            "interpretation": f"{request.confidence_level*100}% confidence that loss will not exceed {var:.2%}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CVaRRequest(BaseModel):
    returns: List[float] = Field(..., description="Return series")
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.99, description="Confidence level")
    method: str = Field(default="historical", description="CVaR method: historical or parametric")

@router.post("/risk/cvar")
async def calculate_cvar(request: CVaRRequest):
    """Calculate Conditional VaR (Expected Shortfall)."""
    try:
        returns_series = pd.Series(request.returns)
        
        if len(returns_series) < 30:
            raise ValueError("Minimum 30 observations required")
        
        cvar = RiskMetrics.conditional_var(
            returns_series,
            confidence_level=request.confidence_level
        )
        
        var = RiskMetrics.value_at_risk(
            returns_series,
            confidence_level=request.confidence_level,
            method="historical"
        )
        
        return {
            "cvar": round(cvar, 6),
            "cvar_value": round(cvar, 6),
            "var": round(var, 6),
            "confidence_level": request.confidence_level,
            "interpretation": f"Expected loss when loss exceeds VaR: {cvar:.2%}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/beta")
async def calculate_beta(
    asset_returns: List[float] = Body(..., description="Asset returns"),
    market_returns: List[float] = Body(..., description="Market returns"),
    method: str = Query("scholes_williams", description="Beta calculation method")
):
    """
    Calculate beta coefficient.
    
    Methods:
    - standard: OLS beta
    - scholes_williams: Adjusted for thin trading
    """
    try:
        from app.services.actuarial import BetaEstimator
        
        asset_series = pd.Series(asset_returns)
        market_series = pd.Series(market_returns)
        
        if len(asset_series) != len(market_series):
            raise ValueError("Asset and market returns must have same length")
        
        if len(asset_series) < 30:
            raise ValueError("Minimum 30 observations required for beta")
        
        if method == "standard":
            beta = BetaEstimator.standard_beta(asset_series, market_series)
        elif method == "scholes_williams":
            beta = BetaEstimator.scholes_williams_beta(asset_series, market_series)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return {
            "beta": round(beta, 4),
            "method": method,
            "interpretation": (
                "High systematic risk" if beta > 1.2
                else "Low systematic risk" if beta < 0.8
                else "Market-level risk"
            )
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
