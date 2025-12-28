from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
import shutil
import logging

print("DEBUG: Loading monitoring.py")

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed system health check including DB connectivity and disk usage.
    """
    health_status = {
        "status": "healthy",
        "components": {
            "database": {"status": "unknown"},
            "disk": {"status": "unknown"}
        }
    }
    
    # Check Database
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {"status": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {"status": "disconnected", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check Disk Space
    try:
        total, used, free = shutil.disk_usage("/")
        health_status["components"]["disk"] = {
            "status": "ok",
            "total_gb": round(total / (2**30), 2),
            "free_gb": round(free / (2**30), 2),
            "percent_used": round((used / total) * 100, 1)
        }
    except Exception as e:
        logger.error(f"Disk health check failed: {e}")
        health_status["components"]["disk"] = {"status": "error", "message": str(e)}

    if health_status["status"] != "healthy":
        raise HTTPException(status_code=503, detail=health_status)
        
    return health_status