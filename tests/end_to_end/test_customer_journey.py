from app.main import app
from fastapi.testclient import TestClient


def test_executive_to_actionable_customer_journey():
    with TestClient(app) as client:
        dashboard = client.get("/api/v1/dashboard").json()
        predictions = client.get("/api/v1/churn/predictions").json()
        recommendations = client.get("/api/v1/customers/analytics/recommendations").json()
        assert dashboard["kpis"]["revenue"] > 0
        assert len(predictions) == dashboard["kpis"]["customers"]
        assert recommendations
