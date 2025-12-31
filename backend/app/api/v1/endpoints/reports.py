from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.services.report_service import ReportService
from app.services.market_data import MarketDataService
from app.api.v1.endpoints.auth import get_current_active_user
from app.core.database import get_db

router = APIRouter()

def get_report_service(db: Session = Depends(get_db)):
    return ReportService(MarketDataService(db))

@router.get("/market-summary")
def get_market_summary_pdf(
    current_user = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service)
):
    """
    Generate and download the Market Summary PDF report.
    """
    try:
        pdf_content = service.generate_market_report()
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=LuSE_Market_Summary.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
