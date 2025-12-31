import numpy as np
from scipy.optimize import minimize
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.core.models import Security
from app.services.market_data import MarketDataService

class YieldCurveService:
    def __init__(self, db: Session):
        self.db = db
        self.market_data = MarketDataService(db)

    def calculate_ytm(self, price, coupon, ttm, face_value=100.0):
        """
        Approximate YTM using the formula:
        YTM ~= (C + (F - P) / t) / ((F + P) / 2)
        """
        if ttm <= 0: return 0.0
        annual_coupon = face_value * coupon
        numerator = annual_coupon + ((face_value - price) / ttm)
        denominator = (face_value + price) / 2
        return numerator / denominator

    def nelson_siegel(self, tau, beta0, beta1, beta2, lam):
        """
        Nelson-Siegel Yield Curve Function.
        tau: Time to maturity (periods)
        """
        if tau == 0: return beta0 + beta1
        term1 = (1 - np.exp(-tau / lam)) / (tau / lam)
        term2 = term1 - np.exp(-tau / lam)
        return beta0 + (beta1 * term1) + (beta2 * term2)

    def fit_nelson_siegel(self, observation_date: date):
        """
        Fit Nelson-Siegel model to observed government bond yields.
        """
        # 1. Fetch Government Bonds
        bonds = self.db.query(Security).filter(
            Security.type == "Bond",
            Security.sector == "Government Bonds"
        ).all()
        
        if not bonds:
            return {"error": "No bond data available"}

        observed_ttm = []
        observed_yields = []
        
        for bond in bonds:
            # Get latest price
            price_record = self.market_data.get_price_as_of(bond.ticker, observation_date)
            if not price_record:
                continue
                
            price = price_record.price
            if price <= 0: continue
            
            # Calculate Time To Maturity (in Years)
            if not bond.maturity_date: continue
            
            maturity = bond.maturity_date.date() if isinstance(bond.maturity_date, datetime) else bond.maturity_date
            delta = (maturity - observation_date).days / 365.0
            
            if delta <= 0: continue
            
            # Calculate YTM
            ytm = self.calculate_ytm(price, bond.coupon_rate or 0, delta, bond.face_value or 100)
            
            observed_ttm.append(delta)
            observed_yields.append(ytm)

        if len(observed_yields) < 3:
            return {"error": "Insufficient bond data points to fit curve (need > 3)"}

        # 2. Optimization
        # Objective: Minimize sum of squared errors
        def objective(params):
            b0, b1, b2, lam = params
            if lam <= 0: return 1e6 # Constraint lambda > 0
            
            errors = []
            for t, y_obs in zip(observed_ttm, observed_yields):
                y_model = self.nelson_siegel(t, b0, b1, b2, lam)
                errors.append((y_obs - y_model) ** 2)
            return sum(errors)

        # Initial Guess: b0=long_run, b1=short-long, b2=hump, lam=1
        initial_guess = [0.15, -0.05, 0.02, 1.0] 
        
        result = minimize(objective, initial_guess, method='Nelder-Mead')
        
        beta0, beta1, beta2, lam = result.x
        
        # 3. Generate Curve Points for Visualization
        plot_points = []
        for t in np.linspace(0.1, 30, 60): # 0 to 30 years
            y = self.nelson_siegel(t, beta0, beta1, beta2, lam)
            plot_points.append({"ttm": round(t, 2), "yield": round(y * 100, 4)}) # Return as %
            
        return {
            "parameters": {
                "beta0": round(beta0, 5),
                "beta1": round(beta1, 5),
                "beta2": round(beta2, 5),
                "lambda": round(lam, 5)
            },
            "curve": plot_points,
            "observed": [
                {"ttm": round(t, 2), "yield": round(y * 100, 4)} 
                for t, y in zip(observed_ttm, observed_yields)
            ]
        }
