"""
Integration tests for FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_probe():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Retail Sales Forecasting" in data["system"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_get_stores():
    response = client.get("/api/stores")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "store_id" in data[0]

def test_get_sales():
    response = client.get("/api/sales?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    if len(data) > 0:
        assert "sales" in data[0]

def test_get_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "mape" in data[0]

def test_get_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_stores" in data
    assert "best_model" in data
    assert "current_mape" in data
    assert "target_status" in data
    assert isinstance(data["target_achieved"], bool)

def test_run_forecast_endpoint():
    payload = {
        "store_id": 1,
        "department_id": 1,
        "horizon": 7,
        "lead_time": 2,
        "service_level": 0.95
    }
    response = client.post("/api/forecast/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["forecasts"]) == 7
    assert "inventory_plan" in data

def test_get_inventory_recommendations():
    response = client.get("/api/inventory/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "status" in data[0]
        assert data[0]["status"] in ["LOW STOCK", "NORMAL", "OVERSTOCK"]
