"""
TimescaleDB Risk Analytics Helper.

Provides optimized functions to call TimescaleDB's pre-built
risk calculation functions for VaR and Beta.

Usage:
    from app.services.timescale_risk import get_beta_from_db, get_var_from_db
    
    # Using database-optimized calculation
    beta_result = get_beta_from_db(db, asset_id=1, benchmark_id=2, lookback_weeks=52)
    var_result = get_var_from_db(db, asset_id=1, lookback_weeks=52)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ==================== Response Models ====================

class BetaResult(BaseModel):
    """Result from TimescaleDB beta calculation."""
    beta: float = Field(..., description="Beta coefficient")
    correlation: float = Field(..., description="Correlation with benchmark")
    observation_count: int = Field(..., description="Number of weekly observations")
    asset_volatility: float = Field(..., description="Annualized asset volatility")
    benchmark_volatility: float = Field(..., description="Annualized benchmark volatility")
    calculation_method: str = Field(default="timescaledb", description="Calculation method used")
    calculation_time: datetime = Field(default_factory=datetime.now, description="When calculated")


class VaRResult(BaseModel):
    """Result from TimescaleDB VaR calculation."""
    var_95: float = Field(..., description="95% VaR as percentage")
    cvar_95: Optional[float] = Field(None, description="Conditional VaR (Expected Shortfall)")
    observation_count: int = Field(..., description="Number of weekly observations")
    min_return: float = Field(..., description="Minimum weekly return observed")
    max_return: float = Field(..., description="Maximum weekly return observed")
    calculation_method: str = Field(default="timescaledb_historical", description="VaR method")
    calculation_time: datetime = Field(default_factory=datetime.now, description="When calculated")


class WeeklyObservation(BaseModel):
    """Single weekly observation with returns."""
    week_start: datetime
    asset_close: float
    benchmark_close: float
    asset_log_return: float
    benchmark_log_return: float


# ==================== Database Functions ====================

def get_weekly_observations(
    db: Session,
    asset_id: int,
    benchmark_id: int,
    lookback_weeks: int = 52
) -> List[WeeklyObservation]:
    """
    Fetch pre-calculated weekly observations from TimescaleDB.
    
    Uses the get_weekly_observations() SQL function which:
    - Resamples daily data to weekly
    - Forward-fills missing prices (LOCF)
    - Calculates log returns
    
    Args:
        db: SQLAlchemy session
        asset_id: Asset to analyze
        benchmark_id: Benchmark asset (e.g., LASI proxy)
        lookback_weeks: Historical period in weeks
        
    Returns:
        List of WeeklyObservation objects
    """
    query = text("""
        SELECT 
            week_start,
            asset_close,
            benchmark_close,
            asset_log_return,
            benchmark_log_return
        FROM get_weekly_observations(:asset_id, :benchmark_id, :lookback_weeks)
    """)
    
    result = db.execute(query, {
        "asset_id": asset_id,
        "benchmark_id": benchmark_id,
        "lookback_weeks": lookback_weeks
    })
    
    observations = [
        WeeklyObservation(
            week_start=row.week_start,
            asset_close=float(row.asset_close),
            benchmark_close=float(row.benchmark_close),
            asset_log_return=float(row.asset_log_return),
            benchmark_log_return=float(row.benchmark_log_return)
        )
        for row in result.fetchall()
    ]
    
    logger.debug(f"Fetched {len(observations)} weekly observations from TimescaleDB")
    return observations


def get_beta_from_db(
    db: Session,
    asset_id: int,
    benchmark_id: int,
    lookback_weeks: int = 52
) -> BetaResult:
    """
    Calculate Beta using TimescaleDB's optimized SQL function.
    
    This is faster than Python calculation for large datasets
    as the aggregation happens in the database.
    
    Args:
        db: SQLAlchemy session
        asset_id: Asset to analyze
        benchmark_id: Benchmark asset
        lookback_weeks: Historical period
        
    Returns:
        BetaResult with beta, correlation, and volatilities
        
    Raises:
        ValueError: If calculation fails or insufficient data
    """
    query = text("""
        SELECT 
            beta,
            correlation,
            observation_count,
            asset_volatility,
            benchmark_volatility
        FROM calculate_beta_sql(:asset_id, :benchmark_id, :lookback_weeks)
    """)
    
    result = db.execute(query, {
        "asset_id": asset_id,
        "benchmark_id": benchmark_id,
        "lookback_weeks": lookback_weeks
    }).fetchone()
    
    if result is None or result.observation_count < 10:
        raise ValueError(
            f"Insufficient data for beta calculation: "
            f"{result.observation_count if result else 0} observations"
        )
    
    beta_result = BetaResult(
        beta=float(result.beta) if result.beta else 0.0,
        correlation=float(result.correlation) if result.correlation else 0.0,
        observation_count=result.observation_count,
        asset_volatility=float(result.asset_volatility) if result.asset_volatility else 0.0,
        benchmark_volatility=float(result.benchmark_volatility) if result.benchmark_volatility else 0.0
    )
    
    logger.info(
        f"Calculated Beta from TimescaleDB: β={beta_result.beta:.4f}, "
        f"ρ={beta_result.correlation:.4f}, n={beta_result.observation_count}"
    )
    
    return beta_result


def get_var_from_db(
    db: Session,
    asset_id: int,
    lookback_weeks: int = 52,
    confidence: float = 0.95
) -> VaRResult:
    """
    Calculate VaR using TimescaleDB's optimized SQL function.
    
    Uses historical simulation (percentile of actual returns).
    
    Args:
        db: SQLAlchemy session
        asset_id: Asset to analyze
        lookback_weeks: Historical period
        confidence: Confidence level (default 95%)
        
    Returns:
        VaRResult with VaR, CVaR, and statistics
        
    Raises:
        ValueError: If calculation fails or insufficient data
    """
    query = text("""
        SELECT 
            var_95,
            cvar_95,
            observation_count,
            min_return,
            max_return
        FROM calculate_var_sql(:asset_id, :lookback_weeks, :confidence)
    """)
    
    result = db.execute(query, {
        "asset_id": asset_id,
        "lookback_weeks": lookback_weeks,
        "confidence": confidence
    }).fetchone()
    
    if result is None or result.observation_count < 10:
        raise ValueError(
            f"Insufficient data for VaR calculation: "
            f"{result.observation_count if result else 0} observations"
        )
    
    var_result = VaRResult(
        var_95=float(result.var_95) if result.var_95 else 0.0,
        cvar_95=float(result.cvar_95) if result.cvar_95 else None,
        observation_count=result.observation_count,
        min_return=float(result.min_return) if result.min_return else 0.0,
        max_return=float(result.max_return) if result.max_return else 0.0
    )
    
    logger.info(
        f"Calculated VaR from TimescaleDB: VaR(95%)={var_result.var_95:.4f}%, "
        f"n={var_result.observation_count}"
    )
    
    return var_result


def check_timescale_functions_exist(db: Session) -> Dict[str, bool]:
    """
    Check if the required TimescaleDB functions are installed.
    
    Returns:
        Dictionary with function names and their existence status
    """
    functions = [
        "get_weekly_observations",
        "calculate_beta_sql", 
        "calculate_var_sql"
    ]
    
    results = {}
    for func_name in functions:
        query = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc 
                WHERE proname = :func_name
            ) AS exists
        """)
        result = db.execute(query, {"func_name": func_name}).fetchone()
        results[func_name] = result.exists if result else False
    
    return results


# ==================== Hybrid Calculation ====================

def get_risk_metrics_hybrid(
    db: Session,
    asset_id: int,
    benchmark_id: int,
    lookback_weeks: int = 52,
    use_timescale: bool = True
) -> Dict[str, Any]:
    """
    Calculate risk metrics using TimescaleDB if available, 
    otherwise fall back to Python calculation.
    
    Args:
        db: SQLAlchemy session
        asset_id: Asset to analyze
        benchmark_id: Benchmark asset
        lookback_weeks: Historical period
        use_timescale: Whether to try TimescaleDB first
        
    Returns:
        Dictionary with beta, VaR, and metadata
    """
    if use_timescale:
        # Check if TimescaleDB functions exist
        func_status = check_timescale_functions_exist(db)
        
        if all(func_status.values()):
            logger.info("Using TimescaleDB-optimized risk calculations")
            try:
                beta_result = get_beta_from_db(db, asset_id, benchmark_id, lookback_weeks)
                var_result = get_var_from_db(db, asset_id, lookback_weeks)
                
                return {
                    "beta": beta_result.beta,
                    "correlation": beta_result.correlation,
                    "var_95": var_result.var_95,
                    "cvar_95": var_result.cvar_95,
                    "observation_count": beta_result.observation_count,
                    "asset_volatility": beta_result.asset_volatility,
                    "benchmark_volatility": beta_result.benchmark_volatility,
                    "calculation_method": "timescaledb",
                    "min_return": var_result.min_return,
                    "max_return": var_result.max_return
                }
            except Exception as e:
                logger.warning(f"TimescaleDB calculation failed, falling back to Python: {e}")
    
    # Fallback to Python calculation
    logger.info("Using Python-based risk calculations")
    from app.services.analytics import get_risk_metrics_sync
    
    metrics = get_risk_metrics_sync(
        db=db,
        asset_id=asset_id,
        benchmark_id=benchmark_id,
        lookback_days=lookback_weeks * 7
    )
    
    return {
        "beta": metrics.beta,
        "var_95": metrics.var_95,
        "observation_count": metrics.observation_count,
        "calculation_method": "python_pandas"
    }
