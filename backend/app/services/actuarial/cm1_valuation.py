# backend/app/services/actuarial/cm1_valuation.py
"""
CM1 Module: Deterministic Valuation

Robust implementation of time value of money, bond pricing, DCF, and annuity calculations
as per IFoA CM1 curriculum, adapted for Zambian market. Includes type hints, docstrings,
and error handling for production use.
"""

import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
from scipy.optimize import newton


@dataclass
class CashFlow:
    """
    Represents a single cash flow.
    Attributes:
        time (float): Time in years
        amount (float): Cash flow amount
    """
    time: float
    amount: float


class TimeValueOfMoney:
    """
    Core TVM engine with actuarial notation and robust error handling.
    """
    @staticmethod
    def discount_factor(i: float, n: float) -> float:
        """
        Calculate discount factor v^n = (1+i)^(-n)
        Args:
            i (float): Interest rate
            n (float): Number of periods
        Returns:
            float: Discount factor
        """
        if i < -1:
            raise ValueError("Interest rate must be greater than -100%.")
        return (1 + i) ** (-n)

    @staticmethod
    def accumulation_factor(i: float, n: float) -> float:
        """
        Calculate accumulation factor (1+i)^n
        """
        if i < -1:
            raise ValueError("Interest rate must be greater than -100%.")
        return (1 + i) ** n

    @staticmethod
    def force_of_interest(i: float) -> float:
        """
        Calculate force of interest δ = ln(1+i)
        """
        if i <= -1:
            raise ValueError("Interest rate must be greater than -100%.")
        return np.log(1 + i)

    @staticmethod
    def discount_rate(i: float) -> float:
        """
        Calculate discount rate d = i/(1+i)
        """
        if i <= -1:
            raise ValueError("Interest rate must be greater than -100%.")
        return i / (1 + i)

    @staticmethod
    def present_value(cash_flows: List[CashFlow], i: float) -> float:
        """
        Calculate present value of a series of cash flows
        """
        if not cash_flows:
            return 0.0
        return sum(cf.amount * TimeValueOfMoney.discount_factor(i, cf.time) for cf in cash_flows)


class AnnuityCalculator:
    """
    Annuity valuation formulas with error handling.
    """
    @staticmethod
    def annuity_immediate(i: float, n: int) -> float:
        """
        Calculate PV of annuity in arrears: a_n| = (1 - v^n) / i
        """
        if i == 0:
            return float(n)
        v = TimeValueOfMoney.discount_factor(i, n)
        return (1 - v) / i
    
    @staticmethod
    def annuity_due(i: float, n: int) -> float:
        """Calculate PV of annuity due: ä_n| = (1 - v^n) / d"""
        v = TimeValueOfMoney.discount_factor(i, n)
        d = TimeValueOfMoney.discount_rate(i)
        return (1 - v) / d
    
    @staticmethod
    def perpetuity(i: float) -> float:
        """Calculate PV of perpetuity: a_∞| = 1/i"""
        return 1 / i
    
    @staticmethod
    def growing_perpetuity(payment: float, i: float, g: float) -> float:
        """Calculate PV of growing perpetuity: PV = payment / (i - g)"""
        if g >= i:
            raise ValueError("Growth rate must be less than discount rate")
        return payment / (i - g)


class BondPricer:
    """Bond pricing and yield calculations."""
    
    @staticmethod
    def bond_price(
        face_value: float,
        coupon_rate: float,
        yield_rate: float,
        years_to_maturity: float,
        frequency: int = 2
    ) -> float:
        """Calculate bond price: Price = Σ(C * v^t) + F * v^n"""
        n_periods = int(years_to_maturity * frequency)
        coupon_payment = (coupon_rate / frequency) * face_value
        period_yield = yield_rate / frequency
        
        # PV of coupon payments
        if period_yield != 0:
            pv_coupons = coupon_payment * AnnuityCalculator.annuity_immediate(
                period_yield, n_periods
            )
        else:
            pv_coupons = coupon_payment * n_periods
        
        # PV of face value
        pv_face = face_value * TimeValueOfMoney.discount_factor(
            period_yield, n_periods
        )
        
        return pv_coupons + pv_face
    
    @staticmethod
    def yield_to_maturity(
        price: float,
        face_value: float,
        coupon_rate: float,
        years_to_maturity: float,
        frequency: int = 2,
        initial_guess: float = 0.10
    ) -> float:
        """Calculate YTM using Newton-Raphson method"""
        def price_diff(ytm):
            calculated_price = BondPricer.bond_price(
                face_value, coupon_rate, ytm, years_to_maturity, frequency
            )
            return calculated_price - price
        
        try:
            ytm = newton(price_diff, initial_guess, maxiter=100)
            return ytm
        except RuntimeError:
            raise ValueError("Failed to converge on YTM solution")
    
    @staticmethod
    def macaulay_duration(
        face_value: float,
        coupon_rate: float,
        yield_rate: float,
        years_to_maturity: float,
        frequency: int = 2
    ) -> float:
        """Calculate Macaulay duration: D_mac = Σ(t * PV(CF_t)) / Price"""
        n_periods = int(years_to_maturity * frequency)
        coupon_payment = (coupon_rate / frequency) * face_value
        period_yield = yield_rate / frequency
        
        weighted_pv = 0
        for t in range(1, n_periods + 1):
            time_years = t / frequency
            pv = coupon_payment * TimeValueOfMoney.discount_factor(period_yield, t)
            weighted_pv += time_years * pv
        
        # Add face value payment
        pv_face = face_value * TimeValueOfMoney.discount_factor(period_yield, n_periods)
        weighted_pv += years_to_maturity * pv_face
        
        price = BondPricer.bond_price(
            face_value, coupon_rate, yield_rate, years_to_maturity, frequency
        )
        
        return weighted_pv / price
    
    @staticmethod
    def modified_duration(
        face_value: float,
        coupon_rate: float,
        yield_rate: float,
        years_to_maturity: float,
        frequency: int = 2
    ) -> float:
        """Calculate modified duration: D_mod = D_mac / (1 + y/k)"""
        d_mac = BondPricer.macaulay_duration(
            face_value, coupon_rate, yield_rate, years_to_maturity, frequency
        )
        return d_mac / (1 + yield_rate / frequency)


class DCFValuation:
    """Discounted Cash Flow valuation for equities."""
    
    @staticmethod
    def gordon_growth_model(
        dividend: float,
        growth_rate: float,
        required_return: float
    ) -> float:
        """Gordon Growth Model: P = D₁ / (r - g)"""
        if growth_rate >= required_return:
            raise ValueError("Growth rate must be less than required return")
        return dividend / (required_return - growth_rate)
    
    @staticmethod
    def wacc_zambian(
        risk_free_rate: float,
        beta: float,
        market_return: float,
        country_risk_premium: float = 0.05,
        equity_weight: float = 0.6,
        debt_weight: float = 0.4,
        cost_of_debt: float = 0.15,
        tax_rate: float = 0.30
    ) -> float:
        """Calculate WACC adjusted for Zambian market with CRP"""
        # Cost of equity with country risk premium
        cost_of_equity = (
            risk_free_rate + 
            beta * (market_return - risk_free_rate) + 
            country_risk_premium
        )
        
        # WACC
        wacc = (
            equity_weight * cost_of_equity + 
            debt_weight * cost_of_debt * (1 - tax_rate)
        )
        
        return wacc
    
    @staticmethod
    def dcf_multistage(
        initial_fcf: float,
        growth_rates: List[float],
        terminal_growth: float,
        wacc: float,
        gdp_growth: float = 0.04
    ) -> float:
        """Multi-stage DCF valuation"""
        if terminal_growth > gdp_growth:
            raise ValueError(
                f"Terminal growth ({terminal_growth:.1%}) exceeds "
                f"GDP growth ({gdp_growth:.1%}). Unrealistic assumption."
            )
        
        pv = 0
        fcf = initial_fcf
        
        # PV of explicit forecast period
        for year, growth in enumerate(growth_rates, 1):
            fcf *= (1 + growth)
            pv += fcf * TimeValueOfMoney.discount_factor(wacc, year)
        
        # Terminal value
        terminal_fcf = fcf * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        pv_terminal = terminal_value * TimeValueOfMoney.discount_factor(
            wacc, len(growth_rates)
        )
        
        return pv + pv_terminal
