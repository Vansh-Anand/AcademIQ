import pytest
from fastapi.testclient import TestClient
from dashboard_api.main import app

client = TestClient(app)

def test_get_all_experiments():
    response = client.get("/api/experiments")
    assert response.status_code == 200
    data = response.json()
    assert "experiments" in data
    assert isinstance(data["experiments"], list)
    
    if len(data["experiments"]) > 0:
        first_exp = data["experiments"][0]
        assert "experiment_id" in first_exp
        assert "title" in first_exp
        assert "execution_mode" in first_exp
        assert "category" in first_exp

def test_get_experiment_detail_exp1():
    response = client.get("/api/experiments/EXP-1")
    if response.status_code == 200:
        data = response.json()
        assert data["experiment_id"] == "EXP-1"
        assert "Direct Prompt Injection Prevention" in data["title"]
        assert data["attack_success_rate"] is not None
        assert data["raw_artifact"] is not None

def test_get_experiment_detail_not_found():
    response = client.get("/api/experiments/NONEXISTENT_EXP")
    assert response.status_code == 404
