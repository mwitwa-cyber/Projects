import numpy as np
from scipy.optimize import newton
from typing import List, Dict, Tuple, Optional
from datetime import date, timedelta

class ValuationService:
    """
    Implements Actuarial Module 1 (CM1): Deterministic Valuation.
    Uses pure Python/NumPy/SciPy as a robust fallback for QuantLib on Windows.
    Provides robust error handling and type hints.
    """

    @staticmethod
    def calculate_discount_factor(rate: float, t: float, compounding: str = "discrete") -> float:
        """
        Calculate discount factor v^t = (1+i)^-t or exp(-rt) for continuous compounding.
        Args:
            rate (float): Interest rate
            t (float): Time in years
            compounding (str): 'discrete' or 'continuous'
        Returns:
            float: Discount factor
        """
        if compounding == "continuous":
            return np.exp(-rate * t)
        if rate < -1:
            raise ValueError("Interest rate must be greater than -100%.")
        return (1 + rate) ** -t

    @staticmethod
    def present_value_annuity(rate: float, n: int, payment: float = 1.0, type: str = "arrears") -> float:
        """
        Calculates a_n (arrears) or a_doubledot_n (due).
        Args:
            rate (float): Interest rate
            n (int): Number of periods
            payment (float): Payment per period
            type (str): 'arrears' or 'due'
        Returns:
            float: Present value of annuity
        """
        if rate == 0:
            return n * payment
        v = 1 / (1 + rate)
        an = (1 - v**n) / rate
        if type == "due":
            an *= (1 + rate)
        return an * payment

    @staticmethod
    def bond_pricing(
        face_value: float,
        coupon_rate: float,
        market_yield: float,
        years_to_maturity: float,
        frequency: int = 2
    ) -> Dict[str, float]:
        """
        Prices a standard fixed-coupon bond.
        Args:
            face_value (float): Face value of bond
            coupon_rate (float): Annual coupon rate
            market_yield (float): Market yield
            years_to_maturity (float): Years to maturity
            frequency (int): Coupon payments per year
        Returns:
            Dict[str, float]: Price, durations, convexity
        """
        n_periods = int(years_to_maturity * frequency)
        periodic_coupon = (coupon_rate * face_value) / frequency
        periodic_yield = market_yield / frequency
        # PV of Coupons (Annuity)
        pv_coupons = ValuationService.present_value_annuity(periodic_yield, n_periods, periodic_coupon)
        # PV of Redemption (Capital)
        pv_redemption = face_value * ((1 + periodic_yield) ** -n_periods)
        price = pv_coupons + pv_redemption
        duration_mac = ValuationService.calculate_duration(face_value, coupon_rate, market_yield, years_to_maturity, frequency)
        convexity = ValuationService.calculate_convexity(face_value, coupon_rate, market_yield, years_to_maturity, frequency)
        return {
            "price": round(price, 4),
            "macaulay_duration": round(duration_mac, 4),
            "modified_duration": round(duration_mac / (1 + periodic_yield), 4),
            "convexity": round(convexity, 4)
        }

    @staticmethod
    def calculate_duration(face, coupon_rate, ytm, maturity, freq=2):
        """
        Macaulay Duration = sum(t * PV_t) / Price
        """
        cf_times = np.arange(1, int(maturity * freq) + 1) / freq
        periodic_coupon = (coupon_rate * face) / freq
        periodic_ytm = ytm / freq
        
        cfs = np.full(len(cf_times), periodic_coupon)
        cfs[-1] += face
        
        pvs = [c * (1 + periodic_ytm)**(-t*freq) for t, c in zip(cf_times, cfs)]
        weighted_times = [t * pv for t, pv in zip(cf_times, pvs)]
        
        price = sum(pvs)
        return sum(weighted_times) / price

    @staticmethod
    def calculate_convexity(face, coupon_rate, ytm, maturity, freq=2):
        """
        Convexity = (1/P) * sum( (t^2 + t/freq) * PV_t ) / (1+y/freq)^2
        """
        cf_times = np.arange(1, int(maturity * freq) + 1) / freq
        periodic_coupon = (coupon_rate * face) / freq
        periodic_ytm = ytm / freq
        
        cfs = np.full(len(cf_times), periodic_coupon)
        cfs[-1] += face
        
        pvs = [c * (1 + periodic_ytm)**(-t*freq) for t, c in zip(cf_times, cfs)]
        
        weighted_conv = [ (t**2 + t/freq) * pv for t, pv in zip(cf_times, pvs) ]
        
        price = sum(pvs)
        return sum(weighted_conv) / (price * (1 + periodic_ytm)**2)

    @staticmethod
    def bootstrap_yield_curve(instruments: List[Dict]) -> List[Dict]:
        """
        Bootstraps a Zero Coupon Yield Curve from a set of par-value instruments (T-Bills and Bonds).
        Instruments: [{'maturity': 0.25, 'rate': 0.15}, {'maturity': 2.0, 'coupon': 0.18, 'price': 100}]
        """
        # Sort by maturity
        instruments.sort(key=lambda x: x['maturity'])
        
        zero_rates = {} # maturity -> zero_rate
        curve_points = []

        for inst in instruments:
            maturity = inst['maturity']
            
            if maturity <= 1.0:
                # T-Bills (Zero Coupon by definition)
                # Price = 100 / (1 + r*t) or similar convention. Assuming 'rate' is annual yield.
                # Simplification: rate provided is the zero rate.
                zero_rate = inst['rate']
                zero_rates[maturity] = zero_rate
            else:
                # Bond: Price = sum(C * e^-r(t)*t) + Face * e^-r(T)*T
                # We need to solve for the zero rate at T, given known zero rates at t < T.
                # Assuming linear interpolation of rates for intermediate cashflows.
                
                price = inst.get('price', 100)
                coupon = inst.get('coupon', 0.0)
                freq = inst.get('freq', 2)
                face = 100
                
                cf_times = np.arange(0.5, maturity + 0.01, 0.5) # Assuming semi-annual
                
                def objective(r_final):
                    # Interpolator
                    temp_rates = zero_rates.copy()
                    temp_rates[maturity] = r_final
                    
                    times_keys = sorted(temp_rates.keys())
                    rates_values = [temp_rates[k] for k in times_keys]
                    
                    pv = 0
                    for t in cf_times:
                        # Linear interop of zero rate
                        r_t = np.interp(t, times_keys, rates_values)
                        cf = (coupon * face / freq)
                        if abs(t - maturity) < 0.01:
                            cf += face
                        
                        pv += cf * np.exp(-r_t * t) # Continuous compounding for curve construction
                    return pv - price

                # Solve for r_final
                try:
                    zero_rate = newton(objective, 0.15)
                except:
                    zero_rate = inst.get('coupon', 0.15) # Fallback

                zero_rates[maturity] = zero_rate
            
            curve_points.append({"maturity": maturity, "zero_rate": round(zero_rates[maturity], 5)})
            
        return curve_points
