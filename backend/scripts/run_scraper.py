"""
Run the market-data scraper as a standalone process.

Usage:
    python run_scraper.py

Environment variables:
    SCRAPER_PROVIDER (simulator|yfinance)
    SCRAPER_INTERVAL (seconds)
    ENABLE_SCRAPER - not used here (script runs regardless)
"""
import os
import asyncio
from app.services.scraper import run_background_scraper


if __name__ == "__main__":
    provider = os.getenv("SCRAPER_PROVIDER", "simulator")
    interval = os.getenv("SCRAPER_INTERVAL", "60")
    try:
        asyncio.run(run_background_scraper(provider, interval))
    except KeyboardInterrupt:
        print("Scraper stopped")
