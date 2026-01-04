from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List

from app.core.db import get_db
from app.services.yield_curve import YieldCurveService
from app.services.analytics import (
    RiskEngine,
    RiskMetrics,
    RiskCalculationError,
    get_risk_metrics_sync
)
from app.models.risk_metrics import RiskMetricsHistory
from pydantic import BaseModel

# TimescaleDB-optimized risk calculations
try:
    from app.services.timescale_risk import (
        get_beta_from_db,
        get_var_from_db,
        get_risk_metrics_hybrid,
        check_timescale_functions_exist,
        BetaResult,
        VaRResult
    )
    TIMESCALE_AVAILABLE = True
except ImportError:
    TIMESCALE_AVAILABLE = False

router = APIRouter()

@router.get("/yield-curve")
def get_yield_curve(
    date_str: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db)
):
    """
    Calculate Nelson-Siegel Yield Curve for Government Bonds.
    Returns: Fitted parameters and curve points for visualization.
    """
    try:
        target_date = date.today()
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        service = YieldCurveService(db)
        result = service.fit_nelson_siegel(target_date)
        
        if "error" in result:
             raise HTTPException(status_code=404, detail=result["error"])
             
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capm/{ticker}")
def get_capm_metrics(
    ticker: str,
    rf: float = 0.15,
    db: Session = Depends(get_db)
):
    """
    Calculate Liquidity-Adjusted CAPM Expected Return.
    rf: Risk-Free Rate (default 15% for ZMW).
    """
    try:
        from app.services.capm import CapmService
        service = CapmService(db)
        result = service.calculate_capm(ticker, risk_free_rate=rf)
        
        if "error" in result:
             raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{asset_id}", response_model=RiskMetrics)
def get_asset_risk_metrics(
    asset_id: int,
    benchmark_id: int = Query(..., description="Benchmark asset ID for beta calculation"),
    lookback_days: int = Query(365, ge=30, le=1825, description="Historical period in days"),
    db: Session = Depends(get_db)
):
    """
    Calculate risk metrics (Beta, VaR) for a specific asset.
    
    - **asset_id**: The asset to analyze
    - **benchmark_id**: The benchmark asset (e.g., market index proxy)
    - **lookback_days**: Historical period for calculations (default: 365 days)
    
    Returns:
        - **beta**: Systematic risk coefficient vs benchmark
        - **var_95**: 95% Value at Risk (weekly, as percentage)
        - **observation_count**: Number of weekly observations used
    
    Notes:
        - Data is resampled to weekly frequency to handle LuSE illiquidity
        - Log returns are used for calculations
        - Forward-fill is applied to handle missing trading days
    """
    try:
        metrics = get_risk_metrics_sync(
            db=db,
            asset_id=asset_id,
            benchmark_id=benchmark_id,
            lookback_days=lookback_days
        )
        return metrics
    except RiskCalculationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": e.message, "code": e.error_code}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Task Trigger Endpoints ====================

class TaskResponse(BaseModel):
    """Response for task trigger endpoints."""
    status: str
    task_id: Optional[str] = None
    message: str


class BatchTaskResponse(BaseModel):
    """Response for batch task triggers."""
    status: str
    total_assets: int
    message: str
    tasks: Optional[List[dict]] = None


@router.post("/risk/calculate/{asset_id}", response_model=TaskResponse)
def trigger_risk_calculation(
    asset_id: int,
    benchmark_id: int = Query(None, description="Benchmark asset ID (default: LASI)"),
    lookback_days: int = Query(365, ge=30, le=1825, description="Historical period"),
):
    """
    Trigger async risk metrics calculation for a specific asset.
    
    Returns a task ID that can be used to check calculation status.
    Results will be stored in the risk_metrics table.
    """
    try:
        from app.tasks import calculate_asset_risk_metrics
        from app.core.config import settings
        
        benchmark_id = benchmark_id or settings.BENCHMARK_ASSET_ID
        
        task = calculate_asset_risk_metrics.delay(
            asset_id=asset_id,
            benchmark_id=benchmark_id,
            lookback_days=lookback_days
        )
        
        return TaskResponse(
            status="queued",
            task_id=task.id,
            message=f"Risk calculation queued for asset {asset_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/calculate-all", response_model=BatchTaskResponse)
def trigger_batch_risk_calculation(
    benchmark_id: int = Query(None, description="Benchmark asset ID (default: LASI)"),
    lookback_days: int = Query(365, ge=30, le=1825, description="Historical period"),
    asset_ids: Optional[List[int]] = Query(None, description="Specific assets to calculate"),
):
    """
    Trigger async risk metrics calculation for all active assets.
    
    Queues individual calculation tasks for each asset.
    Use asset_ids parameter to calculate for specific assets only.
    """
    try:
        from app.tasks import calculate_all_risk_metrics
        from app.core.config import settings
        
        benchmark_id = benchmark_id or settings.BENCHMARK_ASSET_ID
        
        task = calculate_all_risk_metrics.delay(
            benchmark_id=benchmark_id,
            lookback_days=lookback_days,
            asset_ids=asset_ids
        )
        
        return BatchTaskResponse(
            status="queued",
            total_assets=-1,  # Unknown until task runs
            message="Batch risk calculation queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{asset_id}/latest")
def get_latest_stored_risk_metrics(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the most recently calculated risk metrics for an asset.
    
    Returns stored metrics from the database (from scheduled or manual calculations).
    Use GET /risk/{asset_id} for real-time calculation instead.
    """
    try:
        latest = db.query(RiskMetricsHistory).filter(
            RiskMetricsHistory.asset_id == asset_id,
            RiskMetricsHistory.calculation_status == "completed"
        ).order_by(
            RiskMetricsHistory.calculation_date.desc()
        ).first()
        
        if not latest:
            raise HTTPException(
                status_code=404,
                detail=f"No risk metrics found for asset {asset_id}"
            )
        
        return latest.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/{asset_id}/history")
def get_risk_metrics_history(
    asset_id: int,
    limit: int = Query(30, ge=1, le=365, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get historical risk metrics for an asset.
    
    Returns a time series of calculated risk metrics.
    Useful for tracking how risk evolves over time.
    """
    try:
        history = db.query(RiskMetricsHistory).filter(
            RiskMetricsHistory.asset_id == asset_id,
            RiskMetricsHistory.calculation_status == "completed"
        ).order_by(
            RiskMetricsHistory.calculation_date.desc()
        ).limit(limit).all()
        
        return {
            "asset_id": asset_id,
            "count": len(history),
            "metrics": [record.to_dict() for record in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TimescaleDB-Optimized Endpoints ====================

@router.get("/timescale/beta/{asset_id}")
def get_timescale_beta(
    asset_id: int,
    benchmark_id: int = Query(..., description="Benchmark asset ID (e.g., LASI proxy)"),
    lookback_weeks: int = Query(52, ge=10, le=260, description="Lookback period in weeks"),
    db: Session = Depends(get_db)
):
    """
    Calculate Beta using TimescaleDB-optimized SQL functions.
    
    This endpoint offloads the heavy computation to the database,
    making it faster for large datasets.
    
    - **asset_id**: Asset to analyze
    - **benchmark_id**: Benchmark for beta calculation (e.g., LASI index proxy)
    - **lookback_weeks**: Historical period (default: 52 weeks = 1 year)
    
    Returns:
        - **beta**: Systematic risk coefficient
        - **correlation**: Correlation with benchmark
        - **asset_volatility**: Annualized volatility
        - **observation_count**: Number of weekly observations
    """
    if not TIMESCALE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="TimescaleDB risk functions not available"
        )
    
    try:
        result = get_beta_from_db(db, asset_id, benchmark_id, lookback_weeks)
        return {
            "asset_id": asset_id,
            "benchmark_id": benchmark_id,
            "lookback_weeks": lookback_weeks,
            "beta": result.beta,
            "correlation": result.correlation,
            "observation_count": result.observation_count,
            "asset_volatility": result.asset_volatility,
            "benchmark_volatility": result.benchmark_volatility,
            "calculation_method": "timescaledb"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timescale/var/{asset_id}")
def get_timescale_var(
    asset_id: int,
    lookback_weeks: int = Query(52, ge=10, le=260, description="Lookback period in weeks"),
    confidence: float = Query(0.95, ge=0.90, le=0.99, description="Confidence level"),
    db: Session = Depends(get_db)
):
    """
    Calculate Value at Risk (VaR) using TimescaleDB-optimized SQL functions.
    
    Uses historical simulation method with pre-aggregated weekly returns.
    
    - **asset_id**: Asset to analyze
    - **lookback_weeks**: Historical period (default: 52 weeks)
    - **confidence**: Confidence level (default: 95%)
    
    Returns:
        - **var_95**: Value at Risk as percentage
        - **cvar_95**: Conditional VaR (Expected Shortfall)
        - **observation_count**: Number of observations used
    """
    if not TIMESCALE_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="TimescaleDB risk functions not available"
        )
    
    try:
        result = get_var_from_db(db, asset_id, lookback_weeks, confidence)
        return {
            "asset_id": asset_id,
            "lookback_weeks": lookback_weeks,
            "confidence_level": confidence,
            "var": result.var_95,
            "cvar": result.cvar_95,
            "observation_count": result.observation_count,
            "min_return": result.min_return,
            "max_return": result.max_return,
            "calculation_method": "timescaledb_historical",
            "interpretation": f"{confidence*100:.0f}% confidence that weekly loss won't exceed {abs(result.var_95):.2f}%"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timescale/risk/{asset_id}")
def get_timescale_risk_metrics(
    asset_id: int,
    benchmark_id: int = Query(..., description="Benchmark asset ID"),
    lookback_weeks: int = Query(52, ge=10, le=260, description="Lookback period in weeks"),
    db: Session = Depends(get_db)
):
    """
    Calculate comprehensive risk metrics using TimescaleDB or Python fallback.
    
    Automatically uses the fastest available method:
    1. TimescaleDB SQL functions (if installed)
    2. Python pandas calculation (fallback)
    
    Returns combined Beta, VaR, volatility, and correlation metrics.
    """
    if not TIMESCALE_AVAILABLE:
        # Fallback to Python calculation
        try:
            metrics = get_risk_metrics_sync(
                db=db,
                asset_id=asset_id,
                benchmark_id=benchmark_id,
                lookback_days=lookback_weeks * 7
            )
            return {
                "asset_id": asset_id,
                "benchmark_id": benchmark_id,
                "lookback_weeks": lookback_weeks,
                "beta": metrics.beta,
                "var_95": metrics.var_95,
                "observation_count": metrics.observation_count,
                "calculation_method": "python_pandas"
            }
        except RiskCalculationError as e:
            raise HTTPException(status_code=400, detail={"error": e.message, "code": e.error_code})
    
    try:
        result = get_risk_metrics_hybrid(db, asset_id, benchmark_id, lookback_weeks, use_timescale=True)
        return {
            "asset_id": asset_id,
            "benchmark_id": benchmark_id,
            "lookback_weeks": lookback_weeks,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timescale/status")
def get_timescale_status(db: Session = Depends(get_db)):
    """
    Check if TimescaleDB risk functions are installed and ready.
    
    Returns status of each required SQL function.
    """
    if not TIMESCALE_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "TimescaleDB risk module not imported",
            "functions": {}
        }
    
    try:
        func_status = check_timescale_functions_exist(db)
        all_available = all(func_status.values())
        
        return {
            "status": "ready" if all_available else "partial",
            "message": "All TimescaleDB risk functions are installed" if all_available 
                      else "Some functions missing - run weekly_returns_view.sql migration",
            "functions": func_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "functions": {}
        }

