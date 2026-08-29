import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.models import ScenarioDefinition
from benchmarks.experiments.runner import ExperimentHarness
from common.schemas.security import DecisionEnum

def test_telemetry_trace_injection():
    trace_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "telemetry", "execve_trace.jsonl")
    assert os.path.exists(trace_path), f"Fixture not found at {trace_path}"
    
    scenario = ScenarioDefinition(
        scenario_id="EXP-REPLAY",
        scenario_name="Safe Telemetry Replay",
        description="Verify that L3 collector injection and telemetry replay works.",
        category="SMOKE_TEST",
        telemetry_trace=trace_path,
        expected_security_outcome=DecisionEnum.ALLOW
    )
    
    harness = ExperimentHarness()
    result = harness.run_scenario(scenario)
    
    # Assertions
    assert len(result.errors) == 0, f"Errors occurred: {result.errors}"
    assert result.l3_events_processed == 2
    # Since there are no prior L2 events in this trace execution to correlate against,
    # ExecutionCorrelationManager will flag them as anomalous (blocks).
    assert result.l3_anomalies_detected == 2
    assert result.layer_outcomes.L3.decision == "BLOCK"
    
    # Verify L4/L5 are marked unavailable for native replay currently
    assert result.layer_outcomes.L4.decision == "UNAVAILABLE"
    assert result.layer_outcomes.L5.decision == "UNAVAILABLE"
