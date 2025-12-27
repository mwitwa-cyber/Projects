# 🔧 Scraper Quick Setup - Copy & Paste

Choose your provider below and follow the steps.

---

## Option A: Simulator (No Setup - Recommended for Dev)

**Why**: Works immediately, no API keys, good for testing.

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
export ENABLE_SCRAPER=true
export SCRAPER_PROVIDER=simulator
uvicorn app.main:app --reload

# Terminal 2: Test prices
curl "http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)"
```

**In docker**:
```bash
docker-compose up backend db redis
```

---

## Option B: AlphaVantage (Free API)

**Setup: 3 minutes**

### Step 1: Get API Key
```
Visit: https://www.alphavantage.co/
Click "Get Free API Key"
Paste email → confirm → copy API key
```

### Step 2: Run Scraper

```bash
# Export API key
export ALPHAVANTAGE_API_KEY=YOUR_KEY_HERE

# Run standalone scraper
cd backend
pip install -r requirements.txt
export SCRAPER_PROVIDER=alphavantage
export SCRAPER_INTERVAL=120
python scripts/run_scraper.py

# Or run with FastAPI backend
export ENABLE_SCRAPER=true
uvicorn app.main:app --reload
```

### Step 3: Test

```bash
curl "http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)"
```

---

## Option C: Finnhub (Free API, Better Limits)

**Setup: 3 minutes**

### Step 1: Get API Key
```
Visit: https://finnhub.io/
Sign up (free) → confirm email
Dashboard → Account → API Key
Copy and save
```

### Step 2: Run Scraper

```bash
export FINNHUB_API_KEY=YOUR_KEY_HERE

cd backend
export SCRAPER_PROVIDER=finnhub
export SCRAPER_INTERVAL=60
python scripts/run_scraper.py

# Or background
export ENABLE_SCRAPER=true
uvicorn app.main:app --reload
```

### Step 3: Test

```bash
curl "http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)"
```

---

## Option D: Docker (Production)

### Setup

```bash
# Create .env file in project root
cat > .env << 'EOF'
# Choose ONE provider API key
ALPHAVANTAGE_API_KEY=your_key_here
# FINNHUB_API_KEY=your_key_here
# IEXCLOUD_API_KEY=your_key_here
EOF

# Create docker/.env or add to docker-compose.yml
cat > .env.docker << 'EOF'
ENABLE_SCRAPER=true
SCRAPER_PROVIDER=alphavantage
SCRAPER_INTERVAL=120
EOF
```

### Run

```bash
# From project root
docker-compose up -d backend db redis

# View logs
docker-compose logs -f backend

# Test
curl "http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)"
```

---

## Comparing Providers

```
╔═══════════════╦══════════╦════════════╦═══════════╦════════════╗
║ Provider      ║ Free     ║ Setup Time ║ Rate Limit║ Best For   ║
╠═══════════════╬══════════╬════════════╬═══════════╬════════════╣
║ Simulator     ║ Yes      ║ 0 min      ║ ∞         ║ Dev/Demo   ║
║ AlphaVantage  ║ Yes      ║ 3 min      ║ 5/min     ║ Testing    ║
║ Finnhub       ║ Yes      ║ 3 min      ║ 300/min   ║ Production ║
║ IEX Cloud     ║ No       ║ 5 min      ║ 100k/mo   ║ Enterprise ║
╚═══════════════╩══════════╩════════════╩═══════════╩════════════╝
```

**Recommendation**: Start with **Finnhub** (best free tier for production).

---

## Common Issues & Fixes

### "API key not provided"

```bash
# Verify key is exported
echo $FINNHUB_API_KEY

# If empty, set it
export FINNHUB_API_KEY=your_key

# Then retry
python scripts/run_scraper.py
```

### "Symbol not found"

Try symbol mapping:

```bash
export SYMBOL_MAP_CECZ=CECZ.ZA
export SYMBOL_MAP_ZANACO=ZANACO.ZA

# Or switch provider
export SCRAPER_PROVIDER=yfinance
```

### "Rate limit exceeded"

Increase interval:

```bash
# For AlphaVantage (5 req/min):
export SCRAPER_INTERVAL=120

# For Finnhub (300 req/min):
export SCRAPER_INTERVAL=30
```

### Scraper not starting

```bash
# Check if enabled
echo $ENABLE_SCRAPER  # should be "true"

# Check logs
docker-compose logs backend | grep -i scraper

# Test standalone script
cd backend && python scripts/run_scraper.py
```

---

## Verify It's Working

### Check database

```bash
# Via adminer (http://localhost:8080)
# Connect to postgres:password@db:5432/luse_quant
# Query: SELECT * FROM market_prices ORDER BY valid_from DESC LIMIT 10;

# Or via curl
curl "http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)" | json_pp
```

### Monitor in real-time

```bash
# Terminal 1: Watch backend logs
docker-compose logs -f backend

# Terminal 2: Poll API every 10s
while true; do 
  curl -s "http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)" | json_pp
  sleep 10
done
```

---

## Next Steps

1. **Pick a provider** (recommend Finnhub for best free tier)
2. **Copy the command block above** for your provider
3. **Run it**
4. **Verify prices** are being ingested
5. **Monitor** logs for errors

For detailed docs, see: [SCRAPER_CONFIG.md](./SCRAPER_CONFIG.md)
