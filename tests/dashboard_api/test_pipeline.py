from fastapi.testclient import TestClient
from dashboard_api.main import app

client = TestClient(app)

def test_pipeline_safe_scenario():
    response = client.post("/api/pipeline/run", json={"scenario_id": "L7_ATTESTATION"})
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "L7_ATTESTATION"
    assert "total_latency_ns" in data
    assert "overall_decision" in data
    
    l1 = data["L1"]
    assert "decision" in l1
    assert "latency" in l1
    assert "L2" in data
    assert "L3" in data
    assert "L6" in data
    
def test_pipeline_forbidden_scenario():
    response = client.post("/api/pipeline/run", json={"scenario_id": "L2_BACKSLASH"})
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "L2_BACKSLASH"
    
def test_pipeline_invalid_scenario():
    response = client.post("/api/pipeline/run", json={"scenario_id": "INVALID_HACK"})
    assert response.status_code == 400
    assert "Unknown scenario ID" in response.json()["detail"]
