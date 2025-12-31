
from app.core.db import SessionLocal
from app.services.market_data import MarketDataService
from app.core.models import Security, MarketPrice
from datetime import date, timedelta
import random

def seed_today():
    db = SessionLocal()
    service = MarketDataService(db)
    
    today = date.today()
    print(f"Seeding for {today}...")

    # Get all securities
    securities = db.query(Security).all()
    
    for sec in securities:
        # Get latest price to walk from
        latest = service.get_price_as_of(sec.ticker, today - timedelta(days=1))
        
        start_price = latest.price if latest else 10.0
        
        # Random walk
        change = random.uniform(-0.02, 0.02)
        new_price = max(0.01, start_price * (1 + change))
        
        # Volume
        vol = random.randint(100, 5000)
        
        print(f"Updating {sec.ticker}: {start_price} -> {new_price:.2f}")
        service.ingest_price(sec.ticker, round(new_price, 2), vol, today)
        
    db.close()
    print("Seeding Complete.")

if __name__ == "__main__":
    seed_today()
