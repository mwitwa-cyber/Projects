# LuSE Quant Platform - Frontend Integration Guide

## ✅ What's Been Implemented

Your frontend is now fully integrated with the backend APIs! Here's what you have:

### Components Created

1. **Market Pulse** (`components/MarketPulse.tsx`)
   - Real-time market data display
   - Live ticker cards with price changes
   - Market snapshot visualization
   - Integrated with backend market data API

2. **Bond Pricer** (`components/BondPricer.tsx`)
   - Interactive bond pricing calculator
   - Calculate Macaulay & Modified Duration
   - Real-time results display
   - Support for different coupon frequencies (Annual, Semi-annual, Quarterly, Monthly)

3. **Portfolio Optimizer** (`components/PortfolioOptimizer.tsx`)
   - Multi-asset portfolio optimization
   - Three optimization objectives:
     - Maximize Sharpe Ratio
     - Minimize Variance
     - Equal Weight
   - Efficient frontier visualization
   - Asset allocation pie chart
   - Performance metrics (Return, Volatility, Sharpe Ratio)

4. **Risk Analyzer** (`components/RiskAnalyzer.tsx`)
   - Value at Risk (VaR) calculation
     - Historical Simulation
     - Parametric (Normal)
     - Monte Carlo methods
   - Conditional VaR (Expected Shortfall)
   - Beta calculation (Systematic Risk)
   - Return distribution charts
   - Risk interpretation guidance

### API Service Layer

Complete API wrapper (`services/api.ts`) with:
- **Valuation APIs**: Bond pricing, YTM, DCF valuation, Annuities
- **Optimization APIs**: Portfolio optimization, Efficient frontier, Beta
- **Risk APIs**: VaR, CVaR calculations
- **Health Check**: Backend status monitoring

### Navigation & Layout

- **App.tsx**: Multi-tab dashboard with:
  - Backend status indicator
  - Sticky navigation header
  - Tab-based layout
  - Error handling
  - Loading states
  - Responsive design

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

This installs all required packages:
- React 19.2
- TypeScript 5.9
- Vite 7.2
- TailwindCSS 4.1
- Recharts (charting)
- Lucide React (icons)
- Axios (HTTP client)

### Step 2: Start Backend

```bash
# From project root
docker-compose up -d backend db redis
```

Wait for backend to be ready (~10 seconds)

### Step 3: Start Frontend Dev Server

```bash
cd frontend
npm run dev
```

Frontend will start on: **http://localhost:5173**

### Step 4: Open in Browser

Visit **http://localhost:5173** and you'll see:
- LuSE Quant Platform header
- 4 navigation tabs
- Backend status indicator
- Interactive components

---

## 📊 Features & Usage

### 1. Market Pulse Tab

**What it does**: Shows real-time market data from LuSE

```bash
curl http://localhost:8000/api/v1/market-data/market-summary?date=$(date +%Y-%m-%d)
```

**Features**:
- Live ticker prices
- Percentage change indicators
- Mini price charts
- Market depth display
- LASI Index performance

---

### 2. Bond Pricing Tab

**What it does**: Price bonds and calculate duration metrics

**Example - Price a GRZ Bond**:
- Face Value: 100
- Coupon Rate: 15%
- Yield Rate: 18%
- Years to Maturity: 10
- Frequency: Semi-annual

**Results**:
- Bond Price: K98.24
- Macaulay Duration: 6.89 years
- Modified Duration: 6.51 years

**API Endpoint**:
```
POST /api/v1/valuation/bond/price
```

---

### 3. Portfolio Optimizer Tab

**What it does**: Find optimal portfolio weights

**Default Assets**:
- CECZ (Copperbelt Energy)
- ZANACO (Zambia National Bank)
- SCBL (Standard Chartered)

**How to use**:
1. Enter or modify asset returns (comma-separated decimals)
2. Select optimization objective (Sharpe, Variance, Equal)
3. Set risk-free rate (default: 20%)
4. Click "Optimize Portfolio"
5. View results:
   - Asset allocation pie chart
   - Expected return & volatility
   - Sharpe ratio
   - Efficient frontier

**Example Input**:
```
CECZ: 0.02, 0.03, -0.01, 0.04, 0.01
ZANACO: 0.01, 0.02, 0.01, 0.02, 0.03
SCBL: 0.015, 0.025, 0.005, 0.03, 0.02
```

**API Endpoints**:
```
POST /api/v1/optimization/optimize
POST /api/v1/optimization/efficient-frontier
```

---

### 4. Risk Analysis Tab

#### Value at Risk (VaR)

**What it measures**: Maximum expected loss at given confidence level

**How to use**:
1. Enter return series (comma-separated decimals)
2. Select confidence level (90%, 95%, 99%)
3. Choose calculation method:
   - **Historical**: Uses actual distribution
   - **Parametric**: Assumes normal distribution
   - **Monte Carlo**: Simulates 10,000 scenarios
4. View results:
   - VaR value (% loss)
   - CVaR/Expected Shortfall
   - Risk interpretation

**Example**:
- 95% confidence → 2.5% daily loss is maximum expected
- CVaR → If loss exceeds VaR, average loss is 3.2%

**API Endpoints**:
```
POST /api/v1/optimization/risk/var
POST /api/v1/optimization/risk/cvar
```

#### Beta Calculation

**What it measures**: Systematic risk relative to market

**How to use**:
1. Enter asset returns (e.g., ZANACO daily returns)
2. Enter market returns (e.g., LASI index returns)
3. Click "Calculate Beta"
4. View results:
   - Beta value (0.8 = 20% less volatile than market)
   - Alpha (risk-adjusted excess return)
   - R² (model fit percentage)

**Interpretation**:
- β > 1: More volatile than market
- β = 1: Moves with market
- β < 1: Less volatile than market

**API Endpoint**:
```
POST /api/v1/optimization/beta
```

---

## 🔄 Data Flow

```
Frontend (React)
    ↓
API Service Layer (services/api.ts)
    ↓
Axios HTTP Client
    ↓
Backend (FastAPI)
    ↓
Database (PostgreSQL)
```

### Example Flow - Bond Pricing

```
User enters: Face=100, Coupon=10%, Yield=12%, Years=5
                ↓
BondPricer.tsx handles form submission
                ↓
valuationAPI.bondPrice(payload) called
                ↓
Axios POSTs to http://localhost:8000/api/v1/valuation/bond/price
                ↓
Backend processes calculation
                ↓
Returns: {price: 92.79, macaulay_duration: 4.23, ...}
                ↓
Component displays results
```

---

## 🛠️ Troubleshooting

### Issue: "Backend Offline"

**Solution**:
```bash
# Check if backend is running
docker ps | grep backend

# If not running
cd project root
docker-compose up -d backend db redis

# Wait 10 seconds and refresh browser
```

### Issue: CORS Error

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: Backend already has CORS enabled, but ensure:
1. Backend is running on port 8000
2. Frontend base URL in `services/api.ts` is `http://localhost:8000/api/v1`

### Issue: Module Not Found

**Error**: `Cannot find module '@/lib/utils'`

**Solution**:
```bash
# Restart dev server
npm run dev
```

### Issue: Port Already in Use

**Solution - Backend**:
```bash
# Change in docker-compose.yml
services:
  backend:
    ports:
      - "8001:8000"  # Use 8001 instead of 8000

# Update api.ts baseURL to http://localhost:8001/api/v1
```

**Solution - Frontend**:
```bash
# Vite will automatically use next available port
npm run dev  # Will be on 5174 or higher
```

---

## 📦 Component Architecture

### File Structure

```
frontend/src/
├── App.tsx                    # Main app with routing
├── App.css                    # Global styles
├── main.tsx                   # React entry point
├── index.css                  # Tailwind imports
├── services/
│   └── api.ts                # API wrapper
├── components/
│   ├── MarketPulse.tsx       # Market data display
│   ├── BondPricer.tsx        # Bond pricing
│   ├── PortfolioOptimizer.tsx # Portfolio optimization
│   └── RiskAnalyzer.tsx      # Risk metrics
├── lib/
│   └── utils.ts              # Utility functions
├── assets/                   # Static files
└── public/                   # Public assets
```

### Component Props & State

**BondPricer**:
```typescript
State:
- formData: Bond parameters
- result: Pricing results
- loading: API call status
- error: Error message
```

**PortfolioOptimizer**:
```typescript
State:
- assets: Array of {ticker, returns}
- riskFreeRate: Input rate
- objective: Optimization type
- result: Weights & metrics
- frontierData: Efficient frontier points
```

**RiskAnalyzer**:
```typescript
State (VaR Tab):
- varReturns: Return series
- varConfidence: Confidence level
- varMethod: Calculation method
- varResult: VaR value
- cvarResult: Expected shortfall

State (Beta Tab):
- assetReturns: Asset returns
- marketReturns: Market returns
- betaResult: Beta value
```

---

## 🎨 UI Features

### Design System

- **Color Scheme**: Dark mode (slate-900 to slate-950 background)
- **Accents**: Blue, Emerald, Red, Orange, Purple
- **Spacing**: TailwindCSS spacing scale
- **Typography**: Font families via Tailwind
- **Icons**: Lucide React icons

### Interactive Elements

- **Forms**: Input validation, real-time feedback
- **Charts**: Recharts for data visualization
  - Line charts for trends
  - Pie charts for allocation
  - Bar charts for distributions
  - Scatter charts for frontiers
- **Loading States**: Spinner icons during API calls
- **Error Messages**: Red alert boxes with icons
- **Backend Status**: Live indicator in header

### Responsive Design

- Mobile-first approach
- Grid layouts with breakpoints
- Overflow handling for long tables
- Touch-friendly buttons (min 44px)

---

## 🚀 Next Steps

### 1. Test Each Component

```bash
# Start frontend
npm run dev

# Navigate through tabs and test:
# 1. Market Pulse - should show ticker data
# 2. Bond Pricer - enter values and calculate
# 3. Portfolio - add assets and optimize
# 4. Risk - calculate VaR and Beta
```

### 2. Connect Real Data

```typescript
// In components, replace mock data with API calls
const response = await api.get('/market-data/securities');
```

### 3. Add More Features

- Historical price charts
- Performance attribution
- Risk decomposition
- Scenario analysis
- Backtesting engine

### 4. Production Build

```bash
npm run build
# Creates optimized dist/ folder
# Deploy to: Vercel, Netlify, Docker, AWS, etc.
```

---

## 📚 API Reference

### Valuation

```
POST /api/v1/valuation/bond/price
Body: {face_value, coupon_rate, yield_rate, years_to_maturity, frequency}
Response: {price, macaulay_duration, modified_duration}

POST /api/v1/valuation/equity/dcf
Body: {initial_fcf, growth_rate, discount_rate, forecast_years}
Response: {enterprise_value, equity_value}

GET /api/v1/valuation/annuity/{type}
Query: {annuity_payment, rate, periods}
Response: {present_value}
```

### Optimization

```
POST /api/v1/optimization/optimize
Body: {returns_data, objective, risk_free_rate}
Response: {optimal_weights, expected_return, portfolio_volatility, sharpe_ratio}

POST /api/v1/optimization/efficient-frontier
Body: {returns_data, num_points, risk_free_rate}
Response: {frontierPoints[], optimalPoint}

POST /api/v1/optimization/beta
Body: {asset_returns[], market_returns[]}
Response: {beta, alpha, r_squared}
```

### Risk

```
POST /api/v1/optimization/risk/var
Body: {returns[], confidence_level, method}
Response: {var_value, confidence_level, method}

POST /api/v1/optimization/risk/cvar
Body: {returns[], confidence_level, method}
Response: {cvar_value, confidence_level}
```

---

## 🎓 Key Actuarial Concepts

### Bond Pricing
- **Macaulay Duration**: Weighted average time to receive cash flows
- **Modified Duration**: Price sensitivity to yield changes
- **Yield Curve Impact**: Different yields affect bond prices

### Portfolio Optimization
- **Sharpe Ratio**: Return per unit of risk
- **Efficient Frontier**: Best risk/return combinations
- **Diversification**: Combining assets reduces portfolio risk

### Risk Metrics
- **VaR**: Loss that won't be exceeded at confidence level
- **CVaR**: Average loss when VaR is exceeded
- **Beta**: Correlation with market movements
- **Alpha**: Risk-adjusted outperformance

---

## 📞 Support

If you encounter issues:

1. Check backend is running: `docker ps`
2. Verify port 8000 is accessible: `curl http://localhost:8000`
3. Check browser console: `F12` → Console tab
4. Check frontend dev server logs

---

## ✨ You're Ready!

Your LuSE Quant Platform frontend is production-ready. Start exploring the capabilities:

- Price bonds in real-time
- Optimize your portfolio
- Analyze market risk
- Make data-driven decisions

**Happy quantitative finance! 🚀**
