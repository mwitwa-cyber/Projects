import os
import asyncio
import random
import time
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, List, Dict

import yfinance as yf
import requests

from app.core.db import SessionLocal
from app.services.market_data import MarketDataService
from app.core.models import Security
from app.services.luse_provider import LUSEProvider


# ============ CURRENCY CONVERSION ============

# USD-denominated securities on LuSE that need conversion to ZMW
USD_DENOMINATED_SECURITIES = {"REIZ"}


def convert_to_zmw(ticker: str, price: float) -> float:
    """Convert USD-denominated securities to ZMW using live exchange rate."""
    if ticker.upper() in USD_DENOMINATED_SECURITIES:
        try:
            from app.services.currency import convert_usd_to_zmw
            return convert_usd_to_zmw(price)
        except ImportError:
            # Fallback if currency module not available
            return round(price * 22.50, 2)
    return price


# ============ PROVIDER STRATEGY PATTERN ============

class PriceProvider(ABC):
    """Base class for market-data providers."""

    @abstractmethod
    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch price and volume for a symbol. Return {price, volume} or None."""
        pass


class SimulatorProvider(PriceProvider):
    """Simulator: random-walk price updates."""

    def __init__(self):
        self.prices = {}

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        if symbol not in self.prices:
            self.prices[symbol] = 1.0
        change_pct = random.uniform(-0.01, 0.01)
        self.prices[symbol] = max(0.0001, self.prices[symbol] * (1 + change_pct))
        volume = int(abs(random.gauss(1000, 500))) + 10
        return {"price": round(self.prices[symbol], 4), "volume": volume}


class YFinanceProvider(PriceProvider):
    """Yahoo Finance provider."""

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        try:
            tick = os.getenv(f"SYMBOL_MAP_{symbol}", symbol)
            t = yf.Ticker(tick)
            q = t.info
            price = q.get("regularMarketPrice") or q.get("previousClose")
            if price is None:
                return None
            volume = q.get("volume") or 0
            return {"price": float(price), "volume": int(volume)}
        except Exception:
            return None


class AlphaVantageProvider(PriceProvider):
    """AlphaVantage provider (requires API key: ALPHAVANTAGE_API_KEY)."""

    def __init__(self):
        self.api_key = os.getenv("ALPHAVANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit = 5  # ~5 req/min for free tier
        self.last_request_time = 0

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        if not self.api_key:
            return None

        # Rate limiting: ~12s between requests for free tier
        elapsed = time.time() - self.last_request_time
        if elapsed < 12:
            time.sleep(12 - elapsed)

        try:
            # AlphaVantage expects uppercase and may use .ZA for JSE, .L for LSE, etc.
            tick = os.getenv(f"SYMBOL_MAP_{symbol}", symbol)
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": tick,
                "apikey": self.api_key,
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            self.last_request_time = time.time()

            if resp.status_code != 200:
                return None

            data = resp.json()
            quote = data.get("Global Quote", {})

            if not quote or not quote.get("05. price"):
                return None

            price = float(quote["05. price"])
            volume = int(quote.get("06. volume", 0) or 0)
            return {"price": round(price, 4), "volume": volume}
        except Exception:
            return None


class FinnhubProvider(PriceProvider):
    """Finnhub provider (requires API key: FINNHUB_API_KEY)."""

    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        self.base_url = "https://finnhub.io/api/v1/quote"
        self.last_request_time = 0

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        if not self.api_key:
            return None

        # Rate limiting: ~300 req/min for free tier, but be conservative
        elapsed = time.time() - self.last_request_time
        if elapsed < 1:
            time.sleep(1 - elapsed)

        try:
            tick = os.getenv(f"SYMBOL_MAP_{symbol}", symbol)
            params = {"symbol": tick, "token": self.api_key}
            resp = requests.get(self.base_url, params=params, timeout=10)
            self.last_request_time = time.time()

            if resp.status_code != 200:
                return None

            data = resp.json()

            if not data or data.get("c") is None:
                return None

            price = float(data["c"])
            volume = int(data.get("v", 0) or 0)
            return {"price": round(price, 4), "volume": volume}
        except Exception:
            return None


class IEXCloudProvider(PriceProvider):
    """IEX Cloud provider (requires API key: IEXCLOUD_API_KEY)."""

    def __init__(self):
        self.api_key = os.getenv("IEXCLOUD_API_KEY")
        self.base_url = "https://cloud.iexapis.com/stable"
        self.sandbox = os.getenv("IEXCLOUD_SANDBOX", "false").lower() in ("1", "true")

    def fetch_price(self, symbol: str) -> Optional[Dict[str, float]]:
        if not self.api_key:
            return None

        try:
            tick = os.getenv(f"SYMBOL_MAP_{symbol}", symbol)
            endpoint = f"{self.base_url}/data/core/quote/{tick}"
            params = {"token": self.api_key}
            if self.sandbox:
                params["iexcloud_api_version"] = "v1"

            resp = requests.get(endpoint, params=params, timeout=10)

            if resp.status_code != 200:
                return None

            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            if not data or data.get("latestPrice") is None:
                return None

            price = float(data["latestPrice"])
            volume = int(data.get("latestVolume", 0) or 0)
            return {"price": round(price, 4), "volume": volume}
        except Exception:
            return None


# ============ MARKET SCRAPER ============

class MarketScraper:
    def __init__(self, db_session_factory=SessionLocal, provider: str = "simulator", interval: int = 60):
        self.db_session_factory = db_session_factory
        self.provider_name = provider
        self.interval = interval
        self._running = False
        self.provider = self._create_provider(provider)

    def _create_provider(self, provider_name: str) -> PriceProvider:
        """Factory method to create provider instance."""
        name = provider_name.lower()
        if name == "alphavantage":
            return AlphaVantageProvider()
        elif name == "finnhub":
            return FinnhubProvider()
        elif name == "iexcloud":
            return IEXCloudProvider()
        elif name == "yfinance":
            return YFinanceProvider()
        elif name == "luse":
            return LUSEProvider()
        else:
            # Default to simulator
            return SimulatorProvider()

    def _get_securities(self, db) -> List[Security]:
        return db.query(Security).all()

    async def _ingest_for_security(self, db, service: MarketDataService, sec: Security):
        today = date.today()

        # Find latest known price for fallback
        last_record = db.execute(
            "SELECT price FROM market_prices WHERE security_ticker=:t ORDER BY valid_from DESC LIMIT 1",
            {"t": sec.ticker}
        ).fetchone()

        last_price = last_record[0] if last_record else 1.0

        # Try provider fetch
        fetched = self.provider.fetch_price(sec.ticker)

        if fetched:
            price = fetched.get("price", last_price)
            volume = fetched.get("volume", 0)
        else:
            # Fallback: simulator if provider fails
            fallback = SimulatorProvider().fetch_price(sec.ticker)
            price = fallback["price"]
            volume = fallback.get("volume", 0)

        # Convert USD-denominated securities to ZMW
        price = convert_to_zmw(sec.ticker, price)

        service.ingest_price(sec.ticker, price, volume, today)

    async def run_once(self):
        db = self.db_session_factory()
        try:
            service = MarketDataService(db)
            secs = self._get_securities(db)
            for sec in secs:
                await self._ingest_for_security(db, service, sec)
        except Exception as e:
            # Log error but don't stop scraper
            print(f"Scraper error: {e}")
        finally:
            db.close()

    async def start(self):
        self._running = True
        print(f"Scraper started with provider: {self.provider_name}, interval: {self.interval}s")
        while self._running:
            try:
                await self.run_once()
            except Exception:
                pass
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False


async def run_background_scraper(provider: str = None, interval: int = None):
    provider = provider or os.getenv("SCRAPER_PROVIDER", "simulator")
    interval = int(interval or os.getenv("SCRAPER_INTERVAL", "60"))
    scraper = MarketScraper(provider=provider, interval=interval)
    await scraper.start()


if __name__ == "__main__":
    import asyncio

    p = os.getenv("SCRAPER_PROVIDER", "simulator")
    i = int(os.getenv("SCRAPER_INTERVAL", "60"))
    try:
        asyncio.run(run_background_scraper(p, i))
    except KeyboardInterrupt:
        print("\nScraper stopped")
