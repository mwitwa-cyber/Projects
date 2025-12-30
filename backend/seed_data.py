
from app.core.db import SessionLocal, engine, Base
from app.services.market_data import MarketDataService
from datetime import date, timedelta
import random

# Import all models to ensure all tables are registered with SQLAlchemy's metadata
import app.models.user
import app.models.asset
import app.models.price_history
import app.models.portfolio
import app.models.yield_curve
import app.models.market_data

def seed():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    service = MarketDataService(db)

    # 1. Create Securities (Full LuSE List)
    tickers = [
        {"ticker": "AECI", "name": "AECI Mining Explosives", "sector": "Basic Materials"},
        {"ticker": "ATEL", "name": "Airtel Networks Zambia", "sector": "Telecommunications"},
        {"ticker": "BATA", "name": "Zambia Bata Shoe Company", "sector": "Consumer Goods"},
        {"ticker": "BATZ", "name": "British American Tobacco Zambia", "sector": "Consumer Goods"},
        {"ticker": "CCAF", "name": "CEC Africa Investment", "sector": "Financials"},
        {"ticker": "CECZ", "name": "Copperbelt Energy Corporation", "sector": "Utilities"},
        {"ticker": "CHIL", "name": "Chilanga Cement", "sector": "Industrials"},
        {"ticker": "DCZM", "name": "Dot Com Zambia", "sector": "Technology"},
        {"ticker": "FQMZ", "name": "First Quantum Minerals", "sector": "Basic Materials"},
        {"ticker": "MAFS", "name": "Madison Financial Services", "sector": "Financials"},
        {"ticker": "NATB", "name": "National Breweries", "sector": "Consumer Goods"},
        {"ticker": "PMDZ", "name": "Pamodzi Hotel", "sector": "Consumer Services"},
        {"ticker": "PUMA", "name": "Puma Energy Zambia", "sector": "Energy"},
        {"ticker": "REIZ", "name": "Real Estate Investments Zambia", "sector": "Real Estate"},
        {"ticker": "SCBL", "name": "Standard Chartered Bank Zambia", "sector": "Banking"},
        {"ticker": "SHOP", "name": "Shoprite Holdings", "sector": "Retail"},
        {"ticker": "ZABR", "name": "Zambian Breweries", "sector": "Consumer Goods"},
        {"ticker": "ZMBF", "name": "Zambeef Products", "sector": "Consumer Goods"},
        {"ticker": "ZMFA", "name": "Metal Fabricators of Zambia", "sector": "Industrials"},
        {"ticker": "ZMRE", "name": "Zambia Reinsurance", "sector": "Financials"},
        {"ticker": "ZNCO", "name": "Zambia National Commercial Bank", "sector": "Banking"},
        {"ticker": "ZSUG", "name": "Zambia Sugar", "sector": "Consumer Goods"},
        {"ticker": "ZCCM", "name": "ZCCM Investments Holdings", "sector": "Basic Materials"},
        {"ticker": "ZFCO", "name": "Zambia Forestry and Forest Industries", "sector": "Basic Materials"},
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
    
    # Base prices (approximate historical starts)
    base_prices = {
        "AECI": 25.00, "ATEL": 22.00, "BATA": 3.50, "BATZ": 2.80, "CCAF": 0.20,
        "CECZ": 3.50, "CHIL": 14.50, "DCZM": 1.00, "FQMZ": 18.00, "MAFS": 2.10,
        "NATB": 7.50, "PMDZ": 0.80, "PUMA": 1.90, "REIZ": 0.90, "SCBL": 2.10,
        "SHOP": 65.00, "ZABR": 6.80, "ZMBF": 1.50, "ZMFA": 4.20, "ZMRE": 5.00,
        "ZNCO": 4.20, "ZSUG": 12.00, "ZCCM": 45.00, "ZFCO": 2.50
    }
    
    # Current simulation state
    current_prices = base_prices.copy()

    # Volatility & Liquidity profiles
    # Higher liquidity = changes more often
    liquidity_map = {
        "High": ["CECZ", "ZNCO", "SCBL", "SHOP", "ZABR", "ZSUG", "ATEL", "FQMZ", "ZCCM"],
        "Medium": ["AECI", "CHIL", "PUMA", "ZMBF", "BATZ", "ZMRE", "ZFCO"],
        "Low": ["BATA", "CCAF", "DCZM", "MAFS", "NATB", "PMDZ", "REIZ", "ZMFA"]
    }
    
    def get_liquidity(ticker):
        if ticker in liquidity_map["High"]: return 0.8
        if ticker in liquidity_map["Medium"]: return 0.4
        return 0.1

    import random
    current_date = start_date
    while current_date <= date.today():
        for t in tickers:
            ticker = t["ticker"]
            prob = get_liquidity(ticker)
            
            if random.random() < prob:
                # Random walk
                change = random.uniform(-0.03, 0.035) # Slight upward drift
                current_prices[ticker] = max(0.01, current_prices[ticker] * (1 + change))
                
                # Volume simulation based on liquidity
                base_vol = 1000 if prob > 0.5 else 100
                vol = int(random.expovariate(1/base_vol)) + 10
                
                service.ingest_price(ticker, round(current_prices[ticker], 2), vol, current_date)
        
        current_date += timedelta(days=1)
        if current_date.day == 1:
            print(f"Processed up to {current_date}")

    db.close()
    print("Seeding Complete.")

if __name__ == "__main__":
    seed()
