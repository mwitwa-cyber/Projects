# LuSE Quantitative Platform - Implementation Roadmap

## 📊 Project Overview

A comprehensive quantitative investment analysis platform for the Lusaka Securities Exchange (LuSE), implementing advanced actuarial modeling (IFoA CM1, CM2, SP5) with frontier market adjustments.

## 🎯 Current Status

**Completion: ~60%**

### ✅ Completed Components

#### Backend Infrastructure
- [x] Docker containerization with 6 microservices
- [x] PostgreSQL with TimescaleDB for time-series data
- [x] Redis for caching and task queuing
- [x] FastAPI application structure
- [x] Bitemporal data modeling framework
- [x] Database schema with Alembic migrations

#### Actuarial Modules
- [x] **CM1 (Deterministic Valuation)**
  - Time Value of Money engine
  - Bond pricing with YTM solver
  - DCF valuation with Zambian CRP
  - Duration and convexity calculations
  
- [x] **CM2 (Portfolio Optimization)**
  - Ledoit-Wolf covariance shrinkage
  - Scholes-Williams Beta for thin trading
  - Max Sharpe Ratio optimization
  - Minimum Volatility portfolio
  - Efficient Frontier generation
  - VaR and CVaR risk metrics

#### Frontend
- [x] React 19 + TypeScript + Vite setup
- [x] Tailwind CSS v4 styling
- [x] Portfolio Dashboard with Recharts
- [x] Efficient Frontier visualization
- [x] Performance tracking charts

### ⏳ In Progress

- [ ] **CM2 Extensions**
  - Risk parity optimization
  - Black-Litterman model
  - Factor models (Fama-French)

- [ ] **SP5 (Fixed Income & Advanced Risk)**
  - Yield curve bootstrapping with QuantLib
  - Redington immunization solver
  - Stress testing framework
  - Monte Carlo simulation engine

- [ ] **Data Pipeline**
  - LuSE data scraper (afx.kwayisi.org)
  - BoZ yield curve ingestion
  - ZamStats CPI data
  - Automated daily updates

### 📋 Upcoming Features

- [ ] User authentication (JWT)
- [ ] Portfolio management CRUD
- [ ] Real-time WebSocket updates
- [ ] PDF report generation
- [ ] Excel export functionality
- [ ] Mobile responsive design
- [ ] API rate limiting
- [ ] Monitoring and logging

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or 3.12 (NOT 3.14)
- Node.js 18+
- Docker and Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/mwitwa-cyber/Projects.git
cd Projects

# Run automated setup
chmod +x setup.sh
./setup.sh

# Or start manually
docker-compose up -d
```

### Access Points

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Adminer: http://localhost:8080
- Jupyter: http://localhost:8888

## 📁 Repository Structure

```
Projects/
├── backend/
│   ├── app/
│   │   ├── core/              # Configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/
│   │   │   └── actuarial/     # CM1, CM2, SP5 modules
│   │   ├── api/v1/
│   │   │   └── endpoints/     # FastAPI routes
│   │   └── utils/
│   ├── alembic/               # Database migrations
│   ├── scripts/               # Data ingestion
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── charts/
│   │   │   └── portfolio/
│   │   ├── pages/
│   │   ├── services/          # API clients
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── Dockerfile
├── restored_docs/
├── docker-compose.yml
├── setup.sh                   # Automated setup
└── README.md
```

## 🔧 Key Dependencies

### Backend

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM with bitemporal support
- **QuantLib-Python** - Bond pricing, yield curves
- **PyPortfolioOpt** - Portfolio optimization
- **cvxpy** - Convex optimization solver
- **pandas, numpy, scipy** - Data processing
- **TimescaleDB** - Time-series database

### Frontend

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS v4** - Styling
- **Recharts** - Data visualization
- **Framer Motion** - Animations

## 📚 Key Features

### 1. Bitemporal Data Modeling

Tracks both *Valid Time* (when data is true) and *Transaction Time* (when data was recorded):

```sql
price_history (
    trade_date,
    valid_from, valid_to,
    transaction_from, transaction_to,
    is_current
)
```

Enables:
- Audit trails for compliance
- Backtesting with historical knowledge
- Price corrections without data loss

### 2. Frontier Market Adjustments

#### Scholes-Williams Beta
Adjusts for thin trading correlation lag:

```python
β_SW = (β₋₁ + β₀ + β₊₁) / (1 + 2ρ_m)
```

#### Ledoit-Wolf Shrinkage
Repairs noisy covariance matrices:

```python
Σ = δF + (1-δ)S
```

### 3. Zambian Market Specifics

- **Country Risk Premium**: 5% added to CAPM
- **High Risk-Free Rate**: ~20% (GRZ T-bills)
- **Currency Adjustment**: USD/ZMW and ZAR/ZMW
- **Liquidity Constraints**: Position size limits
- **Settlement**: T+3 cycle modeling

## 🧪 Testing

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose run backend pytest tests/integration/
```

## 📊 API Endpoints

### Valuation Endpoints

```http
POST /api/v1/valuation/bond/price
POST /api/v1/valuation/equity/dcf
GET  /api/v1/valuation/annuity/{type}
```

### Optimization Endpoints

```http
POST /api/v1/optimization/optimize
POST /api/v1/optimization/efficient-frontier
GET  /api/v1/optimization/beta/{ticker}
```

### Portfolio Endpoints

```http
GET    /api/v1/portfolios/
POST   /api/v1/portfolios/
GET    /api/v1/portfolios/{id}
PUT    /api/v1/portfolios/{id}
DELETE /api/v1/portfolios/{id}
```

## 🔐 Security Considerations

- JWT authentication (planned)
- SQL injection prevention (SQLAlchemy)
- CORS configuration
- Environment variable secrets
- Rate limiting (planned)

## 📈 Performance Optimization

- TimescaleDB hypertables for efficient time-series queries
- Redis caching for hot data
- Async endpoints for long-running calculations
- Celery for background tasks
- Connection pooling

## 🐛 Known Issues

### Python 3.14 Compatibility

QuantLib-Python and cvxpy have build issues on Python 3.14. 

**Solutions:**
1. Use Python 3.11 or 3.12
2. Install via conda: `conda install -c conda-forge quantlib-python cvxpy`
3. Use Docker exclusively

### Windows Build Errors

C++ dependencies may fail on Windows.

**Solutions:**
1. Use WSL2
2. Install Visual Studio Build Tools
3. Use conda-forge pre-built binaries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 Documentation

- [Implementation Guide](IMPLEMENTATION_GUIDE.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](restored_docs/walkthrough_architecture.md)
- [Technical Specification](LuSE%20Quantitative%20Platform%20Design.docx)

## 🎓 Actuarial Formulas Reference

### CM1 Formulas

```
v^n = (1+i)^(-n)              # Discount factor
δ = ln(1+i)                   # Force of interest
a_n| = (1-v^n)/i              # Annuity immediate
Bond Price = Σ(C*v^t) + F*v^n # Bond valuation
```

### CM2 Formulas

```
σ_p² = w'Σw                   # Portfolio variance
β = Cov(R_i,R_m)/Var(R_m)     # Beta coefficient
Sharpe = (R_p - R_f)/σ_p      # Sharpe ratio
```

## 📞 Support

- GitHub Issues: [Projects/issues](https://github.com/mwitwa-cyber/Projects/issues)
- Email: [your-email]
- Documentation: See `/restored_docs`

## 📄 License

[Add license information]

## 🙏 Acknowledgments

- Institute and Faculty of Actuaries (IFoA) - CM1, CM2, SP5 syllabus
- Lusaka Securities Exchange (LuSE)
- Bank of Zambia (BoZ)
- Open source community

---

**Last Updated**: December 27, 2024
**Version**: 0.1.0
**Status**: Active Development
