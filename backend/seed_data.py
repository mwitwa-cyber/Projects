
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

# Try to import currency service for live exchange rate
try:
    from app.services.currency import get_usd_zmw_rate
    USD_TO_ZMW = get_usd_zmw_rate()
except ImportError:
    USD_TO_ZMW = 22.50  # Fallback rate

def seed():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    service = MarketDataService(db)
    
    print(f"USD/ZMW Exchange Rate: {USD_TO_ZMW}")

    # 1. Create Securities (Full LuSE List - Updated from AfricanFinancials.com Dec 31, 2025)
    tickers = [
        # Mining & Basic Materials
        {"ticker": "AECI", "name": "AECI Mining Explosives PLC", "sector": "Engineering", "price": 130.00},
        {"ticker": "ZCCM", "name": "ZCCM Investments Holdings Plc", "sector": "Investment", "price": 166.00},
        {"ticker": "ZFCO", "name": "Zambia Forestry and Forest Industries", "sector": "Basic Materials", "price": 3.57},
        
        # Telecommunications & Technology
        {"ticker": "ATEL", "name": "Airtel Networks Zambia Plc", "sector": "Technology", "price": 137.73},
        {"ticker": "DCZM", "name": "Dot Com Zambia Plc", "sector": "Technology", "price": 12.30},  # IPO price
        
        # Banking & Financials
        {"ticker": "SCBL", "name": "Standard Chartered Bank Zambia Plc", "sector": "Banking", "price": 2.55},
        {"ticker": "ZNCO", "name": "Zanaco Plc", "sector": "Banking", "price": 5.98},
        {"ticker": "MAFS", "name": "Madison Financial Services", "sector": "Financials", "price": 1.81},
        {"ticker": "ZMRE", "name": "Zambia Reinsurance Plc", "sector": "Financials", "price": 2.70},
        {"ticker": "CCAF", "name": "CEC Africa Investment", "sector": "Financials", "price": 0.83},
        
        # Energy & Utilities
        {"ticker": "CECZ", "name": "Copperbelt Energy Corporation Plc", "sector": "Energy", "price": 19.30},
        {"ticker": "PUMA", "name": "Puma Energy Zambia Plc", "sector": "Energy", "price": 4.00},
        
        # Consumer Goods & Agri-Industrial
        {"ticker": "ZMBF", "name": "Zambeef Products Plc", "sector": "Agri-Industrial", "price": 2.20},
        {"ticker": "ZSUG", "name": "Zambia Sugar Plc", "sector": "Agri-Industrial", "price": 66.97},
        {"ticker": "BATA", "name": "Bata Shoe Company Zambia Plc", "sector": "Consumer Goods", "price": 6.53},
        {"ticker": "BATZ", "name": "British American Tobacco Zambia Plc", "sector": "Consumer Goods", "price": 14.25},
        {"ticker": "ZABR", "name": "Zambian Breweries Plc", "sector": "Consumer Goods", "price": 7.01},
        {"ticker": "NATB", "name": "National Breweries Plc", "sector": "Consumer Goods", "price": 2.99},
        
        # Industrial
        {"ticker": "CHIL", "name": "Chilanga Cement Plc", "sector": "Industrials", "price": 80.00},
        {"ticker": "ZMFA", "name": "Metal Fabricators of Zambia Plc", "sector": "Engineering", "price": 60.00},
        
        # Retail
        {"ticker": "SHOP", "name": "Shoprite Holdings Zambia", "sector": "Retail", "price": 350.00},
        
        # Real Estate (USD-denominated - will be converted)
        {"ticker": "REIZ", "name": "Real Estate Investments Zambia Plc", "sector": "Property", "price": 0.09},  # USD
        
        # Hospitality
        {"ticker": "PMDZ", "name": "Pamodzi Hotel Plc", "sector": "Consumer Services", "price": 5.00},
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
    
    # Base prices as of 1 year ago (January 2025) - calculated from current prices
    # Current prices from AfricanFinancials.com (Jan 2, 2026)
    # LASI: 25,919.83 (+0.86% daily change)
    base_prices = {
        # Mining & Investment (High growth sector)
        "ZCCM": 98.89,      # ZCCM-IH (current: K166.00, +68%)
        "AECI": 77.44,      # AECI Mining Explosives (current: K130.00, +68%)
        "ZFCO": 2.13,       # ZAFFICO (current: K3.57, +68%)
        
        # Telecommunications & Technology (High growth)
        "ATEL": 43.50,      # Airtel Networks Zambia (current: K137.73, +217%)
        "DCZM": 12.30,      # Dot Com Zambia (IPO Dec 2025)
        
        # Banking & Financials
        "SCBL": 2.65,       # Standard Chartered (current: K2.55, -4%)
        "ZNCO": 3.56,       # Zanaco (current: K5.98, +68%)
        "MAFS": 1.08,       # Madison Financial (current: K1.81, +68%)
        "ZMRE": 1.61,       # Zambia Reinsurance (current: K2.70, +68%)
        "CCAF": 0.50,       # CEC Africa (current: K0.83, +66%)
        
        # Energy & Utilities
        "CECZ": 13.84,      # CEC (current: K19.30, +39%)
        "PUMA": 5.80,       # Puma Energy (current: K4.00, -31%)
        
        # Consumer Goods & Agri-Industrial
        "ZMBF": 2.13,       # Zambeef (current: K2.20, +3%)
        "ZSUG": 36.04,      # Zambia Sugar (current: K66.97, +86%)
        "BATA": 3.89,       # Bata (current: K6.53, +68%)
        "BATZ": 8.49,       # BAT Zambia (current: K14.25, +68%)
        "ZABR": 4.18,       # Zambian Breweries (current: K7.01, +68%)
        "NATB": 1.78,       # National Breweries (current: K2.99, +68%)
        
        # Industrial
        "CHIL": 47.66,      # Chilanga Cement (current: K80.00, +68%)
        "ZMFA": 35.74,      # ZAMEFA (current: K60.00, +68%)
        
        # Retail
        "SHOP": 208.50,     # Shoprite (current: K350.00, +68%)
        
        # Real Estate (USD-denominated)
        "REIZ": round(0.07 * USD_TO_ZMW, 2),  # USD 0.07 -> K (current: USD 0.09, +29%)
        
        # Hospitality
        "PMDZ": 2.98,       # Pamodzi Hotel (current: K5.00, +68%)
        
        # Government Bonds (Price per 100 face value)
        "GRZ-2Y": 98.50,    # 2 Year Bond
        "GRZ-3Y": 96.00,    # 3 Year Bond
        "GRZ-5Y": 92.00,    # 5 Year Bond
        "GRZ-10Y": 86.00,   # 10 Year Bond
        "GRZ-15Y": 82.00    # 15 Year Bond
    }
    
    # Current simulation state
    current_prices = base_prices.copy()

    # Volatility & Liquidity profiles based on LuSE trading volumes (from AfricanFinancials)
    # Higher liquidity = changes more often (based on actual 1Y liquidity data)
    liquidity_map = {
        # High liquidity (>K100M/year): CEC K615M, ATEL K205M, CECZ, ZCCM, etc.
        "High": ["CECZ", "ATEL", "ZNCO", "SCBL", "ZCCM", "ZSUG", "ZMBF", "CHIL", "SHOP",
                 "GRZ-2Y", "GRZ-3Y", "GRZ-5Y", "GRZ-10Y", "GRZ-15Y"],
        # Medium liquidity (K10M-K100M/year)
        "Medium": ["AECI", "BATZ", "ZABR", "PUMA", "NATB", "ZMFA", "REIZ"],
        # Low liquidity (<K10M/year)
        "Low": ["BATA", "MAFS", "ZMRE", "ZFCO", "DCZM", "PMDZ", "CCAF"]
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
