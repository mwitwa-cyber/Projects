import pytest
from app.services.actuarial.cm1_valuation import CM1Valuation

@pytest.mark.actuarial
class TestCM1Valuation:
    def test_bond_price(self):
        cm1 = CM1Valuation()
        price = cm1.price(face_value=1000, coupon_rate=0.08, yield_rate=0.07, years=5)
        assert price > 1000  # Price should be above par if coupon > yield

    def test_bond_duration(self):
        cm1 = CM1Valuation()
        duration = cm1.duration(face_value=1000, coupon_rate=0.08, yield_rate=0.07, years=5)
        assert duration > 0

    def test_discounted_cash_flows(self):
        cm1 = CM1Valuation()
        dcf = cm1.discounted_cash_flows(face_value=1000, coupon_rate=0.08, yield_rate=0.07, years=5)
        assert isinstance(dcf, list)
        assert len(dcf) == 11  # 10 semi-annual coupons + principal
