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
