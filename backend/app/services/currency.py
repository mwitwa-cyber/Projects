"""
Currency Exchange Rate Service
Fetches live USD/ZMW exchange rates from Bank of Zambia and other sources.
"""

import os
import re
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
import requests

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# Cache for exchange rate to avoid hammering BoZ website
_rate_cache: Dict[str, any] = {
    "rate": None,
    "timestamp": None,
    "ttl_seconds": 3600  # Cache for 1 hour
}

# Default fallback rate if scraping fails (updated to reflect current ~22-23 range)
DEFAULT_USD_ZMW_RATE = 22.50


def get_cached_rate() -> Optional[float]:
    """Return cached rate if still valid."""
    if _rate_cache["rate"] and _rate_cache["timestamp"]:
        age = (datetime.now() - _rate_cache["timestamp"]).total_seconds()
        if age < _rate_cache["ttl_seconds"]:
            return _rate_cache["rate"]
    return None


def set_cached_rate(rate: float) -> None:
    """Cache the exchange rate."""
    _rate_cache["rate"] = rate
    _rate_cache["timestamp"] = datetime.now()


def fetch_boz_exchange_rate() -> Optional[float]:
    """
    Scrape USD/ZMW exchange rate from Bank of Zambia website.
    Source: https://www.boz.zm/exchange-rates
    """
    if not HAS_BS4:
        print("Warning: beautifulsoup4 not installed, using fallback API")
        return None
    
    # Check cache first
    cached = get_cached_rate()
    if cached:
        return cached
    
    try:
        # Bank of Zambia exchange rates page
        url = "https://www.boz.zm/exchange-rates"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # BoZ typically displays rates in a table
        # Look for USD row and extract mid-rate
        tables = soup.find_all("table")
        
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                cell_text = [c.get_text(strip=True).upper() for c in cells]
                
                # Look for USD row
                if any("USD" in text or "US DOLLAR" in text for text in cell_text):
                    # Try to find numeric values (exchange rates)
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        try:
                            # Remove commas and try to parse as float
                            cleaned = text.replace(",", "").replace(" ", "")
                            rate = float(cleaned)
                            # Valid ZMW/USD rate should be between 15 and 35
                            if 15.0 <= rate <= 35.0:
                                set_cached_rate(rate)
                                print(f"BoZ USD/ZMW Rate: {rate}")
                                return rate
                        except ValueError:
                            continue
        
        # Alternative: Try to find rate in page text using regex
        page_text = soup.get_text()
        patterns = [
            r"USD[:\s]+(\d{2}\.\d{2,4})",
            r"1\s*USD\s*=\s*(\d{2}\.\d{2,4})",
            r"US\s*Dollar[:\s]+(\d{2}\.\d{2,4})",
            r"(\d{2}\.\d{2,4})\s*ZMW",
        ]
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                rate = float(match.group(1))
                if 15.0 <= rate <= 35.0:
                    set_cached_rate(rate)
                    print(f"BoZ USD/ZMW Rate (regex): {rate}")
                    return rate
        
        print("Could not parse BoZ exchange rate, trying fallback APIs")
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching BoZ exchange rate: {e}")
        return None
    except Exception as e:
        print(f"Error parsing BoZ exchange rate: {e}")
        return None


def fetch_exchangerate_api() -> Optional[float]:
    """
    Fallback: Fetch from free exchange rate API (no key required).
    """
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        rate = data.get("rates", {}).get("ZMW")
        if rate and 15.0 <= rate <= 35.0:
            set_cached_rate(rate)
            print(f"ExchangeRate-API USD/ZMW: {rate}")
            return rate
        return None
    except Exception as e:
        print(f"Error fetching from ExchangeRate-API: {e}")
        return None


def fetch_frankfurter_api() -> Optional[float]:
    """
    Fallback: Fetch from Frankfurter API (free, no key, ECB-based).
    Note: May not have ZMW, so this is a last resort.
    """
    try:
        url = "https://api.frankfurter.app/latest?from=USD&to=ZMW"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        rate = data.get("rates", {}).get("ZMW")
        if rate and 15.0 <= rate <= 35.0:
            set_cached_rate(rate)
            print(f"Frankfurter API USD/ZMW: {rate}")
            return rate
        return None
    except Exception as e:
        print(f"Error fetching from Frankfurter API: {e}")
        return None


def get_usd_zmw_rate() -> float:
    """
    Get the current USD/ZMW exchange rate.
    Tries multiple sources in order:
    1. Cache (if valid)
    2. Bank of Zambia website
    3. ExchangeRate-API
    4. Frankfurter API
    5. Environment variable fallback
    6. Default hardcoded value
    
    Returns:
        float: The USD/ZMW exchange rate
    """
    # 1. Check cache
    cached = get_cached_rate()
    if cached:
        return cached
    
    # 2. Try Bank of Zambia
    rate = fetch_boz_exchange_rate()
    if rate:
        return rate
    
    # 3. Try ExchangeRate-API
    rate = fetch_exchangerate_api()
    if rate:
        return rate
    
    # 4. Try Frankfurter API
    rate = fetch_frankfurter_api()
    if rate:
        return rate
    
    # 5. Environment variable fallback
    env_rate = os.getenv("USD_TO_ZMW_RATE")
    if env_rate:
        try:
            rate = float(env_rate)
            if 15.0 <= rate <= 35.0:
                print(f"Using env USD_TO_ZMW_RATE: {rate}")
                return rate
        except ValueError:
            pass
    
    # 6. Default fallback
    print(f"Using default USD/ZMW rate: {DEFAULT_USD_ZMW_RATE}")
    return DEFAULT_USD_ZMW_RATE


def convert_usd_to_zmw(usd_amount: float) -> float:
    """
    Convert USD amount to ZMW using current exchange rate.
    
    Args:
        usd_amount: Amount in USD
        
    Returns:
        float: Amount in ZMW (rounded to 2 decimal places)
    """
    rate = get_usd_zmw_rate()
    return round(usd_amount * rate, 2)


if __name__ == "__main__":
    # Test the exchange rate fetching
    print("=" * 50)
    print("Testing USD/ZMW exchange rate fetching...")
    print("=" * 50)
    
    rate = get_usd_zmw_rate()
    print(f"\nFinal Rate: USD 1 = ZMW {rate}")
    print(f"REIZ (USD 0.09) = ZMW {convert_usd_to_zmw(0.09)}")
    print(f"REIZ historical (USD 0.05) = ZMW {convert_usd_to_zmw(0.05)}")
