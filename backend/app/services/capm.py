import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from datetime import date, timedelta
from scipy import stats
from app.core.models import Security, MarketPrice
from app.services.market_data import MarketDataService

class CapmService:
    def __init__(self, db: Session):
        self.db = db
        self.market_data = MarketDataService(db)

    def get_historical_prices(self, ticker: str, days: int = 365) -> pd.DataFrame:
        """Fetch historical prices as a DataFrame."""
        start_date = date.today() - timedelta(days=days)
        prices = self.db.query(MarketPrice).filter(
            MarketPrice.security_ticker == ticker,
            MarketPrice.valid_from >= start_date,
            MarketPrice.transaction_to == None
        ).all()
        
        if not prices:
            return pd.DataFrame()
            
        data = [{"date": p.valid_from, "price": p.price, "volume": p.volume} for p in prices]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        return df

    def calculate_market_return(self, days: int = 365) -> pd.Series:
        """
        Calculate daily returns for an equal-weighted market index.
        """
        securities = self.db.query(Security).filter(Security.type == "Equity").all()
        market_returns = pd.DataFrame()
        
        for sec in securities:
            df = self.get_historical_prices(sec.ticker, days)
            if not df.empty:
                # Calculate daily returns
                returns = df["price"].pct_change().dropna()
                market_returns[sec.ticker] = returns
        
        if market_returns.empty:
            return pd.Series()
            
        # Equal-weighted index return = mean of individual stock returns for each day
        index_returns = market_returns.mean(axis=1)
        return index_returns

    def calculate_capm(self, ticker: str, risk_free_rate: float = 0.15):
        """
        Calculate CAPM metrics: Beta, Expected Return, Liquidity Premium.
        """
        # 1. Get Stock Data
        stock_df = self.get_historical_prices(ticker)
        if stock_df.empty or len(stock_df) < 30:
             return {"error": "Insufficient history for stock"}
             
        stock_returns = stock_df["price"].pct_change().dropna()
        
        # 2. Get Market Data (Benchmark)
        market_returns = self.calculate_market_return()
        if market_returns.empty:
            return {"error": "Insufficient market data"}
            
        # Align dates
        aligned_data = pd.concat([stock_returns, market_returns], axis=1, join="inner").dropna()
        aligned_data.columns = ["stock", "market"]
        
        if len(aligned_data) < 30:
            return {"error": "Insufficient overlapping data points"}
            
        # 3. Calculate Beta (Slope of regression)
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            aligned_data["market"], aligned_data["stock"]
        )
        beta = slope
        
        # 4. Calculate Market Return (Annualized)
        avg_daily_mkt_return = aligned_data["market"].mean()
        annualized_mkt_return = avg_daily_mkt_return * 252 
        
        # 5. Liquidity Score / Premium
        # Simple proxy: Average Daily Dollar Volume
        stock_df["dollar_vol"] = stock_df["price"] * stock_df["volume"]
        avg_dollar_vol = stock_df["dollar_vol"].mean()
        
        # Scaled Liquidity Premium: Lower volume -> Higher Premium (Max 5%)
        # Thresholds (arbitrary for prototype): > 100k ZMW is liquid (0%), < 1k is illiquid (5%)
        # Linear interpolation in log space
        liquidity_premium = 0.0
        if avg_dollar_vol < 1000:
            liquidity_premium = 0.05
        elif avg_dollar_vol > 100000:
            liquidity_premium = 0.0
        else:
            # 1k to 100k
            log_vol = np.log10(avg_dollar_vol)
            # Map 3 (1k) -> 5 (100k) to 0.05 -> 0.0
            # Slope = -0.05 / 2 = -0.025
            liquidity_premium = 0.05 + (-0.025 * (log_vol - 3))

        # 6. Expected Return
        # CAPM: Rf + Beta * (Rm - Rf) + LiquidityPremium
        expected_return = risk_free_rate + beta * (annualized_mkt_return - risk_free_rate) + liquidity_premium
        
        return {
            "ticker": ticker,
            "beta": round(beta, 4),
            "expected_return": round(expected_return, 4),
            "annualized_market_return": round(annualized_mkt_return, 4),
            "risk_free_rate": risk_free_rate,
            "liquidity_premium": round(liquidity_premium, 4),
            "average_dollar_volume": round(avg_dollar_vol, 2),
            "r_squared": round(r_value**2, 4),
            "alpha": round(intercept * 252, 4) # Annualized Jensen's Alpha
        }
