"""
LuSE Provider - Fetches real market data from afx.kwayisi.org for Lusaka Stock Exchange securities.
"""

import requests
from bs4 import BeautifulSoup
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict


# Define base class here to avoid circular import with scraper.py
class PriceProvider(ABC):
    """Base class for market-data providers."""

    @abstractmethod
    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch price and volume for a symbol. Return {price, volume} or None."""
        pass


# Mapping from our ticker symbols to afx.kwayisi.org URL slugs
AFX_TICKER_MAP = {
    "AECI": "aeci",
    "ATEL": "atel",
    "BATA": "bata",
    "BATZ": "batz",
    "CCAF": "ccaf",
    "CECZ": "cecz",
    "CHIL": "chil",
    "FARM": "farm",
    "FQMZ": "fqmz",
    "MAFS": "mafs",
    "NATB": "natb",
    "PMDZ": "pmdz",
    "PUMA": "puma",
    "REIZ": "reiz",
    "REIZP": "reizp",
    "SCBL": "scbl",
    "SHOP": "shop",
    "ZABR": "zabr",
    "ZCCM": "zccm",
    "ZFCO": "zfco",
    "ZMBF": "zmbf",
    "ZMFA": "zmfa",
    "ZMRE": "zmre",
    "ZNCO": "znco",
    "ZSUG": "zsug",
    # Legacy mappings that may not exist on afx
    "DCZM": None,  # Dot Com Zambia - may not be listed yet
}

# Current real prices from afx.kwayisi.org (as of Jan 2, 2026)
CURRENT_REAL_PRICES = {
    "AECI": 130.00,
    "ATEL": 137.73,
    "BATA": 6.53,
    "BATZ": 14.25,
    "CCAF": 0.83,
    "CECZ": 19.28,
    "CHIL": 80.00,
    "MAFS": 1.81,
    "NATB": 2.99,
    "PMDZ": 5.00,
    "PUMA": 4.00,
    "REIZ": 0.09,  # USD-denominated
    "SCBL": 2.55,
    "SHOP": 350.00,
    "ZABR": 7.01,
    "ZCCM": 166.00,
    "ZFCO": 3.57,
    "ZMBF": 2.20,
    "ZMFA": 60.00,
    "ZMRE": 2.80,  # Updated from 2.70 based on +3.7% gain
    "ZNCO": 5.97,
    "ZSUG": 66.97,
    "DCZM": 12.30,  # IPO price
}


class LUSEProvider(PriceProvider):
    """
    Provider for scraping real market data from afx.kwayisi.org for LuSE securities.
    
    Falls back to cached real prices if scraping fails.
    """
    
    def __init__(self, base_url="https://afx.kwayisi.org/luse/"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        # Keep track of last known prices for fallback
        self._cached_prices = CURRENT_REAL_PRICES.copy()

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Fetch the price and volume for a given symbol from afx.kwayisi.org.
        
        Returns dict with 'price' (ZMW) and 'volume' or None on failure.
        Falls back to cached real prices if live scraping fails.
        """
        symbol = symbol.upper()
        
        # Map our ticker to afx.kwayisi.org slug
        afx_slug = AFX_TICKER_MAP.get(symbol)
        if afx_slug is None:
            # No mapping available - use cached price if available
            if symbol in self._cached_prices:
                self.logger.info(f"Using cached price for {symbol} (no AFX mapping)")
                return {"price": self._cached_prices[symbol], "volume": 0}
            self.logger.warning(f"No afx.kwayisi.org mapping for symbol '{symbol}'")
            return None

        try:
            url = f"{self.base_url}{afx_slug}.html"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            text = soup.get_text()
            
            # Look for: "current share price of ... is ZMW XXX.XX"
            price_match = re.search(r'current share price.*?is\s+ZMW\s+([\d,]+\.?\d*)', text, re.IGNORECASE)
            
            if not price_match:
                # Try: "closed ... at XXX.XX ZMW"
                price_match = re.search(r'at\s+([\d,]+\.?\d*)\s+ZMW', text, re.IGNORECASE)
            
            if not price_match:
                self.logger.warning(f"Could not find price pattern for symbol '{symbol}' on {url}")
                # Fall back to cached price
                if symbol in self._cached_prices:
                    self.logger.info(f"Using cached price for {symbol}")
                    return {"price": self._cached_prices[symbol], "volume": 0}
                return None
            
            price_str = price_match.group(1).replace(",", "")
            price = float(price_str)
            
            # Update cache with the fresh price
            self._cached_prices[symbol] = price
            
            # Look for volume: "traded a total volume of XXX shares"
            volume = 0
            volume_match = re.search(r'volume of\s+([\d,\.]+)\s*(?:shares|traded shares)', text, re.IGNORECASE)
            if volume_match:
                vol_str = volume_match.group(1).replace(",", "")
                # Handle suffixes
                if 'M' in vol_str or 'million' in text.lower():
                    volume = int(float(vol_str.replace('M', '')) * 1_000_000)
                elif 'K' in vol_str:
                    volume = int(float(vol_str.replace('K', '')) * 1_000)
                else:
                    try:
                        volume = int(float(vol_str))
                    except ValueError:
                        volume = 0
            
            self.logger.info(f"Fetched {symbol}: price={price} ZMW, volume={volume}")
            return {"price": round(price, 2), "volume": volume}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch data from afx.kwayisi.org for {symbol}: {e}")
            # Fall back to cached price
            if symbol in self._cached_prices:
                self.logger.info(f"Using cached price for {symbol} after request error")
                return {"price": self._cached_prices[symbol], "volume": 0}
            return None
        except (ValueError, IndexError, AttributeError) as e:
            self.logger.error(f"Failed to parse data for symbol '{symbol}': {e}")
            # Fall back to cached price
            if symbol in self._cached_prices:
                self.logger.info(f"Using cached price for {symbol} after parse error")
                return {"price": self._cached_prices[symbol], "volume": 0}
            return None

    def get_all_prices(self) -> Dict[str, Dict[str, float]]:
        """
        Fetch prices for all known LuSE securities.
        
        Returns dict mapping ticker -> {price, volume}
        """
        results = {}
        for ticker in AFX_TICKER_MAP.keys():
            if AFX_TICKER_MAP[ticker] is not None:  # Only fetch if mapping exists
                price_data = self.fetch_price(ticker)
                if price_data:
                    results[ticker] = price_data
        return results

    def get_cached_price(self, symbol: str) -> Optional[float]:
        """Get the cached real price for a symbol without making an HTTP request."""
        return self._cached_prices.get(symbol.upper())
