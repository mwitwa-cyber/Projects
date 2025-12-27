# locustfile.py for backend performance testing
from locust import HttpUser, task, between

class BackendUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def get_market_data(self):
        self.client.get("/api/v1/market-data/luse/latest")

    @task(2)
    def optimize_portfolio(self):
        payload = {"portfolio_id": 1, "objective": "max_sharpe"}
        self.client.post("/api/v1/optimization/optimize", json=payload)

    @task(1)
    def bond_valuation(self):
        payload = {"coupon_rate": 0.12, "maturity": "2030-12-31", "ytm": 0.15, "face_value": 1000}
        self.client.post("/api/v1/valuation/bond/price", json=payload)

    @task(1)
    def create_portfolio(self):
        payload = {"name": "PerfTest", "description": "", "portfolio_type": "personal", "holdings": []}
        self.client.post("/api/v1/portfolios/", json=payload)
