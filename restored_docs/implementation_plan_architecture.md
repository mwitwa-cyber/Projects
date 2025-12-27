# Implementation Plan - LuSE Quantitative Investment Analysis Platform

# Goal Description
Develop a robust, microservices-based quantitative investment platform tailored for the Lusaka Securities Exchange (LuSE). The system will address local market idiosyncrasies (thin trading, data sparsity) using advanced actuarial models (Scholes-Williams Beta, Bitemporal Data Modeling) and provide a premium, reactive frontend for investment analysis.

## User Review Required
> [!IMPORTANT]
> **Data Sources**: We will use mock data seeded with realistic LuSE values (e.g., ZANACO, CECZ) for development as live feeds require contracts.
> **Docker Requirement**: The persistence layer (TimescaleDB, Redis) relies on Docker. Ensure Docker Desktop is running.

## Proposed Changes

### Infrastructure Layer
#### [NEW] [docker-compose.yml](file:///C:/Users/Mwitw/.gemini/antigravity/scratch/luse-quant-platform/docker-compose.yml)
- PostgreSQL/TimescaleDB for bitemporal market data.
- Redis for caching and Celery message broker.
- Adminer or similar for DB inspection.

### Backend (Python/FastAPI)
Structure: `backend/`
- **Market Data Service**: Handles `ticker`, `price`, `volume` with `valid_time` and `transaction_time`.
- **Actuarial Service**: Wraps QuantLib for Bond Pricing and Yield Curves.
- **Optimization Service**: Uses PyPortfolioOpt/CVXPY for Mean-Variance and Immunization.
- **Worker**: Celery worker for heavy matrix operations.

### Frontend (React/TypeScript)
Structure: `frontend/`
- **Tech Stack**: Vite, React, TypeScript, TailwindCSS (v4 if available/stable, else v3 + custom CSS for "Premium" feel).
- **Key Components**:
    - `EfficientFrontierChart`: D3.js implementation for the scatter plot.
    - `YieldCurveBuilder`: Interactive line chart for bootstrapping adjustments.
    - `BitemporalScreener`: Time-travel debugging UI for price history.

## Verification Plan

### Automated Tests
- **Unit Tests**: Pytest for mathematical correctness (e.g., checking if $a_{\overline{n|}}$ matches standard actuarial tables).
- **Integration Tests**: Verify Celery task execution and Redis round-trip.

### Manual Verification
- **Yield Curve sanity check**: Ensure 10y GRZ bond yields are higher than 91d T-bills (normal curve) or reflect current inversion.
- **Liquidity Adjustment**: Verify Scholes-Williams Beta > OLS Beta for illiquid stocks like REIZ.
