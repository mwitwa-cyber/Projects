"""
ZamStats CPI Data Ingestion: Fetches monthly CPI data and stores it for inflation calculations.
"""
import requests
import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.models.market_data import MarketData

ZAMSTATS_URL = "https://www.zamstats.gov.zm/index.php/publications/category/13-consumer-price-index-cpi"  # Example URL
logger = logging.getLogger("zamstats_cpi")


def fetch_zamstats_cpi():
    """Fetch and store ZamStats CPI data."""
    session = SessionLocal()
    try:
        response = requests.get(ZAMSTATS_URL)
        response.raise_for_status()
        # TODO: Parse HTML or CSV for CPI values and dates
        # Example parsed data:
        cpi_data = [
            {"observation_date": datetime(2025, 11, 1).date(), "inflation_rate": 0.13},
            {"observation_date": datetime(2025, 12, 1).date(), "inflation_rate": 0.14},
            # ...
        ]
        for entry in cpi_data:
            md = MarketData(
                observation_date=entry["observation_date"],
                inflation_rate=entry["inflation_rate"]
            )
            session.add(md)
        session.commit()
        logger.info(f"Stored {len(cpi_data)} CPI data points.")
    except Exception as e:
        logger.error(f"Failed to fetch or store ZamStats CPI data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fetch_zamstats_cpi()
