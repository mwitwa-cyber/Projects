
import sys
import os
import requests
from datetime import date, timedelta
import random

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

API_URL = "http://localhost:8000/api/v1/market-data"

def seed_securities():
    securities = [
        {"ticker": "ZANACO", "name": "Zambia National Commercial Bank", "sector": "Banking"},
        {"ticker": "CECZ", "name": "Copperbelt Energy Corporation", "sector": "Energy"},
        {"ticker": "SHOP", "name": "Shoprite Holdings", "sector": "Retail"},
        {"ticker": "SCBL", "name": "Standard Chartered Bank", "sector": "Banking"},
        {"ticker": "LAFARGE", "name": "Lafarge Zambia", "sector": "Industrial"},
        {"ticker": "AIRTEL", "name": "Airtel Networks Zambia", "sector": "Telecommunications"},
        {"ticker": "ZSUG", "name": "Zambia Sugar", "sector": "Consumer Goods"}
    ]

    print("Seeding Securities...")
    for sec in securities:
        try:
            response = requests.post(f"{API_URL}/tickers", json=sec)
            if response.status_code == 200:
                print(f"Created {sec['ticker']}")
            else:
                print(f"Failed to create {sec['ticker']}: {response.text}")
        except Exception as e:
            print(f"Error creating {sec['ticker']}: {e}")

def seed_prices():
    tickers = ["ZANACO", "CECZ", "SHOP", "SCBL", "LAFARGE", "AIRTEL", "ZSUG"]
    base_prices = {
        "ZANACO": 4.20,
        "CECZ": 3.80,
        "SHOP": 65.00,
        "SCBL": 2.10,
        "LAFARGE": 15.50,
        "AIRTEL": 45.00,
        "ZSUG": 12.30
    }

    start_date = date.today() - timedelta(days=30)
    
    print("Seeding Prices...")
    for ticker in tickers:
        current_price = base_prices[ticker]
        for i in range(31):
            day = start_date + timedelta(days=i)
            # Random walk
            change = random.uniform(-0.05, 0.05) * current_price
            current_price += change
            current_price = round(current_price, 2)
            
            data = {
                "ticker": ticker,
                "price": current_price,
                "volume": random.randint(100, 10000),
                "date": day.isoformat()
            }
            
            try:
                response = requests.post(f"{API_URL}/prices", json=data)
                if response.status_code != 200:
                    print(f"Failed to ingest price for {ticker} on {day}: {response.text}")
            except Exception as e:
                print(f"Error seeding price for {ticker}: {e}")
        print(f"Seeded prices for {ticker}")

if __name__ == "__main__":
    seed_securities()
    seed_prices()
