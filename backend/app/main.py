from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LuSE Quantitative Investment Analysis Platform",
    description="Actuarial and Investment Analysis API for the Zambian Market",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import market_data, valuation
from app.core import models
from app.core.db import engine

# Create tables
models.Base.metadata.create_all(bind=engine)

app.include_router(market_data.router, prefix="/api/v1/market-data", tags=["Market Data"])
app.include_router(valuation.router, prefix="/api/v1/valuation", tags=["Valuation"])

@app.get("/")
async def root():
    return {"message": "LuSE Quant Platform API Operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
