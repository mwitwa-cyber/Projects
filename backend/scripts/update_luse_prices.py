"""
Simple script to update database with real LuSE prices.
Avoids complex imports by using raw SQL.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from sqlalchemy import create_engine, text

# Real LuSE stock prices from afx.kwayisi.org (as of January 2, 2026)
REAL_PRICES = {
    "AECI": 130.00,
    "ATEL": 137.73,
    "BATA": 6.53,
    "BATZ": 14.25,
    "CCAF": 0.83,
    "CECZ": 19.28,
    "CHIL": 80.00,
    "DCZM": 12.30,
    "MAFS": 1.81,
    "NATB": 2.99,
    "PMDZ": 5.00,
    "PUMA": 4.00,
    "REIZ": 2.03,  # 0.09 USD * ~22.5 ZMW/USD
    "SCBL": 2.55,
    "SHOP": 350.00,
    "ZABR": 7.01,
    "ZCCM": 166.00,
    "ZFCO": 3.57,
    "ZMBF": 2.20,
    "ZMFA": 60.00,
    "ZMRE": 2.80,
    "ZNCO": 5.97,
    "ZSUG": 66.97,
}


def update_prices():
    """Update market_prices with real LuSE data."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/luse_quant")
    engine = create_engine(db_url)
    today = date.today()
    now = datetime.now()
    
    print("=" * 60)
    print(f"Updating LuSE prices as of {today}")
    print("=" * 60)
    
    with engine.connect() as conn:
        for ticker, price in REAL_PRICES.items():
            try:
                # Check if we already have a price for today
                result = conn.execute(text("""
                    SELECT id FROM market_prices 
                    WHERE security_ticker = :ticker 
                    AND DATE(valid_from) = :valid_date
                    AND transaction_to IS NULL
                """), {"ticker": ticker, "valid_date": today})
                
                existing = result.fetchone()
                
                if existing:
                    # Update existing record
                    conn.execute(text("""
                        UPDATE market_prices 
                        SET price = :price, transaction_from = :now
                        WHERE id = :id
                    """), {"price": price, "now": now, "id": existing[0]})
                    print(f"✓ {ticker:6} -> ZMW {price:>10.2f} (updated)")
                else:
                    # Insert new record
                    conn.execute(text("""
                        INSERT INTO market_prices (security_ticker, price, volume, valid_from, transaction_from)
                        VALUES (:ticker, :price, :volume, :valid_from, :now)
                    """), {
                        "ticker": ticker,
                        "price": price,
                        "volume": 0,
                        "valid_from": today,
                        "now": now
                    })
                    print(f"✓ {ticker:6} -> ZMW {price:>10.2f} (inserted)")
                    
            except Exception as e:
                print(f"✗ {ticker:6} -> Error: {e}")
        
        conn.commit()
    
    print("=" * 60)
    print("Update complete!")
    print("=" * 60)


def show_prices():
    """Show current prices in database."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/luse_quant")
    engine = create_engine(db_url)
    
    print("\n" + "=" * 60)
    print("Current prices in database vs Real prices")
    print("=" * 60)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT ON (security_ticker) 
                security_ticker, price, DATE(valid_from) as valid_date
            FROM market_prices 
            WHERE security_ticker NOT LIKE 'GRZ%'
            ORDER BY security_ticker, valid_from DESC
        """))
        
        for row in result:
            ticker, db_price, valid_date = row
            real_price = REAL_PRICES.get(ticker, None)
            if real_price:
                diff_pct = ((db_price - real_price) / real_price) * 100
                status = "✓" if abs(diff_pct) < 1 else "✗"
                print(f"{status} {ticker:6} | DB: {db_price:>8.2f} | Real: {real_price:>8.2f} | Diff: {diff_pct:>+6.1f}%")
            else:
                print(f"? {ticker:6} | DB: {db_price:>8.2f} | Real: N/A")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update database with real LuSE prices")
    parser.add_argument("--show", action="store_true", help="Show current prices")
    parser.add_argument("--update", action="store_true", help="Update with real prices")
    
    args = parser.parse_args()
    
    if args.show:
        show_prices()
    elif args.update:
        update_prices()
    else:
        print("Usage:")
        print("  python update_luse_prices.py --show    # Show current vs real prices")
        print("  python update_luse_prices.py --update  # Update DB with real prices")
