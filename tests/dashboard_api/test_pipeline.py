from fastapi.testclient import TestClient
from dashboard_api.main import app

client = TestClient(app)

def test_pipeline_safe_scenario():
    response = client.post("/api/pipeline/run", json={"scenario_id": "SAFE_READ"})
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "SAFE_READ"
    assert "total_latency_ns" in data
    assert "overall_decision" in data
    
    l1 = data["L1"]
    assert "decision" in l1
    assert "latency" in l1
    assert "L2" in data
    assert "L3" in data
    assert "L6" in data
    
def test_pipeline_forbidden_scenario():
    response = client.post("/api/pipeline/run", json={"scenario_id": "OBFUSCATED_COMMAND"})
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "OBFUSCATED_COMMAND"
    
def test_pipeline_invalid_scenario():
    response = client.post("/api/pipeline/run", json={"scenario_id": "INVALID_HACK"})
    assert response.status_code == 400
    assert "Unknown scenario ID" in response.json()["detail"]
