"""
LuSE Data Scraper: Fetches daily equity prices from afx.kwayisi.org and stores them in the price_history table.
"""
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime


# ORM/database session imports
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.price_history import PriceHistory

LUSE_URL = "https://afx.kwayisi.org/zse/"
SECURITIES = ["ZCCM-IH", "Zanaco", "ZESCO", "Barclays"]  # Extend as needed

logger = logging.getLogger("luse_scraper")



def fetch_luse_prices():
    """Fetch daily LUSE equity prices from afx.kwayisi.org and store in DB."""
    results = []
    session = SessionLocal()
    try:
        response = requests.get(LUSE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        if not table:
            logger.error("No table found on LUSE page.")
            return results
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue
            security = cols[0].text.strip()
            if security not in SECURITIES:
                continue
            try:
                price = float(cols[1].text.replace(",", ""))
                volume = int(cols[4].text.replace(",", ""))
                trade_date = datetime.now().date()
                # Data validation
                if price < 0 or volume < 0:
                    logger.warning(f"Invalid data for {security}: price={price}, volume={volume}")
                    continue
                # Find asset by ticker
                asset = session.query(Asset).filter(Asset.ticker == security).first()
                if not asset:
                    logger.warning(f"Asset not found for ticker: {security}")
                    continue
                # Create PriceHistory record
                price_record = PriceHistory(
                    asset_id=asset.id,
                    trade_date=trade_date,
                    close_price=price,
                    volume=volume,
                    valid_from=datetime.now(),
                    valid_to=None,
                    transaction_from=datetime.now(),
                    transaction_to=None,
                    is_current=True
                )
                session.add(price_record)
                session.commit()
                results.append({
                    "security": security,
                    "price": price,
                    "volume": volume,
                    "trade_date": trade_date
                })
            except Exception as e:
                logger.error(f"Error parsing row for {security}: {e}")
                session.rollback()
    except Exception as e:
        logger.error(f"Failed to fetch LUSE data: {e}")
    finally:
        session.close()
    return results

if __name__ == "__main__":
    data = fetch_luse_prices()
    print(data)
