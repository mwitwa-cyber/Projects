
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.services.scraper import PriceProvider
from typing import Optional, Dict

class LUSEProvider(PriceProvider):
    """Provider for scraping data from the Lusaka Securities Exchange."""
    def __init__(self, url="https://www.luse.co.zm/"):
        self.url = url
        self.securities = ["AELZ", "AIRTEL", "BATA", "BATZ", "CCAF", "CEC", "REIZ", "MAFS", "PUMA", "SHOP", "SCBL", "ZCCM-IH", "ZMBF", "ZNCO", "ZSIC"]
        self.logger = logging.getLogger(__name__)

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Fetch the price and volume for a given symbol from the LUSE website.
        """
        if symbol not in self.securities:
            return None

        try:
            response = requests.get(self.url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find("table")

            if not table:
                self.logger.error("No data table found on the LUSE website.")
                return None

            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 5 and cols[0].text.strip() == symbol:
                    price = float(cols[2].text.replace(",", ""))
                    volume = int(cols[5].text.replace(",", ""))
                    return {"price": price, "volume": volume}

            self.logger.warning(f"Symbol '{symbol}' not found in the LUSE data table.")
            return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from LUSE: {e}")
            return None
        except (ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse LUSE data for symbol '{symbol}': {e}")
            return None
