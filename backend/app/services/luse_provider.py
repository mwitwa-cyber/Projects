
import requests
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.services.scraper import PriceProvider
from typing import Optional, Dict

# Mapping from our ticker symbols to AfricanFinancials URL slugs
AFRICANFINANCIALS_TICKER_MAP = {
    "AECI": "zm-aeci",
    "ATEL": "zm-atel", 
    "BATA": "zm-bata",
    "BATZ": "zm-batz",
    "CCAF": "zm-ccaf",
    "CECZ": "zm-cec",
    "CHIL": "zm-chil",
    "DCZM": "zm-dcz",
    "MAFS": "zm-mafs",
    "NATB": "zm-natb",
    "PMDZ": "zm-pmdz",
    "PUMA": "zm-puma",
    "REIZ": "zm-reiz",
    "SCBL": "zm-scz",
    "SHOP": "zm-shop",
    "ZABR": "zm-zabr",
    "ZMBF": "zm-zamb",
    "ZMFA": "zm-zamefa",
    "ZMRE": "zm-zmre",
    "ZNCO": "zm-zanaco",
    "ZSUG": "zm-zmsg",
    "ZCCM": "zm-zccm",
    "ZFCO": "zm-zaffico",
}

class LUSEProvider(PriceProvider):
    """Provider for scraping data from African Financials for LuSE securities."""
    
    def __init__(self, base_url="https://africanfinancials.com/company/"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Fetch the price and volume for a given symbol from African Financials.
        """
        # Map our ticker to AfricanFinancials slug
        af_slug = AFRICANFINANCIALS_TICKER_MAP.get(symbol.upper())
        if not af_slug:
            self.logger.warning(f"No AfricanFinancials mapping for symbol '{symbol}'")
            return None

        try:
            url = f"{self.base_url}{af_slug}/"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Look for price pattern: "PRICE (KWACHA)XX.XX" or "PRICE (US CENTS)XX.XX"
            text = soup.get_text()
            
            # Try Kwacha price first
            price_match = re.search(r'PRICE\s*\(KWACHA\)\s*([\d,]+\.?\d*)', text)
            is_usd = False
            
            if not price_match:
                # Try USD price (for REIZ)
                price_match = re.search(r'PRICE\s*\(US CENTS\)\s*([\d,]+\.?\d*)', text)
                is_usd = True
            
            if not price_match:
                self.logger.warning(f"Could not find price for symbol '{symbol}' on {url}")
                return None
            
            price_str = price_match.group(1).replace(",", "")
            price = float(price_str)
            
            # Convert USD cents to ZMW if needed
            if is_usd:
                from app.services.currency import convert_usd_to_zmw
                price = convert_usd_to_zmw(price / 100)  # Convert cents to dollars first
            
            # Look for volume: "TODAY'S VOLUMEXXX"
            volume_match = re.search(r"TODAY'S VOLUME\s*([\d,\.]+[KMB]?)", text)
            volume = 0
            if volume_match:
                vol_str = volume_match.group(1).replace(",", "")
                # Handle K (thousands), M (millions), B (billions)
                if vol_str.endswith('K'):
                    volume = int(float(vol_str[:-1]) * 1000)
                elif vol_str.endswith('M'):
                    volume = int(float(vol_str[:-1]) * 1000000)
                elif vol_str.endswith('B'):
                    volume = int(float(vol_str[:-1]) * 1000000000)
                else:
                    volume = int(float(vol_str))
            
            self.logger.info(f"Fetched {symbol}: price={price}, volume={volume}")
            return {"price": round(price, 2), "volume": volume}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from AfricanFinancials for {symbol}: {e}")
            return None
        except (ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse data for symbol '{symbol}': {e}")
            return None
