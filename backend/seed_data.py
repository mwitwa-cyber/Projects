from app.core.db import SessionLocal, engine
from app.core import models
from app.services.market_data import MarketDataService
from datetime import date, timedelta
import random

def seed():
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    service = MarketDataService(db)

    # 1. Create Securities (LuSE Concentrated Basket)
    tickers = [
        {"ticker": "CECZ", "name": "Copperbelt Energy Corporation", "sector": "Energy"},
        {"ticker": "ZANACO", "name": "Zambia National Commercial Bank", "sector": "Banking"},
        {"ticker": "SCBL", "name": "Standard Chartered Bank Zambia", "sector": "Banking"},
        {"ticker": "SHOP", "name": "Shoprite Holdings", "sector": "Retail"},
        {"ticker": "REIZ", "name": "Real Estate Investments Zambia", "sector": "Real Estate"},
        {"ticker": "ZSUG", "name": "Zambia Sugar", "sector": "Agriculture"},
        {"ticker": "BATZ", "name": "British American Tobacco Zambia", "sector": "Consumer Goods"},
        {"ticker": "LAFA", "name": "Lafarge Zambia", "sector": "Industrial"},
    ]

    print("Seeding Securities...")
    for t in tickers:
        try:
            service.create_ticker(t["ticker"], t["name"], t["sector"])
            print(f"Created {t['ticker']}")
        except Exception:
            print(f"Skipping {t['ticker']} (already exists)")
            db.rollback()

    # 2. Seed Price History (Last 1 year)
    print("Seeding Price History...")
    start_date = date.today() - timedelta(days=365)
    
    # Base prices
    prices = {
        "CECZ": 3.50, "ZANACO": 4.20, "SCBL": 2.10, "SHOP": 65.00,
        "REIZ": 1.50, "ZSUG": 12.00, "BATZ": 3.80, "LAFA": 5.50
    }
    
    # Volatility & Liquidity profiles
    # Liquidity: Probability of trading on any given day
    liquidity = {
        "CECZ": 0.8, "ZANACO": 0.9, "SCBL": 0.6, "SHOP": 0.3,
        "REIZ": 0.1, "ZSUG": 0.5, "BATZ": 0.2, "LAFA": 0.4
    }

    current_date = start_date
    while current_date <= date.today():
        for ticker, base_price in prices.items():
            if random.random() < liquidity[ticker]:
                # Random walk
                change = random.uniform(-0.02, 0.02)
                prices[ticker] = max(0.01, prices[ticker] * (1 + change))
                
                # Volume simulation
                vol = int(random.expovariate(1/1000)) + 100
                
                service.ingest_price(ticker, round(prices[ticker], 2), vol, current_date)
        
        current_date += timedelta(days=1)
        if current_date.day == 1:
            print(f"Processed up to {current_date}")

    db.close()
    print("Seeding Complete.")

if __name__ == "__main__":
    seed()
