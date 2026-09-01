from fastapi.testclient import TestClient
from dashboard_api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "components" in data
    assert "orchestrator" in data["components"]
    assert "experiment_results" in data["components"]
    assert "eces_sqlite" in data["components"]
