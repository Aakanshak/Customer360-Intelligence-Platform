from app.main import app
from fastapi.testclient import TestClient


def test_health_and_dashboard():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200
        assert response.json()["kpis"]["customers"] == 80


def test_customer_and_forecast_endpoints():
    with TestClient(app) as client:
        profile = client.get("/api/v1/customers/profile/1")
        assert profile.status_code == 200
        forecast = client.post("/api/v1/forecast/revenue", json={"horizon": 3})
        assert forecast.status_code == 200
        assert len(forecast.json()["forecast"]) == 3


def test_missing_customer_is_404():
    with TestClient(app) as client:
        assert client.get("/api/v1/customers/profile/999999").status_code == 404
