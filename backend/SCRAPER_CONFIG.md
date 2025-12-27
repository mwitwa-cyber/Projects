# 🔌 LuSE Scraper Configuration Guide

## Overview

The market-data scraper supports multiple providers with pluggable API strategies:

| Provider | Type | Free Tier | Rate Limit | Setup |
|----------|------|-----------|-----------|-------|
| **Simulator** | Demo | Yes | N/A | No API key needed |
| **YFinance** | Free | Yes | ~200/day | No API key needed |
| **AlphaVantage** | Freemium | Yes | 5 req/min | Free API key |
| **Finnhub** | Freemium | Yes | ~300/min | Free API key |
| **IEX Cloud** | Commercial | No | 100k/month | Paid API key |

---

## 🚀 Quick Start

### Option 1: Simulator (Default - No Setup)

```bash
# Start backend with default simulator provider
export SCRAPER_PROVIDER=simulator
export SCRAPER_INTERVAL=60
export ENABLE_SCRAPER=true

python scripts/run_scraper.py
# or
uvicorn app.main:app --reload
```

**When to use**: Development, testing, demos (doesn't require real market data).

---

### Option 2: YFinance (Free, No API Key)

```bash
export SCRAPER_PROVIDER=yfinance
export SCRAPER_INTERVAL=60
export ENABLE_SCRAPER=true

python scripts/run_scraper.py
```

**Pros**: Free, no signup required.
**Cons**: May be rate-limited or blocked; unofficial API.
**Best for**: Small personal projects.

---

### Option 3: AlphaVantage (Free Tier)

**Step 1: Get Free API Key**
1. Visit: https://www.alphavantage.co/
2. Click "Get Free API Key"
3. Enter your email, submit
4. Copy your API key from confirmation email

**Step 2: Configure**

```bash
# Create backend/.env or set environment variables
export ALPHAVANTAGE_API_KEY=your_api_key_here
export SCRAPER_PROVIDER=alphavantage
export SCRAPER_INTERVAL=120  # 12s rate limit, so 120s+ between runs
export ENABLE_SCRAPER=true

# Optional: Map local tickers to AlphaVantage symbols
# (e.g., if "CECZ" isn't recognized, map to "CECZ.ZA" or similar)
export SYMBOL_MAP_CECZ=CECZ.ZA

python scripts/run_scraper.py
```

**Pros**: 
- Free tier: 5 requests/minute
- Reliable
- Supports 1000+ symbols
- Rate limiting built-in

**Cons**:
- 5 req/min on free tier
- Not all Zambian stocks may be available
- Requires symbol mapping for some tickers

**API Docs**: https://www.alphavantage.co/documentation/

---

### Option 4: Finnhub (Free Tier)

**Step 1: Get Free API Key**
1. Visit: https://finnhub.io/
2. Sign up (free account)
3. Go to dashboard → Account → API Key
4. Copy your API key

**Step 2: Configure**

```bash
export FINNHUB_API_KEY=your_api_key_here
export SCRAPER_PROVIDER=finnhub
export SCRAPER_INTERVAL=60
export ENABLE_SCRAPER=true

# Optional symbol mapping
export SYMBOL_MAP_CECZ=CECZ

python scripts/run_scraper.py
```

**Pros**:
- Free tier: ~300 requests/minute
- Very fast
- Good coverage
- Real-time data

**Cons**:
- Zambian stocks limited coverage
- May need to use international equivalents (e.g., JSE tickers)

**API Docs**: https://finnhub.io/docs/api

---

### Option 5: IEX Cloud (Commercial)

**Step 1: Sign Up**
1. Visit: https://iexcloud.io/
2. Create account (free tier with limited requests)
3. Copy API key from dashboard

**Step 2: Configure**

```bash
export IEXCLOUD_API_KEY=your_api_key_here
export SCRAPER_PROVIDER=iexcloud
export IEXCLOUD_SANDBOX=false      # set to true to use sandbox
export SCRAPER_INTERVAL=60
export ENABLE_SCRAPER=true

python scripts/run_scraper.py
```

**Pros**:
- Most reliable
- Best data quality
- High rate limits
- Sandbox available for testing

**Cons**:
- Paid after free tier
- Primarily US stocks

**API Docs**: https://iexcloud.io/docs/

---

## 🔄 Running the Scraper

### Standalone (Recommended for Testing)

```bash
cd backend

# Install dependencies first
pip install -r requirements.txt

# Run scraper script
python scripts/run_scraper.py
```

**Output**:
```
Scraper started with provider: simulator, interval: 60s
# (logs every 60s when price updates are ingested)
```

Stop with `Ctrl+C`.

### Background (Inside FastAPI)

```bash
# Set ENABLE_SCRAPER=true before starting backend
export ENABLE_SCRAPER=true
export SCRAPER_PROVIDER=alphavantage
export ALPHAVANTAGE_API_KEY=your_key

# Start backend normally
uvicorn app.main:app --reload

# Scraper runs in background, ingesting prices while API responds to requests
```

### Docker (Production)

Update `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - ENABLE_SCRAPER=true
      - SCRAPER_PROVIDER=alphavantage
      - ALPHAVANTAGE_API_KEY=${ALPHAVANTAGE_API_KEY}
      - SCRAPER_INTERVAL=120
      - DATABASE_URL=postgresql://postgres:password@db:5432/luse_quant
```

Then:

```bash
# Create .env file in project root
echo "ALPHAVANTAGE_API_KEY=your_key_here" >> .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

---

## 🎯 Symbol Mapping

If your ticker symbols don't match the provider's format, use environment variable mapping:

```bash
# Map local "CECZ" to "CECZ.ZA" on AlphaVantage
export SYMBOL_MAP_CECZ=CECZ.ZA
export SYMBOL_MAP_ZANACO=ZANACO.ZA
export SYMBOL_MAP_SCBL=SCBL.ZA

# Map to international equivalents if needed
export SYMBOL_MAP_CECZ=CECZ  # try direct first
# If that fails, try:
export SYMBOL_MAP_CECZ=ZWL:CECZ  # currency-prefixed
```

**Common Zambian mappings**:
- CECZ → CECZ (or CECZ.ZA)
- ZANACO → ZANACO (or ZANACO.ZA)
- SCBL → SCBL (or SCBL.ZA)
- JSE tickers (South Africa) → Add .JO suffix

---

## 🛡️ Fallback & Error Handling

The scraper implements intelligent fallback:

1. **Try primary provider** (AlphaVantage, Finnhub, etc.)
2. **If API fails** → Fall back to simulator
3. **Continue ingesting** with simulated data (prevents scraper crash)
4. **Retry next cycle** (provider may come back online)

This ensures your scraper is **resilient to API outages**.

---

## ⚡ Performance Tips

### Rate Limiting

Set `SCRAPER_INTERVAL` based on your needs:

```bash
# For AlphaVantage (5 req/min = 12s per request)
# If you have 8 tickers, need 8*12=96s minimum
export SCRAPER_INTERVAL=120

# For Finnhub (300 req/min = 200ms between requests)
# 8 tickers = ~1.6s, so safe interval is 60s
export SCRAPER_INTERVAL=60

# For simulator (unlimited)
export SCRAPER_INTERVAL=10
```

### Database Optimization

Add indexes for faster lookups:

```sql
-- In PostgreSQL (optional, accelerates price lookups)
CREATE INDEX idx_bitemporal_lookup 
ON market_prices(security_ticker, valid_from, transaction_to);
```

---

## 🔍 Monitoring & Debugging

### Check if scraper is running

```bash
# View recent prices in database
# (from PostgreSQL client or via API endpoint)
curl "http://localhost:8000/api/v1/market-data/market-summary?date=2025-12-27"
```

### View backend logs

```bash
# If using docker-compose
docker-compose logs -f backend

# If running locally
# (logs print to stdout)
```

### Test API key manually

```bash
# AlphaVantage
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=CECZ&apikey=YOUR_KEY"

# Finnhub
curl "https://finnhub.io/api/v1/quote?symbol=CECZ&token=YOUR_KEY"

# IEX Cloud
curl "https://cloud.iexapis.com/stable/data/core/quote/CECZ?token=YOUR_KEY"
```

---

## 📋 Environment Variables Reference

### Core Scraper

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_SCRAPER` | `false` | Enable scraper on startup (true/1/yes) |
| `SCRAPER_PROVIDER` | `simulator` | Provider: simulator, yfinance, alphavantage, finnhub, iexcloud |
| `SCRAPER_INTERVAL` | `60` | Seconds between scraper runs |

### Provider-Specific

| Variable | Provider | Description |
|----------|----------|-------------|
| `ALPHAVANTAGE_API_KEY` | AlphaVantage | Your API key from alphavantage.co |
| `FINNHUB_API_KEY` | Finnhub | Your API key from finnhub.io |
| `IEXCLOUD_API_KEY` | IEX Cloud | Your API key from iexcloud.io |
| `IEXCLOUD_SANDBOX` | IEX Cloud | Use sandbox: true/false |

### Symbol Mapping

| Variable Pattern | Description |
|-----------------|-------------|
| `SYMBOL_MAP_*` | Map local ticker to provider format. E.g., `SYMBOL_MAP_CECZ=CECZ.ZA` |

---

## 📚 Examples

### Example 1: Development (Simulator)

```bash
# backend/.env
ENABLE_SCRAPER=true
SCRAPER_PROVIDER=simulator
SCRAPER_INTERVAL=10
DATABASE_URL=postgresql://postgres:password@localhost:5432/luse_quant
```

```bash
# Start
cd backend
python scripts/run_scraper.py
```

### Example 2: Testing with AlphaVantage

```bash
# backend/.env
ENABLE_SCRAPER=true
SCRAPER_PROVIDER=alphavantage
ALPHAVANTAGE_API_KEY=demo  # use their demo key or sign up for free
SCRAPER_INTERVAL=120
SYMBOL_MAP_CECZ=CECZ
SYMBOL_MAP_ZANACO=ZANACO
DATABASE_URL=postgresql://postgres:password@localhost:5432/luse_quant
```

```bash
cd backend
python scripts/run_scraper.py
```

### Example 3: Production with Finnhub

```bash
# backend/.env
ENABLE_SCRAPER=true
SCRAPER_PROVIDER=finnhub
FINNHUB_API_KEY=your_api_key
SCRAPER_INTERVAL=60
DATABASE_URL=postgresql://postgres:password@db:5432/luse_quant
```

```bash
# docker-compose.yml
services:
  backend:
    environment:
      ENABLE_SCRAPER: 'true'
      SCRAPER_PROVIDER: finnhub
      FINNHUB_API_KEY: ${FINNHUB_API_KEY}
      DATABASE_URL: postgresql://postgres:password@db:5432/luse_quant
```

```bash
# .env (project root)
FINNHUB_API_KEY=your_actual_key

# Start
docker-compose up -d
```

---

## 🚨 Troubleshooting

### Scraper not running

```bash
# Check if ENABLE_SCRAPER is set
echo $ENABLE_SCRAPER  # should be "true" or "1"

# Check backend startup logs
docker-compose logs backend | grep -i scraper

# Try standalone script
cd backend && python scripts/run_scraper.py
```

### "No API key provided"

```bash
# Verify API key is set
echo $ALPHAVANTAGE_API_KEY  # should not be empty

# Restart with key in environment
export ALPHAVANTAGE_API_KEY=your_key
python scripts/run_scraper.py
```

### "Symbol not found"

The provider doesn't recognize your ticker. Try:

```bash
# Add symbol mapping
export SYMBOL_MAP_CECZ=CECZ.ZA

# Or switch to another provider
export SCRAPER_PROVIDER=yfinance
```

### Very slow scraping

You may be hitting rate limits. Increase interval:

```bash
# Current: 10 requests in 60s
# Increase to 120s if using AlphaVantage
export SCRAPER_INTERVAL=120
```

### API key rate limit exceeded

```bash
# AlphaVantage: Wait until next minute / upgrade account
# Finnhub: 300/min usually sufficient; upgrade if needed
# IEX Cloud: Check your plan; upgrade if needed

# Temporary workaround: use simulator
export SCRAPER_PROVIDER=simulator
```

---

## 📞 API Provider Links

- **AlphaVantage**: https://www.alphavantage.co/ (Free: 5 req/min)
- **Finnhub**: https://finnhub.io/ (Free: 60 req/min)
- **IEX Cloud**: https://iexcloud.io/ (Free tier available)
- **YFinance**: https://github.com/ranaroussi/yfinance (Unofficial, free)

---

## 🎓 Next Steps

1. **Choose a provider** (start with simulator, then try Finnhub for free real data)
2. **Get API key** (if needed)
3. **Set environment variables**
4. **Start backend** with `ENABLE_SCRAPER=true`
5. **Monitor prices** via API: `GET /api/v1/market-data/market-summary`
6. **Scale up** (add more securities, optimize rate limits, upgrade to paid tier if needed)

---

**Happy scraping!** 🚀
