#!/usr/bin/env python3
"""
Scrape stock prices from African Financials for LuSE securities.
https://africanfinancials.com/lusaka-securities-exchange-share-prices/
"""

import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://africanfinancials.com/lusaka-securities-exchange-share-prices/"

def scrape_luse_stocks():
    """Scrape all LuSE stock data from African Financials."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    session = requests.Session()
    response = session.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    stocks = []
    
    # Find all company entries - they typically have a pattern
    # Looking for company names and prices in the page
    
    # Method 1: Look for data table
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        print(f"\nTable {i}: {len(rows)} rows")
        for row in rows[:10]:  # Print first 10 rows
            cols = row.find_all(['td', 'th'])
            text = [col.get_text(strip=True) for col in cols]
            if text:
                print(f"  Row: {text}")
    
    # Method 2: Look for company links/cards
    print("\n\nLooking for company links...")
    company_links = soup.find_all('a', href=re.compile(r'/company/zm-'))
    for link in company_links[:20]:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        print(f"  Link: {text} -> {href}")
    
    # Method 3: Look for price patterns in the text
    print("\n\nLooking for price patterns...")
    price_pattern = re.compile(r'(\d+\.?\d*)\s*Kwacha')
    matches = price_pattern.findall(response.text)
    print(f"Found {len(matches)} price matches: {matches[:10]}")
    
    # Method 4: Look for specific elements
    print("\n\nLooking for specific elements...")
    
    # Look for divs/elements that might contain stock info
    stock_divs = soup.find_all('div', class_=re.compile(r'stock|price|company', re.I))
    print(f"Found {len(stock_divs)} stock-related divs")
    
    # Look for the LUSE-ASI index
    index_match = re.search(r'LUSE-ASI[^\d]*(\d[\d,\.]*)', response.text)
    if index_match:
        print(f"\nLASI Index: {index_match.group(1)}")
    
    # Look for exchange rate
    rate_match = re.search(r'ZAMBIA KWACHA[^\d]*(\d+\.?\d*)', response.text)
    if rate_match:
        print(f"USD/ZMW Rate: {rate_match.group(1)}")
    
    return stocks

if __name__ == "__main__":
    stocks = scrape_luse_stocks()
    print(f"\n\nTotal stocks found: {len(stocks)}")
    for stock in stocks:
        print(stock)
