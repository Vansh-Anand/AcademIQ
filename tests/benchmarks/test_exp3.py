import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.exp3_multistep_exfiltration import build_scenarios, baseline_evaluate

@pytest.fixture
def scenarios():
    return build_scenarios()

def test_exp3_scenarios_have_correct_structure(scenarios):
    assert len(scenarios) == 6
    for s in scenarios:
        assert "id" in s
        assert "nodes" in s
        assert "is_attack" in s
        assert len(s["nodes"]) > 0

def test_exp3_baseline_misses_exfiltration(scenarios):
    # Scenario D is the exfiltration attack
    scenario_d = next(s for s in scenarios if s["id"] == "D")
    
    # The baseline shouldn't detect it because no individual node is critical
    assert baseline_evaluate(scenario_d["nodes"]) == False

def test_exp3_safe_scenarios_do_not_block(scenarios):
    scenario_a = next(s for s in scenarios if s["id"] == "A")
    scenario_b = next(s for s in scenarios if s["id"] == "B")
    
    # Baseline shouldn't block
    assert baseline_evaluate(scenario_a["nodes"]) == False
    assert baseline_evaluate(scenario_b["nodes"]) == False
