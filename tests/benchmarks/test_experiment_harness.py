import pytest
import time
import uuid
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.models import ScenarioDefinition
from benchmarks.experiments.runner import ExperimentHarness
from common.events.schemas import ToolInvocationEvent
from common.schemas.security import DecisionEnum

def test_scenario_definition_validates():
    # Test that the Pydantic model validates correctly
    scenario = ScenarioDefinition(
        scenario_id="TEST-001",
        scenario_name="Safe Smoke Test",
        description="A harmless scenario.",
        category="SMOKE_TEST",
        expected_security_outcome=DecisionEnum.ALLOW
    )
    assert scenario.scenario_id == "TEST-001"
    assert len(scenario.agent_events) == 0

def test_safe_smoke_scenario():
    # Create the single SAFE demonstration scenario
    event = ToolInvocationEvent(
        event_id=f"evt-{uuid.uuid4()}",
        timestamp_ns=time.time_ns(),
        layer="AGENT",
        trace_id=f"trc-{uuid.uuid4()}",
        simulation=True,
        tool_name="read_file", # Allowed by GCD compiler
        arguments={"path": "/safe/file.txt"} # Explicitly allowed in compiler.py
    )
    
    scenario = ScenarioDefinition(
        scenario_id="EXP-SMOKE",
        scenario_name="SAFE_READ_OPERATION",
        description="A benign ToolInvocationEvent representing an allowed read operation.",
        category="SMOKE_TEST",
        agent_events=[event],
        expected_security_outcome=DecisionEnum.ALLOW
    )
    
    harness = ExperimentHarness()
    result = harness.run_scenario(scenario)
    
    # Assertions
    assert result.scenario_id == "EXP-SMOKE"
    assert result.total_latency_ns > 0
    assert result.start_timestamp_ns > 0
    assert result.end_timestamp_ns > result.start_timestamp_ns
    assert len(result.errors) == 0
    
    # In a simulation mode orchestrator, benign actions should visit layers and pass
    assert result.layer_outcomes.L1.decision == "ALLOW"
    assert result.layer_outcomes.L2.decision == "ALLOW"
    # L3/L4/L5 are simulated as well
    assert result.layer_outcomes.L5.decision == "ALLOW"
    
    assert result.attack_blocked is False
    assert result.attack_success is False
    assert result.stopping_layer is None
    assert result.evidence_reference is not None
