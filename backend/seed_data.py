
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

    # 1.1 Seed Bonds (Government)
    bonds = [
        {"ticker": "GRZ-2Y", "name": "GRZ 2 Year Bond", "coupon": 0.09, "maturity": date.today() + timedelta(days=365*2)},
        {"ticker": "GRZ-3Y", "name": "GRZ 3 Year Bond", "coupon": 0.11, "maturity": date.today() + timedelta(days=365*3)},
        {"ticker": "GRZ-5Y", "name": "GRZ 5 Year Bond", "coupon": 0.13, "maturity": date.today() + timedelta(days=365*5)},
        {"ticker": "GRZ-10Y", "name": "GRZ 10 Year Bond", "coupon": 0.15, "maturity": date.today() + timedelta(days=365*10)},
        {"ticker": "GRZ-15Y", "name": "GRZ 15 Year Bond", "coupon": 0.16, "maturity": date.today() + timedelta(days=365*15)},
    ]
    
    print("Seeding Bonds...")
    for b in bonds:
        try:
            service.create_ticker(
                ticker=b["ticker"], 
                name=b["name"], 
                sector="Government Bonds",
                security_type="Bond",
                maturity_date=b["maturity"],
                coupon_rate=b["coupon"]
            )
            print(f"Created {b['ticker']}")
        except Exception as e:
            print(f"Skipping {b['ticker']} ({str(e)})")
            db.rollback()

    # 2. Seed Price History (Last 1 year)
    print("Seeding Price History...")
    start_date = date.today() - timedelta(days=365)
    
    # Base prices as of 1 year ago (January 2025) - realistic LuSE historical values
    # These will drift toward current prices over the simulation period
    base_prices = {
        # Banking & Financials
        "ZNCO": 5.20,       # Zanaco
        "SCBL": 2.20,       # Standard Chartered Bank Zambia
        "MAFS": 2.00,       # Madison Financial Services
        "CCAF": 0.65,       # CEC Africa Investment
        "ZMRE": 4.80,       # Zambia Reinsurance
        
        # Mining & Basic Materials  
        "ZCCM": 140.00,     # ZCCM-IH
        "AECI": 100.00,     # AECI Mining Explosives
        "FQMZ": 10.00,      # First Quantum Minerals
        "ZFCO": 3.00,       # ZAFFICO
        
        # Telecommunications
        "ATEL": 115.00,     # Airtel Networks Zambia
        
        # Consumer Goods
        "BATZ": 12.50,      # British American Tobacco Zambia
        "BATA": 5.80,       # Bata Zambia
        "ZMBF": 1.85,       # Zambeef Products
        "ZSUG": 58.00,      # Zambia Sugar
        "ZABR": 6.50,       # Zambian Breweries
        "NATB": 7.80,       # National Breweries
        
        # Industrial & Utilities
        "CECZ": 16.00,      # Copperbelt Energy Corporation
        "CHIL": 65.00,      # Chilanga Cement
        "ZMFA": 4.20,       # ZAMEFA
        
        # Energy
        "PUMA": 3.50,       # Puma Energy Zambia
        
        # Retail
        "SHOP": 300.00,     # Shoprite Holdings
        
        # Real Estate & Hospitality
        "REIZ": 0.07,       # Real Estate Investments Zambia
        "PMDZ": 0.85,       # Taj Pamodzi Hotel
        
        # Technology
        "DCZM": 19.50,      # Dot Com Zambia
        
        # Government Bonds (Price per 100 face value)
        "GRZ-2Y": 98.50,    # 2 Year Bond
        "GRZ-3Y": 96.00,    # 3 Year Bond
        "GRZ-5Y": 92.00,    # 5 Year Bond
        "GRZ-10Y": 86.00,   # 10 Year Bond
        "GRZ-15Y": 82.00    # 15 Year Bond
    }
    
    # Current simulation state
    current_prices = base_prices.copy()

    # Volatility & Liquidity profiles
    # Higher liquidity = changes more often
    liquidity_map = {
        "High": ["CECZ", "ZNCO", "SCBL", "SHOP", "ZABR", "ZSUG", "ATEL", "FQMZ", "ZCCM", 
                 "GRZ-2Y", "GRZ-3Y", "GRZ-5Y", "GRZ-10Y", "GRZ-15Y"], # Bonds are liquid
        "Medium": ["AECI", "CHIL", "PUMA", "ZMBF", "BATZ", "ZMRE", "ZFCO"],
        "Low": ["BATA", "CCAF", "DCZM", "MAFS", "NATB", "PMDZ", "REIZ", "ZMFA"]
    }
    
    def get_liquidity(ticker):
        if ticker in liquidity_map["High"]: return 0.8
        if ticker in liquidity_map["Medium"]: return 0.4
        return 0.1

    all_tickers = [t["ticker"] for t in tickers] + [b["ticker"] for b in bonds]
    
    import random
    current_date = start_date
    while current_date <= date.today():
        for ticker in all_tickers:
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
