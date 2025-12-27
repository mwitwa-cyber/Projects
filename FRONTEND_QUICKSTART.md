# LuSE Quant Platform - Frontend Quick Start

## 🚀 Run Everything in 3 Steps

### Step 1: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 2: Start Docker Containers
```bash
# From project root
docker-compose up -d backend db redis
echo "Waiting for backend to start..."
sleep 10
docker logs backend  # Check backend logs
```

### Step 3: Start Frontend Dev Server
```bash
npm run dev
```

**Frontend is live at: http://localhost:5173**

---

## 📊 Test Each Component

### 1. **Market Pulse** (Default Tab)
- Shows live ticker data from backend
- Should display CECZ, ZANACO, SCBL
- Live price updates and percentage changes

### 2. **Bond Pricer** (Click "Bond Pricing" Tab)

**Test Case**:
```
Face Value: 100
Coupon Rate: 15%
Yield Rate: 18%
Years to Maturity: 10
Frequency: Semi-annual

Expected: Bond Price ≈ K95-98
```

### 3. **Portfolio Optimizer** (Click "Portfolio" Tab)

**Test Case**:
```
Assets: CECZ, ZANACO, SCBL
Returns: Use default or enter your own
Objective: Maximize Sharpe Ratio
Risk-Free Rate: 20%

Expected: Shows optimal weights + Efficient Frontier chart
```

### 4. **Risk Analysis** (Click "Risk Analysis" Tab)

**VaR Test**:
```
Returns: 0.02, -0.03, 0.04, -0.01, 0.05, ...
Confidence: 95%
Method: Historical

Expected: VaR ≈ -2.5% (95% confidence max loss)
```

**Beta Test**:
```
Asset Returns: Market index returns
Market Returns: LASI or benchmark returns

Expected: Beta value (systematic risk measure)
```

---

## ✅ Success Indicators

You'll know everything works when:

- ✅ http://localhost:5173 loads without errors
- ✅ Backend status shows "Online" in header
- ✅ Market Pulse displays ticker cards with data
- ✅ Bond Pricer calculates and returns results
- ✅ Portfolio Optimizer shows weights + efficient frontier
- ✅ Risk Analyzer calculates VaR and Beta
- ✅ No red error messages in UI or console

---

## 🐛 Troubleshooting

### Backend shows "Offline"
```bash
# Restart containers
docker-compose restart backend
sleep 5
# Refresh browser
```

### Port 5173 already in use
```bash
# Vite will automatically use next available port (5174, 5175, etc.)
# Check terminal for actual port
```

### Build errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📱 Mobile Testing

Frontend is responsive and works on:
- Desktop (1920x1080+)
- Tablet (768x1024)
- Mobile (375x667)

Test on your phone by visiting:
```
http://<your-computer-ip>:5173
```

Find your IP:
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig
```

---

## 🎯 What's Implemented

### Components ✅
- Market Pulse Dashboard
- Bond Pricing Calculator
- Portfolio Optimizer
- Risk Analyzer (VaR, Beta)

### Features ✅
- API integration with backend
- Error handling
- Loading states
- Responsive design
- Dark theme UI
- Backend health check
- Tab-based navigation

### Charts ✅
- Line charts (trends)
- Pie charts (allocation)
- Bar charts (distribution)
- Scatter charts (efficient frontier)

---

## 📚 File Structure

```
frontend/
├── src/
│   ├── App.tsx                    ← Main component with tabs
│   ├── components/
│   │   ├── MarketPulse.tsx       ← Market data display
│   │   ├── BondPricer.tsx        ← Bond pricing
│   │   ├── PortfolioOptimizer.tsx ← Portfolio optimization
│   │   └── RiskAnalyzer.tsx      ← Risk metrics
│   ├── services/
│   │   └── api.ts                ← API wrapper
│   ├── lib/
│   │   └── utils.ts              ← Helper functions
│   ├── main.tsx                  ← React entry point
│   └── index.css                 ← Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── FRONTEND_INTEGRATION.md       ← Complete guide
└── FRONTEND_QUICKSTART.md        ← This file
```

---

## 🚀 Next Actions

1. **Run the project**
   ```bash
   npm run dev
   ```

2. **Test all components**
   - Try each tab
   - Enter test data
   - Verify calculations

3. **Connect real data** (optional)
   - Modify API calls to use live market data
   - Add price history charts
   - Integrate with data feeds

4. **Deploy** (when ready)
   ```bash
   npm run build
   # Deploy dist/ folder to hosting
   ```

---

## 💡 Tips

- Use Chrome DevTools (F12) to debug
- Check Network tab to see API calls
- View Console for error messages
- Use test data initially, then real data

---

## 🎉 You're All Set!

Frontend integration is complete. Start building! 🚀

**Questions?** Check [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) for detailed documentation.
