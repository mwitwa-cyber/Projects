from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.db import get_db
from app.services.yield_curve import YieldCurveService

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
