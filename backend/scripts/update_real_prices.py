"""
Update Database with Real LuSE Market Data from afx.kwayisi.org

This script:
1. Updates existing securities with current real prices
2. Does NOT delete historical data - appends new prices
3. Uses the LUSEProvider to fetch live data with cached fallback
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from app.core.db import SessionLocal
from app.core.models import Security
from app.services.market_data import MarketDataService
from app.services.luse_provider import LUSEProvider, CURRENT_REAL_PRICES


def update_with_real_prices():
    """Update the database with real LuSE prices."""
    db = SessionLocal()
    service = MarketDataService(db)
    provider = LUSEProvider()
    today = date.today()
    
    print("=" * 60)
    print(f"Updating LuSE prices as of {today}")
    print("=" * 60)
    
    # Get all securities (excluding bonds)
    securities = db.query(Security).filter(Security.type != "Bond").all()
    
    updated = 0
    failed = 0
    
    for sec in securities:
        ticker = sec.ticker
        
        # Try to fetch live price first
        result = provider.fetch_price(ticker)
        
        if result:
            price = result["price"]
            volume = result.get("volume", 0)
            
            # Ingest the new price
            try:
                service.ingest_price(ticker, price, volume, today)
                print(f"✓ {ticker:6} -> ZMW {price:>10.2f} (vol: {volume:,})")
                updated += 1
            except Exception as e:
                print(f"✗ {ticker:6} -> Error ingesting: {e}")
                failed += 1
        else:
            # Check if we have a cached price
            cached = CURRENT_REAL_PRICES.get(ticker)
            if cached:
                try:
                    service.ingest_price(ticker, cached, 0, today)
                    print(f"~ {ticker:6} -> ZMW {cached:>10.2f} (cached)")
                    updated += 1
                except Exception as e:
                    print(f"✗ {ticker:6} -> Error ingesting cached: {e}")
                    failed += 1
            else:
                print(f"✗ {ticker:6} -> No price available")
                failed += 1
    
    db.commit()
    db.close()
    
    print("=" * 60)
    print(f"Update complete: {updated} updated, {failed} failed")
    print("=" * 60)


def show_current_db_prices():
    """Show current prices in the database for comparison."""
    db = SessionLocal()
    
    print("\n" + "=" * 60)
    print("Current prices in database (most recent per ticker)")
    print("=" * 60)
    
    result = db.execute("""
        SELECT DISTINCT ON (security_ticker) 
            security_ticker, price, valid_from
        FROM market_prices 
        WHERE security_ticker NOT LIKE 'GRZ%'
        ORDER BY security_ticker, valid_from DESC
    """)
    
    for row in result:
        ticker, price, valid_from = row
        real_price = CURRENT_REAL_PRICES.get(ticker, "N/A")
        diff = ""
        if isinstance(real_price, (int, float)):
            pct_diff = ((price - real_price) / real_price) * 100 if real_price else 0
            diff = f"({pct_diff:+.1f}%)"
        print(f"{ticker:6} -> DB: ZMW {price:>10.2f} | Real: {real_price:>10} {diff}")
    
    db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update database with real LuSE prices")
    parser.add_argument("--show", action="store_true", help="Show current DB prices without updating")
    parser.add_argument("--update", action="store_true", help="Update prices with real data")
    
    args = parser.parse_args()
    
    if args.show:
        show_current_db_prices()
    elif args.update:
        update_with_real_prices()
    else:
        print("Usage:")
        print("  python update_real_prices.py --show    # Show current DB prices")
        print("  python update_real_prices.py --update  # Update with real prices")
