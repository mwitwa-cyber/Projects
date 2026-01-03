"""
Celery Beat Scheduler for Data Pipelines and Risk Calculations
"""
from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import logging
from typing import Optional, List

logger = logging.getLogger("scheduler")

# Initialize Celery app
celery_app = Celery('luse_quant_tasks')

# Load configuration from settings
try:
    from app.core.config import settings
    celery_app.conf.broker_url = settings.CELERY_BROKER_URL
    celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND
    RISK_HOUR = settings.RISK_CALCULATION_HOUR
    RISK_MINUTE = settings.RISK_CALCULATION_MINUTE
    DEFAULT_LOOKBACK = settings.DEFAULT_LOOKBACK_DAYS
    BENCHMARK_ID = settings.BENCHMARK_ASSET_ID
except Exception:
    # Fallback for testing
    celery_app.conf.broker_url = 'redis://redis:6379/0'
    celery_app.conf.result_backend = 'redis://redis:6379/0'
    RISK_HOUR = 18
    RISK_MINUTE = 30
    DEFAULT_LOOKBACK = 365
    BENCHMARK_ID = 1

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Lusaka',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute timeout
    worker_prefetch_multiplier=1,
)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure scheduled tasks."""
    
    # Daily LUSE update (weekdays at 5:30 PM)
    sender.add_periodic_task(
        crontab(hour=17, minute=30, day_of_week='1-5'),
        daily_luse_update.s(),
        name='Fetch LUSE prices daily'
    )
    
    # Daily Risk Metrics calculation (weekdays at 6:30 PM - after price update)
    sender.add_periodic_task(
        crontab(hour=RISK_HOUR, minute=RISK_MINUTE, day_of_week='1-5'),
        calculate_all_risk_metrics.s(),
        name='Calculate risk metrics for all assets'
    )
    
    # Weekly BoZ yield curve update (Monday 9 AM)
    sender.add_periodic_task(
        crontab(hour=9, minute=0, day_of_week='1'),
        weekly_boz_yield_curve_update.s(),
        name='Fetch BoZ yield curve weekly'
    )
    
    # Monthly ZamStats CPI update (1st of month at 10 AM)
    sender.add_periodic_task(
        crontab(hour=10, minute=0, day_of_month='1'),
        monthly_zamstats_cpi_update.s(),
        name='Fetch ZamStats CPI monthly'
    )


# ==================== Data Pipeline Tasks ====================

@celery_app.task(bind=True, max_retries=3)
def daily_luse_update(self):
    """Fetch daily LUSE prices."""
    logger.info("Running daily LUSE update...")
    try:
        from backend.services.data_pipelines.luse_scraper import fetch_luse_prices
        fetch_luse_prices()
        logger.info("LUSE update completed successfully")
    except Exception as exc:
        logger.error(f"LUSE update failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def weekly_boz_yield_curve_update(self):
    """Fetch weekly BoZ yield curve data."""
    logger.info("Running weekly BoZ yield curve update...")
    try:
        from backend.services.data_pipelines.boz_yield_curve import fetch_boz_yield_curve
        fetch_boz_yield_curve()
        logger.info("BoZ yield curve update completed successfully")
    except Exception as exc:
        logger.error(f"BoZ yield curve update failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def monthly_zamstats_cpi_update(self):
    """Fetch monthly ZamStats CPI data."""
    logger.info("Running monthly ZamStats CPI update...")
    try:
        from backend.services.data_pipelines.zamstats import fetch_zamstats_cpi
        fetch_zamstats_cpi()
        logger.info("ZamStats CPI update completed successfully")
    except Exception as exc:
        logger.error(f"ZamStats CPI update failed: {exc}")
        self.retry(exc=exc, countdown=60)


# ==================== Risk Calculation Tasks ====================

@celery_app.task(bind=True, max_retries=2)
def calculate_asset_risk_metrics(
    self,
    asset_id: int,
    benchmark_id: Optional[int] = None,
    lookback_days: Optional[int] = None
) -> dict:
    """
    Calculate and store risk metrics for a single asset.
    
    Args:
        asset_id: The asset to analyze
        benchmark_id: Benchmark for beta calculation (default: LASI)
        lookback_days: Historical period (default: 365)
        
    Returns:
        Dict with calculation results
    """
    benchmark_id = benchmark_id or BENCHMARK_ID
    lookback_days = lookback_days or DEFAULT_LOOKBACK
    
    logger.info(
        f"Calculating risk metrics for asset {asset_id} "
        f"vs benchmark {benchmark_id} ({lookback_days} days)"
    )
    
    try:
        from app.core.db import SessionLocal
        from app.services.analytics import RiskEngine, RiskCalculationError
        from app.models.risk_metrics import RiskMetricsHistory
        
        db = SessionLocal()
        try:
            engine = RiskEngine(db)
            metrics = engine.calculate_risk_metrics_sync(
                asset_id=asset_id,
                benchmark_id=benchmark_id,
                lookback_days=lookback_days
            )
            
            # Store in database
            risk_record = RiskMetricsHistory(
                asset_id=asset_id,
                benchmark_id=benchmark_id,
                calculation_date=metrics.calculation_date,
                beta=metrics.beta,
                var_95=metrics.var_95,
                observation_count=metrics.observation_count,
                lookback_days=metrics.lookback_days,
                calculation_status="completed"
            )
            db.add(risk_record)
            db.commit()
            
            logger.info(
                f"Risk metrics stored for asset {asset_id}: "
                f"beta={metrics.beta:.4f}, VaR={metrics.var_95:.4f}%"
            )
            
            return {
                "status": "success",
                "asset_id": asset_id,
                "beta": metrics.beta,
                "var_95": metrics.var_95,
                "observation_count": metrics.observation_count
            }
            
        except RiskCalculationError as e:
            # Store failed calculation
            risk_record = RiskMetricsHistory(
                asset_id=asset_id,
                benchmark_id=benchmark_id,
                calculation_date=datetime.now(),
                beta=0.0,
                var_95=0.0,
                observation_count=0,
                lookback_days=lookback_days,
                calculation_status="failed",
                error_message=str(e.message)[:500]
            )
            db.add(risk_record)
            db.commit()
            
            logger.warning(f"Risk calculation failed for asset {asset_id}: {e.message}")
            return {
                "status": "failed",
                "asset_id": asset_id,
                "error": e.message,
                "error_code": e.error_code
            }
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Risk calculation error for asset {asset_id}: {exc}")
        self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True)
def calculate_all_risk_metrics(
    self,
    benchmark_id: Optional[int] = None,
    lookback_days: Optional[int] = None,
    asset_ids: Optional[List[int]] = None
) -> dict:
    """
    Calculate risk metrics for all active assets (or specified subset).
    
    Args:
        benchmark_id: Benchmark for beta calculation
        lookback_days: Historical period
        asset_ids: Optional list of specific assets (default: all active)
        
    Returns:
        Summary of calculations
    """
    benchmark_id = benchmark_id or BENCHMARK_ID
    lookback_days = lookback_days or DEFAULT_LOOKBACK
    
    logger.info(f"Starting batch risk calculation (benchmark={benchmark_id})")
    
    try:
        from app.core.db import SessionLocal
        from app.models.asset import Asset
        
        db = SessionLocal()
        try:
            if asset_ids:
                assets = db.query(Asset).filter(
                    Asset.id.in_(asset_ids),
                    Asset.is_active == True
                ).all()
            else:
                assets = db.query(Asset).filter(
                    Asset.is_active == True,
                    Asset.id != benchmark_id  # Skip benchmark itself
                ).all()
            
            asset_id_list = [a.id for a in assets]
            logger.info(f"Queuing risk calculations for {len(asset_id_list)} assets")
            
        finally:
            db.close()
        
        # Queue individual calculations
        results = []
        for asset_id in asset_id_list:
            task = calculate_asset_risk_metrics.delay(
                asset_id=asset_id,
                benchmark_id=benchmark_id,
                lookback_days=lookback_days
            )
            results.append({"asset_id": asset_id, "task_id": task.id})
        
        return {
            "status": "queued",
            "total_assets": len(asset_id_list),
            "benchmark_id": benchmark_id,
            "lookback_days": lookback_days,
            "tasks": results
        }
        
    except Exception as exc:
        logger.error(f"Batch risk calculation error: {exc}")
        return {"status": "error", "error": str(exc)}


@celery_app.task
def get_latest_risk_metrics(asset_id: int) -> Optional[dict]:
    """
    Retrieve the latest risk metrics for an asset.
    
    Args:
        asset_id: Asset identifier
        
    Returns:
        Latest risk metrics or None
    """
    try:
        from app.core.db import SessionLocal
        from app.models.risk_metrics import RiskMetricsHistory
        
        db = SessionLocal()
        try:
            latest = db.query(RiskMetricsHistory).filter(
                RiskMetricsHistory.asset_id == asset_id,
                RiskMetricsHistory.calculation_status == "completed"
            ).order_by(
                RiskMetricsHistory.calculation_date.desc()
            ).first()
            
            if latest:
                return latest.to_dict()
            return None
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Error fetching risk metrics for asset {asset_id}: {exc}")
        return None
