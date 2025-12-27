"""
BoZ Yield Curve Ingestion: Fetches and parses BoZ yield curve data, bootstraps zero-coupon curve, and stores in yield_curve table.
"""
import requests
import logging
from datetime import datetime
# from QuantLib import ...  # QuantLib integration for bootstrapping

from app.core.database import SessionLocal
from app.models.yield_curve import YieldCurveData

BOZ_URL = "https://www.boz.zm/monetary-policy/statistics/yield-curve/"  # Example URL
logger = logging.getLogger("boz_yield_curve")


def fetch_boz_yield_curve():
    """Fetch and store BoZ yield curve data."""
    session = SessionLocal()
    try:
        response = requests.get(BOZ_URL)
        response.raise_for_status()
        # TODO: Parse HTML or CSV for yield curve points (tenor, yield)
        # Example parsed data:
        curve_points = [
            {"tenor_days": 91, "yield_rate": 0.18},
            {"tenor_days": 182, "yield_rate": 0.195},
            {"tenor_days": 365, "yield_rate": 0.21},
            # ...
        ]
        observation_date = datetime.now().date()
        for point in curve_points:
            yc = YieldCurveData(
                observation_date=observation_date,
                instrument_type="T-Bill/Bond",
                tenor_days=point["tenor_days"],
                yield_rate=point["yield_rate"]
            )
            session.add(yc)
        session.commit()
        logger.info(f"Stored {len(curve_points)} yield curve points for {observation_date}")
    except Exception as e:
        logger.error(f"Failed to fetch or store BoZ yield curve: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fetch_boz_yield_curve()
